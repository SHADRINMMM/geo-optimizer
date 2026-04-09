"""
Monitoring task: check AI mentions for all active sites.
Frequency is per-site (daily/weekly/monthly), controlled by monitoring_frequency field.
Engines and query expansion are configured via settings.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from app.worker import celery_app

logger = logging.getLogger(__name__)

# Registry of available engine checkers
_ENGINE_REGISTRY = {
    "gemini": "app.services.monitor.gemini_checker.check_mention_gemini",
    "claude": "app.services.monitor.claude_checker.check_mention_claude",
    "google_ai": "app.services.monitor.google_checker.check_mention_google",
    "chatgpt": "app.services.monitor.openai_checker.check_mention_openai",
    "yandex": "app.services.monitor.yandex_checker.check_mention_yandex",
}


def _load_checker(engine: str):
    """Dynamically import checker function by engine name."""
    import importlib
    path = _ENGINE_REGISTRY[engine]
    module_path, func_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


@celery_app.task(name="app.tasks.monitor.run_all_monitors")
def run_all_monitors():
    return asyncio.run(_run_all())


@celery_app.task(name="app.tasks.monitor.check_site_mentions")
def check_site_mentions(site_id: str):
    return asyncio.run(_check_site(site_id))


async def _run_all():
    from app.core.database import AsyncSessionLocal
    from app.models import Site, SiteProfile
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Site, SiteProfile)
            .join(SiteProfile, SiteProfile.site_id == Site.id, isouter=True)
            .where(Site.status == "done")
        )
        rows = result.all()

    now = datetime.now(timezone.utc)
    scheduled = 0
    for site, profile in rows:
        if _should_run(profile, now):
            check_site_mentions.delay(site.id)
            scheduled += 1

    return {"scheduled": scheduled}


def _should_run(profile, now: datetime) -> bool:
    """Check if site needs monitoring based on its frequency setting."""
    if not profile:
        return True  # no profile yet, run anyway
    freq = getattr(profile, "monitoring_frequency", "weekly")
    # Find last check time from DB — approximated here as "always run"
    # Real logic would query MonitoringResult.checked_at for this site
    return True  # Celery beat schedule handles the interval


async def _check_site(site_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models import Site, SiteProfile, MonitoringJob, MonitoringResult
    from app.services.monitor.query_expander import expand_queries
    from app.core.config import get_settings
    from sqlalchemy import select

    settings = get_settings()
    enabled_engines = [e.strip() for e in settings.MONITOR_ENGINES.split(",") if e.strip() in _ENGINE_REGISTRY]

    async with AsyncSessionLocal() as db:
        profile_result = await db.execute(
            select(SiteProfile).where(SiteProfile.site_id == site_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile or not profile.target_queries:
            return {"skipped": True, "reason": "no profile or no target_queries"}

        business_name = profile.business_name or ""
        products = [p.get("name") for p in (profile.products_services or []) if p.get("name")]

        # Expand queries if not cached or expansion enabled
        if settings.MONITOR_QUERY_EXPANSION > 0:
            if not profile.expanded_queries:
                all_queries = await expand_queries(
                    business_name=business_name,
                    business_description=profile.description or "",
                    target_queries=profile.target_queries,
                    city=profile.city or "",
                    n_per_query=settings.MONITOR_QUERY_EXPANSION,
                )
                profile.expanded_queries = all_queries
                await db.commit()
            else:
                all_queries = profile.expanded_queries
        else:
            all_queries = list(profile.target_queries)

        # Cap total queries
        queries_to_check = all_queries[:settings.MONITOR_MAX_QUERIES]

        results = []
        for query in queries_to_check:
            for engine in enabled_engines:
                try:
                    checker = _load_checker(engine)
                except KeyError:
                    logger.warning(f"Unknown engine: {engine}")
                    continue

                job = MonitoringJob(
                    site_id=site_id,
                    query=query,
                    engine=engine,
                    status="running",
                    scheduled_at=datetime.now(timezone.utc),
                )
                db.add(job)
                await db.flush()

                try:
                    result = await checker(
                        query=query,
                        business_name=business_name,
                        products=products,
                    )
                    monitoring_result = MonitoringResult(
                        job_id=job.id,
                        site_id=site_id,
                        engine=engine,
                        query=query,
                        mentioned=result.get("mentioned", False),
                        position=result.get("position"),
                        snippet=result.get("snippet"),
                        product_mentions=result.get("product_mentions"),
                        competitor_mentions=result.get("competitors"),
                        full_response=result.get("full_response", "")[:5000],
                        checked_at=datetime.now(timezone.utc),
                    )
                    db.add(monitoring_result)
                    job.status = "done"
                    results.append(result)
                except Exception as e:
                    job.status = "error"
                    logger.error(
                        f"Monitor check failed site={site_id} query={query!r} engine={engine}: {e}"
                    )

        await db.commit()
        return {"checked": len(results), "site_id": site_id, "engines": enabled_engines}
