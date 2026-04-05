"""
Patch robots.txt to allow AI bots and add llms.txt reference.
Fetches existing robots.txt and merges in our additions.
"""
import httpx


# AI bots that should be allowed to crawl for GEO visibility
AI_BOTS = [
    "GPTBot",           # ChatGPT
    "Claude-Web",       # Anthropic Claude
    "ClaudeBot",        # Anthropic Claude (alt)
    "PerplexityBot",    # Perplexity AI
    "YouBot",           # You.com
    "cohere-ai",        # Cohere
    "Omgilibot",        # Social listening / AI
    "anthropic-ai",     # Anthropic crawler
    "Google-Extended",  # Google AI training
    "CCBot",            # Common Crawl (used by many LLMs)
    "Bytespider",       # ByteDance / TikTok AI
    "ia_archiver",      # Internet Archive (training data)
]


async def build_patched_robots(base_url: str) -> str:
    """
    Fetch existing robots.txt and patch it with AI bot permissions + llms.txt link.
    Returns the full patched content as a string.
    """
    existing = await _fetch_existing_robots(base_url)
    return _patch_robots(existing, base_url)


def _patch_robots(existing: str, base_url: str) -> str:
    """Merge AI bot rules into existing robots.txt content."""
    lines = existing.strip().splitlines() if existing else []

    # Check what's already present
    existing_lower = existing.lower()
    already_has_sitemap = "sitemap:" in existing_lower
    llms_txt_url = base_url.rstrip("/") + "/llms.txt"
    already_has_llms = "llms.txt" in existing_lower

    # Build block to add
    additions = []

    # Add AI bot allow rules that aren't already present
    for bot in AI_BOTS:
        if bot.lower() not in existing_lower:
            additions.append(f"\n# {bot} — AI search engine crawler")
            additions.append(f"User-agent: {bot}")
            additions.append("Allow: /")
            additions.append("")

    # Add llms.txt reference if not present
    if not already_has_llms:
        additions.append(f"# AI-readable site description")
        additions.append(f"# llms.txt: {llms_txt_url}")
        additions.append("")

    if not additions:
        return existing

    result_parts = []
    if lines:
        result_parts.append("\n".join(lines))
        result_parts.append("")

    result_parts.append("# === AI Search Engine Optimization ===")
    result_parts.append("# Added by GEO Optimizer (causabi.com)")
    result_parts.extend(additions)

    return "\n".join(result_parts)


async def _fetch_existing_robots(base_url: str) -> str:
    """Fetch robots.txt from the site, return empty string if not found."""
    robots_url = base_url.rstrip("/") + "/robots.txt"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(robots_url)
            if resp.status_code == 200 and "text" in resp.headers.get("content-type", ""):
                return resp.text
    except Exception:
        pass
    return ""
