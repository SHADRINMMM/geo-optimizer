"""
Google AI Overview checker — use Playwright to check if business appears
in Google Search AI Overviews (SGE) for a query.
"""
import re
import logging
from app.services.ai.prompt_templates import MONITOR_ANALYSIS_PROMPT
from app.services.ai.gemini_client import _parse_json

logger = logging.getLogger(__name__)


async def check_mention_google(query: str, business_name: str, products: list) -> dict:
    """
    Search Google and extract AI Overview text, then analyze for business mentions.
    Falls back to standard snippet analysis if no AI Overview found.
    """
    try:
        ai_overview_text = await _fetch_google_ai_overview(query)
    except Exception as e:
        logger.warning(f"Google checker failed to fetch: {e}")
        ai_overview_text = ""

    if not ai_overview_text:
        return {
            "mentioned": False,
            "position": None,
            "snippet": None,
            "product_mentions": [],
            "competitors": [],
            "full_response": "",
            "engine": "google_ai",
        }

    # Analyze with Gemini (cheaper than Claude for this)
    result = await _analyze_with_gemini(query, business_name, products, ai_overview_text)
    result["engine"] = "google_ai"
    result["full_response"] = ai_overview_text[:2000]
    return result


async def _fetch_google_ai_overview(query: str) -> str:
    """Use Playwright to get Google AI Overview text for a query."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        page = await context.new_page()

        try:
            search_url = f"https://www.google.com/search?q={_url_encode(query)}&hl=ru"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            # Try to extract AI Overview / SGE block
            # Google uses various class names — try multiple selectors
            ai_text = await page.evaluate("""() => {
                // Try AI Overview container selectors
                const selectors = [
                    '[data-attrid="wa:/description"]',
                    '.kno-rdesc span',
                    '[jsname="yEVEwb"]',
                    '.ILfuVd',
                    '.wDYxhc',
                    'div[data-chunk-index]',
                    '.yDYNvb',
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText && el.innerText.length > 50) {
                        return el.innerText.trim();
                    }
                }
                // Fallback: first meaningful paragraph from search results
                const snippets = document.querySelectorAll('.VwiC3b, .yXK7lf');
                return Array.from(snippets).slice(0, 3).map(e => e.innerText).join('\\n');
            }""")

            return ai_text or ""
        finally:
            await browser.close()


async def _analyze_with_gemini(
    query: str,
    business_name: str,
    products: list,
    ai_response: str,
) -> dict:
    """Use Gemini to analyze Google results for business mentions."""
    from app.services.ai.gemini_client import _model as model

    prompt = MONITOR_ANALYSIS_PROMPT.format(
        query=query,
        business_name=business_name,
        products=", ".join(products[:10]) if products else "не указаны",
        ai_response=ai_response,
    )

    try:
        response = model.generate_content(prompt)
        result = _parse_json(response.text)
        return result
    except Exception as e:
        logger.warning(f"Gemini analysis failed: {e}")
        return {
            "mentioned": False,
            "position": None,
            "snippet": None,
            "product_mentions": [],
            "competitors": [],
        }


def _url_encode(text: str) -> str:
    from urllib.parse import quote_plus
    return quote_plus(text)
