"""
Claude mention checker — ask Claude a user query and analyze if business appears.
Uses AWS Bedrock Claude client.
"""
from app.services.ai.claude_client import check_mention_claude as _check


async def check_mention_claude(query: str, business_name: str, products: list) -> dict:
    """
    Ask Claude the query as a real user would, then check if business is mentioned.
    Returns structured result dict.
    """
    result = await _check(
        query=query,
        business_name=business_name,
        products=products,
    )
    result["engine"] = "claude"
    return result
