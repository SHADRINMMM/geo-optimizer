"""
GET/POST /api/v1/monitor — AI mention monitoring endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.auth import get_current_user, get_or_create_db_user
from app.models import Site, MonitoringJob, MonitoringResult

router = APIRouter()


@router.post("/monitor/{site_id}/run")
async def trigger_monitor(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger AI mention monitoring for a site."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    if site.status != "done":
        raise HTTPException(
            status_code=400,
            detail="Site must complete analysis before monitoring",
        )

    from app.tasks.monitor import check_site_mentions
    check_site_mentions.delay(site_id)

    return {"message": f"Monitoring started for {site.domain}", "site_id": site_id}


@router.get("/monitor/{site_id}/results")
async def get_monitor_results(
    site_id: str,
    limit: int = 20,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI mention monitoring results for a site."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Site not found")

    # Latest monitoring job
    job_result = await db.execute(
        select(MonitoringJob)
        .where(MonitoringJob.site_id == site_id)
        .order_by(desc(MonitoringJob.created_at))
    )
    latest_job = job_result.scalars().first()

    # Results
    results_query = await db.execute(
        select(MonitoringResult)
        .where(MonitoringResult.site_id == site_id)
        .order_by(desc(MonitoringResult.checked_at))
        .limit(limit)
    )
    results = results_query.scalars().all()

    return {
        "site_id": site_id,
        "latest_job": {
            "id": latest_job.id,
            "query": latest_job.query,
            "engine": latest_job.engine,
            "status": latest_job.status,
            "scheduled_at": latest_job.scheduled_at,
        } if latest_job else None,
        "results": [
            {
                "id": r.id,
                "query": r.query,
                "engine": r.engine,
                "mentioned": r.mentioned,
                "position": r.position,
                "snippet": r.snippet,
                "product_mentions": r.product_mentions,
                "competitor_mentions": r.competitor_mentions,
                "checked_at": r.checked_at,
            }
            for r in results
        ],
    }


@router.get("/monitor/{site_id}/score")
async def get_visibility_score(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI Visibility Score — composite metric for the site.
    Returns score, trend, and per-query breakdown.
    """
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Site not found")

    from app.services.monitor.metrics_builder import build_visibility_report
    report = await build_visibility_report(site_id, db)

    return report
