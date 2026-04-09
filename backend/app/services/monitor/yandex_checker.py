"""
YandexGPT checker — query YandexGPT API and analyze if business is mentioned.
Docs: https://yandex.cloud/ru/docs/foundation-models/text-generation/api-ref/
"""
import json
import logging
import urllib.request
from app.services.ai.prompt_templates import MONITOR_ANALYSIS_PROMPT
from app.services.ai.gemini_client import _model, _parse_json
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _ask_yandex_sync(query: str) -> str:
    """Call YandexGPT API synchronously."""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    body = json.dumps({
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 1500},
        "messages": [
            {"role": "system", "text": "Ты помощник, который отвечает на вопросы пользователей."},
            {"role": "user", "text": query},
        ],
    }).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["result"]["alternatives"][0]["message"]["text"]


async def check_mention_yandex(query: str, business_name: str, products: list) -> dict:
    """Ask YandexGPT the query, then analyze if business is mentioned."""
    import asyncio
    loop = asyncio.get_running_loop()

    if not settings.YANDEX_API_KEY or not settings.YANDEX_FOLDER_ID:
        logger.warning("Yandex checker skipped: YANDEX_API_KEY or YANDEX_FOLDER_ID not set")
        return _empty_result("yandex")

    try:
        ai_text = await loop.run_in_executor(None, _ask_yandex_sync, query)
    except Exception as e:
        logger.warning(f"YandexGPT request failed: {e}")
        return _empty_result("yandex")

    # Analyze with Gemini (cheaper than Yandex for analysis)
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
        logger.warning(f"Yandex analysis parse failed: {e}")
        result = {"mentioned": False, "position": None, "snippet": None,
                  "product_mentions": [], "competitors": []}

    result["full_response"] = ai_text
    result["engine"] = "yandex"
    return result


def _empty_result(engine: str) -> dict:
    return {
        "mentioned": False, "position": None, "snippet": None,
        "product_mentions": [], "competitors": [], "full_response": "", "engine": engine,
    }
