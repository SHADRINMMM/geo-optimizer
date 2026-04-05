"""
Fetch business reviews from Google Places, 2GIS.
"""
import httpx
from app.core.config import get_settings

settings = get_settings()


async def fetch_reviews(name: str, address: str = "", city: str = "") -> list[dict]:
    """
    Fetch reviews from available sources.
    Returns list of review dicts.
    """
    all_reviews = []

    if settings.GOOGLE_PLACES_API_KEY and name:
        google_reviews = await _fetch_google_places(name, address, city)
        all_reviews.extend(google_reviews)

    return all_reviews


async def _fetch_google_places(name: str, address: str, city: str) -> list[dict]:
    """Fetch from Google Places API."""
    query = f"{name} {city or address}".strip()

    async with httpx.AsyncClient(timeout=10) as client:
        # Find place
        search_resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,name,rating,user_ratings_total",
                "key": settings.GOOGLE_PLACES_API_KEY,
            },
        )
        search_data = search_resp.json()
        candidates = search_data.get("candidates", [])
        if not candidates:
            return []

        place_id = candidates[0].get("place_id")
        rating = candidates[0].get("rating")
        review_count = candidates[0].get("user_ratings_total", 0)

        # Get reviews
        details_resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "reviews,opening_hours,formatted_address",
                "language": "ru",
                "key": settings.GOOGLE_PLACES_API_KEY,
            },
        )
        details = details_resp.json().get("result", {})
        raw_reviews = details.get("reviews", [])

    reviews = []
    for r in raw_reviews[:10]:
        reviews.append({
            "source": "google",
            "rating": r.get("rating"),
            "text": r.get("text"),
            "author": r.get("author_name"),
            "date": r.get("relative_time_description"),
        })

    # Add summary entry
    if rating:
        reviews.insert(0, {
            "source": "google",
            "rating": rating,
            "text": f"Средний рейтинг на Google: {rating} ({review_count} отзывов)",
            "author": "Google Maps",
            "date": None,
            "_is_summary": True,
        })

    return reviews
