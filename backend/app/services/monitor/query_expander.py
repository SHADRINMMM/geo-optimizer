"""
Query expander — given a business profile and target keywords,
generate semantically related queries that users might ask AI search engines.
"""
import json
import logging
from app.services.ai.gemini_client import _model, _parse_json

logger = logging.getLogger(__name__)


async def expand_queries(
    business_name: str,
    business_description: str,
    target_queries: list[str],
    city: str = "",
    n_per_query: int = 3,
) -> list[str]:
    """
    For each target query generate n_per_query semantically similar variants.
    Returns deduplicated list of all queries (original + expanded).
    """
    import asyncio

    if not target_queries:
        return []

    prompt = _build_expansion_prompt(
        business_name=business_name,
        description=business_description,
        queries=target_queries,
        city=city,
        n_per_query=n_per_query,
    )

    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(None, _model.generate_content, prompt)
        expanded = _parse_json(response.text)
        if not isinstance(expanded, list):
            raise ValueError("Expected list")
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}")
        return target_queries  # fallback to originals

    # Merge originals + expanded, deduplicate preserving order
    all_queries = list(target_queries)
    seen = set(q.lower() for q in target_queries)
    for q in expanded:
        if isinstance(q, str) and q.lower() not in seen:
            all_queries.append(q)
            seen.add(q.lower())

    return all_queries


def _build_expansion_prompt(
    business_name: str,
    description: str,
    queries: list[str],
    city: str,
    n_per_query: int,
) -> str:
    city_hint = f" в городе {city}" if city else ""
    return f"""Ты помогаешь оптимизировать видимость бизнеса в AI-поисковиках (ChatGPT, Gemini, Яндекс).

Бизнес: "{business_name}"
Описание: {description}
Город{city_hint}

Для каждого из следующих целевых запросов придумай {n_per_query} семантически близких варианта — так, как реальные пользователи могут спросить у ИИ-ассистента то же самое другими словами. Используй разные формулировки: вопросы, фразы с "где", "как", "что лучше", разговорный стиль.

Целевые запросы:
{json.dumps(queries, ensure_ascii=False, indent=2)}

Верни JSON-массив строк — только новые варианты (без исходных):
["запрос1", "запрос2", ...]

Только JSON, без markdown."""
