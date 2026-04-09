"""
Google Gemini 3.0 Flash client — primary AI for content generation.
"""
import json
import re
import google.generativeai as genai
from app.core.config import get_settings
from app.services.ai.prompt_templates import BUILD_PROFILE_PROMPT, FAQ_GENERATION_PROMPT

settings = get_settings()
genai.configure(api_key=settings.GOOGLE_API_KEY)

_model = genai.GenerativeModel(settings.LLM_MODEL)


def _parse_json(text: str) -> dict | list:
    """Extract JSON from model response (handles markdown code blocks)."""
    text = text.strip()
    # Remove markdown code blocks if present
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return json.loads(text.strip())


async def build_business_profile(url: str, crawl_data: dict, reviews: list) -> dict:
    """
    Main function: build complete business profile from crawl data.
    Uses Gemini multimodal for any images/PDFs found.
    """
    # Process images if any (take first 3)
    image_descriptions = []
    for image_url in crawl_data.get("images", [])[:3]:
        try:
            from app.services.ingestion.gemini_vision import process_image_url
            desc = await process_image_url(image_url)
            image_descriptions.append(desc)
        except Exception:
            pass

    # Process PDFs (take first 2)
    pdf_content = []
    for pdf_url in crawl_data.get("pdfs", [])[:2]:
        try:
            from app.services.ingestion.gemini_vision import process_pdf_url
            content = await process_pdf_url(pdf_url)
            pdf_content.append(content)
        except Exception:
            pass

    # Build context for the prompt
    pages_text = ""
    for page in crawl_data.get("pages", [])[:5]:
        pages_text += f"\n--- {page.get('url', '')} ---\n"
        pages_text += f"Заголовок: {page.get('h1', '') or page.get('title', '')}\n"
        pages_text += f"Описание: {page.get('description', '')}\n"
        pages_text += (page.get("body_text", "") or "")[:800]
        pages_text += "\n"

    if image_descriptions:
        pages_text += "\n\nОПИСАНИЯ ИЗОБРАЖЕНИЙ:\n" + "\n".join(image_descriptions)

    if pdf_content:
        pages_text += "\n\nСОДЕРЖИМОЕ PDF ФАЙЛОВ:\n" + "\n".join(pdf_content)

    reviews_text = "\n".join([
        f"- {r.get('source', '')}: {r.get('rating', '')}★ — {r.get('text', '')[:200]}"
        for r in reviews[:10] if r.get("text")
    ]) or "Отзывы не найдены"

    prompt = BUILD_PROFILE_PROMPT.format(
        crawl_data=pages_text[:6000],
        reviews=reviews_text[:2000],
    )

    import asyncio
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, _model.generate_content, prompt)
    profile = _parse_json(response.text)

    # Enrich with crawl data that wasn't parsed
    if not profile.get("phone") and crawl_data.get("phone"):
        profile["phone"] = crawl_data["phone"]
    if not profile.get("email") and crawl_data.get("email"):
        profile["email"] = crawl_data["email"]

    # Add raw crawl data for re-processing
    profile["raw_crawl_data"] = {
        "url": crawl_data.get("url"),
        "existing_schema": crawl_data.get("existing_schema", []),
        "social": crawl_data.get("social", {}),
    }

    return profile


async def generate_faq(business_name: str, business_type: str, description: str, language: str = "ru") -> list:
    """Generate FAQ list for a business."""
    prompt = FAQ_GENERATION_PROMPT.format(
        business_type=business_type,
        business_name=business_name,
        description=description,
        language=language,
    )
    import asyncio
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, _model.generate_content, prompt)
    return _parse_json(response.text)
