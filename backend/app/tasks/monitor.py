"""
Weekly monitoring task: check AI mentions for all active sites.
"""
import asyncio
import logging
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.monitor.run_all_monitors")
def run_all_monitors():
    return asyncio.run(_run_all())


@celery_app.task(name="app.tasks.monitor.check_site_mentions")
def check_site_mentions(site_id: str):
    return asyncio.run(_check_site(site_id))


async def _run_all():
    from app.core.database import AsyncSessionLocal
    from app.models import Site
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Site).where(Site.status == "done"))
        sites = result.scalars().all()

    for site in sites:
        check_site_mentions.delay(site.id)

    return {"scheduled": len(sites)}


async def _check_site(site_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models import Site, SiteProfile, MonitoringJob, MonitoringResult
    from app.services.monitor.claude_checker import check_mention_claude
    from app.services.monitor.google_checker import check_mention_google
    from sqlalchemy import select
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        profile_result = await db.execute(
            select(SiteProfile).where(SiteProfile.site_id == site_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile or not profile.target_queries:
            return {"skipped": True}

        results = []
        for query in profile.target_queries[:5]:  # Max 5 queries per site
            for engine, checker in [
                ("claude", check_mention_claude),
                ("google_ai", check_mention_google),
            ]:
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
                        business_name=profile.business_name or "",
                        products=[p.get("name") for p in (profile.products_services or [])],
                    )
                    monitoring_result = MonitoringResult(
                        job_id=job.id,
                        site_id=site_id,
                        engine=engine,
                        query=query,
                        mentioned=result["mentioned"],
                        position=result.get("position"),
                        snippet=result.get("snippet"),
                        product_mentions=result.get("product_mentions"),
                        competitor_mentions=result.get("competitors"),
                        full_response=result.get("full_response", "")[:2000],
                        checked_at=datetime.now(timezone.utc),
                    )
                    db.add(monitoring_result)
                    job.status = "done"
                    results.append(result)
                except Exception as e:
                    job.status = "error"
                    logger.error(f"Monitor check failed site={site_id} query={query!r} engine={engine}: {e}")

        await db.commit()
        return {"checked": len(results), "site_id": site_id}
