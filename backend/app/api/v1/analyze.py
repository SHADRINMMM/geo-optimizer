"""
POST /api/v1/analyze — submit a URL for GEO optimization pipeline.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, get_or_create_db_user
from app.models import Site, GenerationJob

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: str  # plain str so we can normalize it ourselves


class AnalyzeResponse(BaseModel):
    site_id: str
    job_id: str
    status: str
    message: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_site(
    body: AnalyzeRequest,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a website URL for full GEO optimization.
    Creates a Site record, queues the Celery pipeline task.
    """
    db_user = await get_or_create_db_user(propelauth_user, db)

    # Normalize URL
    url = body.url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Derive domain and slug
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    base_slug = domain.replace(".", "-")

    # Check if this user already has this site
    existing = await db.execute(
        select(Site).where(Site.user_id == db_user.id, Site.domain == domain)
    )
    site = existing.scalar_one_or_none()

    if site:
        # Re-run pipeline for existing site
        if site.status in ("processing", "crawling", "generating", "saving"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Site is already being processed",
            )
        site.status = "queued"
        site.error_message = None
    else:
        # Make slug unique
        slug = await _unique_slug(base_slug, db)
        site = Site(
            id=str(uuid.uuid4()),
            user_id=db_user.id,
            url=url,
            domain=domain,
            slug=slug,
            status="queued",
        )
        db.add(site)

    await db.flush()

    # Create generation job
    job = GenerationJob(
        id=str(uuid.uuid4()),
        site_id=site.id,
        status="queued",
        progress_pct=0,
        progress_step="queued",
    )
    db.add(job)
    await db.commit()

    # Queue Celery task
    from app.tasks.crawl import run_full_pipeline
    run_full_pipeline.delay(site.id, url)

    return AnalyzeResponse(
        site_id=site.id,
        job_id=job.id,
        status="queued",
        message=f"Analysis started for {domain}",
    )


@router.get("/analyze/{site_id}/status")
async def get_analysis_status(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll job progress for a site analysis."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    job_result = await db.execute(
        select(GenerationJob).where(GenerationJob.site_id == site_id)
    )
    job = job_result.scalar_one_or_none()

    return {
        "site_id": site_id,
        "site_status": site.status,
        "job": {
            "status": job.status if job else None,
            "progress_pct": job.progress_pct if job else 0,
            "progress_step": job.progress_step if job else None,
            "error": job.error if job else None,
            "started_at": job.started_at if job else None,
            "finished_at": job.finished_at if job else None,
        } if job else None,
    }


async def _unique_slug(base: str, db: AsyncSession) -> str:
    """Append numeric suffix if slug is taken."""
    slug = base
    counter = 1
    while True:
        result = await db.execute(select(Site).where(Site.slug == slug))
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base}-{counter}"
        counter += 1
