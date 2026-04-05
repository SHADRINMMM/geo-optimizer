"""
Main pipeline task: crawl → ingest → AI process → generate → save → notify
"""
import asyncio
from datetime import datetime, timezone
from app.worker import celery_app


@celery_app.task(bind=True, name="app.tasks.crawl.run_full_pipeline")
def run_full_pipeline(self, site_id: str, url: str):
    """
    Full GEO optimization pipeline for a site.
    Runs asynchronously via asyncio.run() since Celery workers are sync.
    """
    return asyncio.run(_async_pipeline(self, site_id, url))


async def _async_pipeline(task, site_id: str, url: str):
    from app.core.database import AsyncSessionLocal
    from app.models import Site, SiteProfile, GenerationJob
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Update job status
        result = await db.execute(
            select(GenerationJob).where(GenerationJob.site_id == site_id)
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = "started"
            job.started_at = datetime.now(timezone.utc)
            job.celery_task_id = task.request.id
            job.progress_pct = 5
            job.progress_step = "crawling"
            await db.commit()

    try:
        # Step 1: Crawl
        await _update_progress(site_id, "crawling", 10)
        from app.services.crawler.playwright_crawler import crawl_site
        crawl_result = await crawl_site(url)

        # Step 2: Fetch reviews
        await _update_progress(site_id, "fetching_reviews", 25)
        from app.services.ingestion.reviews_fetcher import fetch_reviews
        reviews = await fetch_reviews(
            name=crawl_result.get("business_name", ""),
            address=crawl_result.get("address", ""),
            city=crawl_result.get("city", ""),
        )

        # Step 3: Process with Gemini (multimodal)
        await _update_progress(site_id, "ai_processing", 40)
        from app.services.ai.gemini_client import build_business_profile
        profile_data = await build_business_profile(url, crawl_result, reviews)

        # Step 4: Get site slug for hosted profile URL
        slug = await _get_site_slug(site_id)

        # Step 5: Generate all files
        await _update_progress(site_id, "generating", 60)
        from app.services.generator.llms_txt import build_llms_txt
        from app.services.generator.schema_builder import build_json_ld
        from app.services.generator.faq_builder import build_faq_html
        from app.services.generator.robots_patcher import build_patched_robots
        from app.services.generator.zip_builder import build_export_zip

        llms_txt = build_llms_txt(profile_data, reviews)
        schema_json = build_json_ld(profile_data, reviews)
        faq_html = build_faq_html(
            profile_data.get("faq", []),
            business_name=profile_data.get("business_name", ""),
        )
        robots_txt = await build_patched_robots(url)
        zip_bytes = build_export_zip(
            llms_txt=llms_txt,
            schema_json=schema_json,
            robots_txt=robots_txt,
            faq_html=faq_html,
            business_name=profile_data.get("business_name", ""),
            slug=slug,
        )

        # Step 6: Save to DB and R2
        await _update_progress(site_id, "saving", 80)
        await _save_results(site_id, profile_data, reviews, {
            "llms_txt": llms_txt,
            "schema_json": schema_json,
            "faq_html": faq_html,
            "robots_txt": robots_txt,
        }, zip_bytes=zip_bytes)

        # Step 7: Ping IndexNow
        await _update_progress(site_id, "indexing", 90)
        from app.services.generator.indexnow import ping_indexnow
        await ping_indexnow(url, slug)

        # Step 7: Done
        await _finish_job(site_id, success=True)

        return {"status": "done", "site_id": site_id}

    except Exception as e:
        await _finish_job(site_id, success=False, error=str(e))
        raise


async def _update_progress(site_id: str, step: str, pct: int):
    from app.core.database import AsyncSessionLocal
    from app.models import GenerationJob, Site
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GenerationJob).where(GenerationJob.site_id == site_id)
        )
        job = result.scalar_one_or_none()
        if job:
            job.progress_step = step
            job.progress_pct = pct
            await db.commit()

        # Update site status too
        site_result = await db.execute(select(Site).where(Site.id == site_id))
        site = site_result.scalar_one_or_none()
        if site:
            site.status = step
            await db.commit()


async def _get_site_slug(site_id: str) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models import Site
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        return site.slug if site else site_id


async def _save_results(site_id: str, profile_data: dict, reviews: list, files: dict, zip_bytes: bytes = None):
    from app.core.database import AsyncSessionLocal
    from app.core.storage import upload_file
    from app.models import SiteProfile, SiteFile, SiteReview
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Upsert SiteProfile
        result = await db.execute(select(SiteProfile).where(SiteProfile.site_id == site_id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = SiteProfile(site_id=site_id)
            db.add(profile)

        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        # Save ZIP to R2
        if zip_bytes:
            zip_key = f"sites/{site_id}/export.zip"
            upload_file(zip_key, zip_bytes, "application/zip")

        # Save files to R2 + DB
        for file_type, content in files.items():
            r2_key = f"sites/{site_id}/{file_type}"
            content_type = "text/plain" if file_type in ["llms_txt", "robots_txt"] else "application/json"
            public_url = upload_file(r2_key, content, content_type)

            file_result = await db.execute(
                select(SiteFile).where(SiteFile.site_id == site_id, SiteFile.file_type == file_type)
            )
            site_file = file_result.scalar_one_or_none()
            if not site_file:
                site_file = SiteFile(site_id=site_id, file_type=file_type)
                db.add(site_file)

            site_file.content = content if len(content) < 65000 else None
            site_file.r2_key = r2_key
            site_file.public_url = public_url

        # Save reviews
        for review in reviews:
            site_review = SiteReview(
                site_id=site_id,
                source=review.get("source", "unknown"),
                rating=review.get("rating"),
                text=review.get("text"),
                author=review.get("author"),
                review_date=review.get("date"),
            )
            db.add(site_review)

        await db.commit()


async def _finish_job(site_id: str, success: bool, error: str = None):
    from app.core.database import AsyncSessionLocal
    from app.models import GenerationJob, Site
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        job_result = await db.execute(
            select(GenerationJob).where(GenerationJob.site_id == site_id)
        )
        job = job_result.scalar_one_or_none()
        if job:
            job.status = "done" if success else "error"
            job.finished_at = datetime.now(timezone.utc)
            job.progress_pct = 100 if success else job.progress_pct
            if error:
                job.error = error

        site_result = await db.execute(select(Site).where(Site.id == site_id))
        site = site_result.scalar_one_or_none()
        if site:
            site.status = "done" if success else "error"
            if error:
                site.error_message = error

        await db.commit()
