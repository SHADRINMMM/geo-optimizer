"""
Gemini checker — query Gemini 2.5 Flash as a user would, analyze if business is mentioned.
"""
import logging
from app.services.ai.prompt_templates import MONITOR_ANALYSIS_PROMPT
from app.services.ai.gemini_client import _model, _parse_json

logger = logging.getLogger(__name__)


async def check_mention_gemini(query: str, business_name: str, products: list) -> dict:
    """Ask Gemini the query as a real user, then analyze if business is mentioned."""
    import asyncio
    loop = asyncio.get_running_loop()

    # Step 1: ask Gemini as user
    user_response = await loop.run_in_executor(None, _model.generate_content, query)
    ai_text = user_response.text

    # Step 2: analyze with Gemini
    analysis_prompt = MONITOR_ANALYSIS_PROMPT.format(
        query=query,
        business_name=business_name,
        products=", ".join(products[:10]) if products else "не указаны",
        ai_response=ai_text,
    )
    analysis_resp = await loop.run_in_executor(None, _model.generate_content, analysis_prompt)

    try:
        result = _parse_json(analysis_resp.text)
    except Exception as e:
        logger.warning(f"Gemini analysis parse failed: {e}")
        result = {"mentioned": False, "position": None, "snippet": None,
                  "product_mentions": [], "competitors": []}

    result["full_response"] = ai_text
    result["engine"] = "gemini"
    return result
