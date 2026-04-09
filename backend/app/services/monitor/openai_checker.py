"""
ChatGPT checker — query GPT-4o-mini via OpenAI API and analyze if business is mentioned.
"""
import json
import logging
import urllib.request
from app.services.ai.prompt_templates import MONITOR_ANALYSIS_PROMPT
from app.services.ai.gemini_client import _model, _parse_json
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _ask_openai_sync(query: str) -> str:
    """Call OpenAI Chat Completions API synchronously."""
    url = "https://api.openai.com/v1/chat/completions"
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 1500,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


async def check_mention_openai(query: str, business_name: str, products: list) -> dict:
    """Ask ChatGPT the query, then analyze if business is mentioned."""
    import asyncio
    loop = asyncio.get_running_loop()

    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI checker skipped: OPENAI_API_KEY not set")
        return _empty_result("chatgpt")

    try:
        ai_text = await loop.run_in_executor(None, _ask_openai_sync, query)
    except Exception as e:
        logger.warning(f"OpenAI request failed: {e}")
        return _empty_result("chatgpt")

    analysis_prompt = MONITOR_ANALYSIS_PROMPT.format(
        query=query,
        business_name=business_name,
        products=", ".join(products[:10]) if products else "не указаны",
        ai_response=ai_text,
    )
    try:
        analysis_resp = await loop.run_in_executor(None, _model.generate_content, analysis_prompt)
        result = _parse_json(analysis_resp.text)
    except Exception as e:
        logger.warning(f"OpenAI analysis parse failed: {e}")
        result = {"mentioned": False, "position": None, "snippet": None,
                  "product_mentions": [], "competitors": []}

    result["full_response"] = ai_text
    result["engine"] = "chatgpt"
    return result


def _empty_result(engine: str) -> dict:
    return {
        "mentioned": False, "position": None, "snippet": None,
        "product_mentions": [], "competitors": [], "full_response": "", "engine": engine,
    }
