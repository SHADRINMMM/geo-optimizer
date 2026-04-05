"""
Async Playwright crawler — extracts all available data from a website.
"""
import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import Any

from playwright.async_api import async_playwright, Page


PRIORITY_PATHS = ["/", "/about", "/o-nas", "/services", "/uslugi", "/products",
                  "/menu", "/contacts", "/kontakty", "/price", "/prices"]

MAX_PAGES = 8
TIMEOUT = 15000


async def crawl_site(url: str) -> dict[str, Any]:
    """
    Full crawl of a website. Returns structured data dict.
    """
    if not url.startswith("http"):
        url = "https://" + url

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; GEOBot/1.0; +https://ai.causabi.com/bot)",
            viewport={"width": 1280, "height": 800},
        )
        try:
            result = await _crawl(context, url)
        finally:
            await browser.close()

    return result


async def _crawl(context, base_url: str) -> dict[str, Any]:
    domain = urlparse(base_url).netloc
    visited = set()
    all_data = {
        "url": base_url,
        "domain": domain,
        "pages": [],
        "images": [],
        "pdfs": [],
        "business_name": None,
        "description": None,
        "address": None,
        "city": None,
        "phone": None,
        "email": None,
        "hours": None,
        "social": {},
        "existing_schema": [],
        "meta": {},
    }

    # Build URL list to visit
    urls_to_visit = [base_url]
    for path in PRIORITY_PATHS[1:]:
        urls_to_visit.append(urljoin(base_url, path))

    # Visit each URL
    for url in urls_to_visit[:MAX_PAGES]:
        if url in visited:
            continue
        visited.add(url)
        try:
            page_data = await _crawl_page(context, url)
            if page_data:
                all_data["pages"].append(page_data)
                _merge_data(all_data, page_data)
        except Exception:
            pass

    # Collect all images and PDFs
    for page in all_data["pages"]:
        all_data["images"].extend(page.get("images", []))
        all_data["pdfs"].extend(page.get("pdfs", []))

    # Deduplicate
    all_data["images"] = list(set(all_data["images"]))[:10]
    all_data["pdfs"] = list(set(all_data["pdfs"]))[:5]

    return all_data


async def _crawl_page(context, url: str) -> dict | None:
    page = await context.new_page()
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT)
        if not response or response.status >= 400:
            return None

        await page.wait_for_timeout(1500)  # Let JS render

        data = await page.evaluate("""() => {
            const getText = (sel) => {
                const el = document.querySelector(sel);
                return el ? el.innerText.trim() : null;
            };
            const getMeta = (name) => {
                const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                return el ? el.getAttribute('content') : null;
            };

            // Schema.org JSON-LD
            const schemas = [];
            document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
                try { schemas.push(JSON.parse(s.textContent)); } catch(e) {}
            });

            // Images
            const images = [];
            document.querySelectorAll('img[src]').forEach(img => {
                const src = img.src;
                if (src && !src.includes('data:') && (src.includes('.jpg') || src.includes('.jpeg') || src.includes('.png') || src.includes('.webp'))) {
                    images.push(src);
                }
            });

            // PDFs
            const pdfs = [];
            document.querySelectorAll('a[href*=".pdf"]').forEach(a => {
                if (a.href) pdfs.push(a.href);
            });

            // Social links
            const social = {};
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href;
                if (href.includes('instagram.com')) social.instagram = href;
                if (href.includes('vk.com')) social.vk = href;
                if (href.includes('t.me') || href.includes('telegram')) social.telegram = href;
                if (href.includes('youtube.com')) social.youtube = href;
            });

            // Phone numbers
            const bodyText = document.body.innerText;
            const phoneMatch = bodyText.match(/[\+7|8][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}/);
            const emailMatch = bodyText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);

            return {
                title: document.title,
                h1: getText('h1'),
                description: getMeta('description') || getMeta('og:description'),
                og_title: getMeta('og:title'),
                og_image: getMeta('og:image'),
                schemas,
                images: images.slice(0, 5),
                pdfs: pdfs.slice(0, 3),
                social,
                phone: phoneMatch ? phoneMatch[0] : null,
                email: emailMatch ? emailMatch[0] : null,
                body_text: document.body.innerText.substring(0, 3000),
            };
        }""")

        data["url"] = url
        return data

    except Exception as e:
        return None
    finally:
        await page.close()


def _merge_data(all_data: dict, page_data: dict):
    """Merge page-level data into aggregate."""
    if not all_data["business_name"] and page_data.get("og_title"):
        all_data["business_name"] = page_data["og_title"]
    if not all_data["business_name"] and page_data.get("h1"):
        all_data["business_name"] = page_data["h1"]

    if not all_data["description"] and page_data.get("description"):
        all_data["description"] = page_data["description"]

    if not all_data["phone"] and page_data.get("phone"):
        all_data["phone"] = page_data["phone"]

    if not all_data["email"] and page_data.get("email"):
        all_data["email"] = page_data["email"]

    # Merge social
    all_data["social"].update(page_data.get("social", {}))

    # Merge existing schema
    for schema in page_data.get("schemas", []):
        if schema not in all_data["existing_schema"]:
            all_data["existing_schema"].append(schema)
