"""
Public profile endpoints — hosted business pages for AI indexing.
GET /b/<slug> — human-readable page
GET /b/<slug>/llms.txt — AI-readable file
GET /b/<slug>/schema.json — JSON-LD schema
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import Site, SiteProfile, SiteFile, SiteReview

router = APIRouter()


@router.get("/b/{slug}/llms.txt", response_class=PlainTextResponse)
async def get_llms_txt(slug: str, db: AsyncSession = Depends(get_db)):
    """Serve llms.txt for AI crawlers — indexed by ChatGPT, Perplexity, etc."""
    site_file = await _get_file(slug, "llms_txt", db)
    if not site_file or not site_file.content:
        raise HTTPException(status_code=404, detail="llms.txt not found")

    return PlainTextResponse(
        content=site_file.content,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "public, max-age=3600",
            "X-Robots-Tag": "index, follow",
        },
    )


@router.get("/b/{slug}/schema.json")
async def get_schema_json(slug: str, db: AsyncSession = Depends(get_db)):
    """Serve JSON-LD schema for SEO/AI tools."""
    site_file = await _get_file(slug, "schema_json", db)
    if not site_file or not site_file.content:
        raise HTTPException(status_code=404, detail="Schema not found")

    import json
    return Response(
        content=site_file.content,
        media_type="application/ld+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/b/{slug}/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt(slug: str, db: AsyncSession = Depends(get_db)):
    """Serve robots.txt with AI bot rules."""
    site_file = await _get_file(slug, "robots_txt", db)
    if not site_file or not site_file.content:
        # Return a sensible default
        return PlainTextResponse("User-agent: *\nAllow: /\n")

    return PlainTextResponse(content=site_file.content)


@router.get("/b/{slug}")
async def get_public_profile(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Public business profile page data.
    Used by frontend to render the hosted profile (causabi.com/b/<slug>).
    Also returned as JSON for API consumers.
    """
    site_result = await db.execute(
        select(Site).where(Site.slug == slug)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_result = await db.execute(
        select(SiteProfile).where(SiteProfile.site_id == site.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not ready yet")

    # Top reviews for display
    reviews_result = await db.execute(
        select(SiteReview)
        .where(SiteReview.site_id == site.id, SiteReview.text.isnot(None))
        .order_by(SiteReview.rating.desc())
        .limit(5)
    )
    reviews = reviews_result.scalars().all()

    return {
        "slug": slug,
        "url": site.url,
        "business_name": profile.business_name,
        "description": profile.description,
        "short_description": profile.short_description,
        "business_category": profile.business_category,
        "address": profile.address,
        "city": profile.city,
        "phone": profile.phone,
        "email": profile.email,
        "website": profile.website,
        "hours": profile.hours,
        "google_rating": profile.google_rating,
        "google_review_count": profile.google_review_count,
        "unique_features": profile.unique_features or [],
        "products_services": profile.products_services or [],
        "faq": profile.faq or [],
        "reviews": [
            {
                "author": r.author,
                "rating": r.rating,
                "text": r.text,
                "source": r.source,
            }
            for r in reviews
        ],
        "llms_txt_url": f"https://causabi.com/b/{slug}/llms.txt",
        "schema_url": f"https://causabi.com/b/{slug}/schema.json",
    }


async def _get_file(slug: str, file_type: str, db: AsyncSession):
    """Helper: get a SiteFile by slug + file_type."""
    site_result = await db.execute(
        select(Site).where(Site.slug == slug)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        return None

    file_result = await db.execute(
        select(SiteFile).where(
            SiteFile.site_id == site.id,
            SiteFile.file_type == file_type,
        )
    )
    return file_result.scalar_one_or_none()
