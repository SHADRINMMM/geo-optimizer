"""
AWS Bedrock Claude client — used for AI mention monitoring.
"""
import json
import boto3
from app.core.config import get_settings
from app.services.ai.prompt_templates import MONITOR_ANALYSIS_PROMPT

settings = get_settings()


def _get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=settings.AWS_BEDROCK_REGION,
    )


async def ask_claude(prompt: str, max_tokens: int = 2000) -> str:
    """
    Send a prompt to Claude via Bedrock and return text response.
    Note: boto3 is synchronous — run in executor for async contexts.
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _ask_claude_sync, prompt, max_tokens)


def _ask_claude_sync(prompt: str, max_tokens: int = 2000) -> str:
    client = _get_bedrock_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = client.invoke_model(
        modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


async def check_mention_claude(query: str, business_name: str, products: list) -> dict:
    """
    Ask Claude the user's query and analyze if business is mentioned.
    Returns structured mention result.
    """
    # First: ask Claude as a user would
    user_response = await ask_claude(
        f"{query}",
        max_tokens=1000,
    )

    # Then: analyze the response
    analysis_prompt = MONITOR_ANALYSIS_PROMPT.format(
        query=query,
        business_name=business_name,
        products=", ".join(products[:10]) if products else "не указаны",
        ai_response=user_response,
    )
    analysis_raw = await ask_claude(analysis_prompt, max_tokens=800)

    try:
        import re
        analysis_raw = re.sub(r"```(?:json)?\s*", "", analysis_raw)
        analysis_raw = re.sub(r"```\s*$", "", analysis_raw)
        result = json.loads(analysis_raw.strip())
    except Exception:
        result = {"mentioned": False, "position": None, "snippet": None,
                  "product_mentions": [], "competitors": []}

    result["full_response"] = user_response
    result["engine"] = "claude"
    return result
