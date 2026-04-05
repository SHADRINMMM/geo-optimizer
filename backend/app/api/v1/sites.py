"""
GET /api/v1/sites — list user's sites and their generated files.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import get_current_user, get_or_create_db_user
from app.models import Site, SiteProfile, SiteFile, GenerationJob

router = APIRouter()


@router.get("/sites")
async def list_sites(
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all sites for the current user."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    result = await db.execute(
        select(Site).where(Site.user_id == db_user.id).order_by(Site.created_at.desc())
    )
    sites = result.scalars().all()

    return {"sites": [_site_summary(s) for s in sites]}


@router.get("/sites/{site_id}")
async def get_site(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full site details with profile and files."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Load profile
    profile_result = await db.execute(
        select(SiteProfile).where(SiteProfile.site_id == site_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Load files
    files_result = await db.execute(
        select(SiteFile).where(SiteFile.site_id == site_id)
    )
    files = files_result.scalars().all()

    # Load latest job
    job_result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.site_id == site_id)
        .order_by(GenerationJob.created_at.desc())
    )
    job = job_result.scalars().first()

    return {
        "site": _site_summary(site),
        "profile": _profile_data(profile) if profile else None,
        "files": [_file_summary(f) for f in files],
        "job": _job_data(job) if job else None,
        "hosted_url": f"https://causabi.com/b/{site.slug}",
    }


@router.get("/sites/{site_id}/files/{file_type}")
async def get_file_content(
    site_id: str,
    file_type: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get raw content of a specific generated file."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    # Verify ownership
    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Site not found")

    file_result = await db.execute(
        select(SiteFile).where(
            SiteFile.site_id == site_id,
            SiteFile.file_type == file_type,
        )
    )
    site_file = file_result.scalar_one_or_none()
    if not site_file:
        raise HTTPException(status_code=404, detail=f"File '{file_type}' not found")

    return {
        "file_type": file_type,
        "content": site_file.content,
        "public_url": site_file.public_url,
        "r2_key": site_file.r2_key,
        "version": site_file.version,
    }


@router.get("/sites/{site_id}/download")
async def get_download_url(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pre-signed download URL for the ZIP export."""
    from app.core.storage import get_public_url

    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    zip_url = get_public_url(f"sites/{site_id}/export.zip")
    return {"download_url": zip_url}


@router.delete("/sites/{site_id}")
async def delete_site(
    site_id: str,
    propelauth_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a site and all its data."""
    db_user = await get_or_create_db_user(propelauth_user, db)

    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.user_id == db_user.id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    await db.delete(site)
    await db.commit()

    return {"deleted": True, "site_id": site_id}


def _site_summary(site: Site) -> dict:
    return {
        "id": site.id,
        "url": site.url,
        "domain": site.domain,
        "slug": site.slug,
        "status": site.status,
        "error_message": site.error_message,
        "created_at": site.created_at,
        "updated_at": site.updated_at,
    }


def _profile_data(profile: SiteProfile) -> dict:
    return {
        "business_name": profile.business_name,
        "description": profile.description,
        "short_description": profile.short_description,
        "business_type": profile.business_type,
        "business_category": profile.business_category,
        "address": profile.address,
        "city": profile.city,
        "phone": profile.phone,
        "email": profile.email,
        "hours": profile.hours,
        "website": profile.website,
        "google_rating": profile.google_rating,
        "google_review_count": profile.google_review_count,
        "products_services": profile.products_services,
        "faq": profile.faq,
        "target_queries": profile.target_queries,
        "unique_features": profile.unique_features,
    }


def _file_summary(f: SiteFile) -> dict:
    return {
        "file_type": f.file_type,
        "public_url": f.public_url,
        "version": f.version,
        "created_at": f.created_at,
    }


def _job_data(job: GenerationJob) -> dict:
    return {
        "id": job.id,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "progress_step": job.progress_step,
        "error": job.error,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }
