"""
IndexNow API — notify search engines instantly after content generation.
Free API: submit URL once, Bing/Yandex/other engines pick it up.
"""
import httpx
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# IndexNow endpoint (Bing routes to all participating engines)
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

# Participating search engines (all accept IndexNow)
INDEXNOW_HOSTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]


async def ping_indexnow(site_url: str, slug: str) -> dict:
    """
    Submit hosted profile URL to IndexNow for immediate indexing.
    Returns dict with success/failure per engine.
    """
    # The URL of our hosted profile page for this business
    hosted_url = f"https://causabi.com/b/{slug}"

    # Also submit the business's own site if we know it
    urls_to_submit = [hosted_url]
    if site_url and site_url != hosted_url:
        # Submit key file URL on their domain if we have hosting access
        # For now, just submit our hosted page
        pass

    key = settings.INDEXNOW_KEY
    if not key:
        logger.warning("INDEXNOW_KEY not configured — skipping IndexNow ping")
        return {"skipped": True, "reason": "no_key"}

    results = {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        for engine_url in INDEXNOW_HOSTS:
            try:
                resp = await client.post(
                    engine_url,
                    json={
                        "host": "causabi.com",
                        "key": key,
                        "urlList": urls_to_submit,
                    },
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
                engine_name = engine_url.split("//")[1].split("/")[0]
                results[engine_name] = {
                    "status": resp.status_code,
                    "ok": resp.status_code in (200, 202),
                }
                logger.info(f"IndexNow {engine_name}: {resp.status_code} for {hosted_url}")
            except Exception as e:
                engine_name = engine_url.split("//")[1].split("/")[0]
                results[engine_name] = {"status": None, "ok": False, "error": str(e)}
                logger.warning(f"IndexNow {engine_name} failed: {e}")

    return results


async def submit_url_list(urls: list[str]) -> bool:
    """Submit a list of URLs to IndexNow (batch submission)."""
    key = settings.INDEXNOW_KEY
    if not key or not urls:
        return False

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                INDEXNOW_ENDPOINT,
                json={
                    "host": "causabi.com",
                    "key": key,
                    "urlList": urls[:10000],  # IndexNow max per request
                },
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            return resp.status_code in (200, 202)
    except Exception as e:
        logger.error(f"IndexNow batch submit failed: {e}")
        return False
