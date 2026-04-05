"""
Generate llms.txt file — the AI-readable site description standard.
"""


def build_llms_txt(profile: dict, reviews: list) -> str:
    """Build llms.txt content from business profile."""
    name = profile.get("business_name", "Business")
    short_desc = profile.get("short_description") or profile.get("description", "")
    description = profile.get("description", "")
    address = profile.get("address", "")
    city = profile.get("city", "")
    phone = profile.get("phone", "")
    email = profile.get("email", "")
    hours = profile.get("hours", "")
    website = profile.get("website", "")
    products_services = profile.get("products_services") or []
    faq = profile.get("faq") or []
    unique_features = profile.get("unique_features") or []

    lines = [f"# {name}"]
    if short_desc:
        lines.append(f"> {short_desc}")
    lines.append("")

    if description:
        lines.append("## About")
        lines.append(description)
        lines.append("")

    if unique_features:
        lines.append("## Key Features")
        for feature in unique_features:
            lines.append(f"- {feature}")
        lines.append("")

    if products_services:
        lines.append("## Products & Services")
        # Group by category
        categories: dict[str, list] = {}
        for item in products_services:
            cat = item.get("category") or "General"
            categories.setdefault(cat, []).append(item)

        for cat, items in categories.items():
            if len(categories) > 1:
                lines.append(f"\n### {cat}")
            for item in items:
                price_str = f" — {item['price']}" if item.get("price") else ""
                desc_str = f": {item['description']}" if item.get("description") else ""
                lines.append(f"- **{item['name']}**{price_str}{desc_str}")
        lines.append("")

    if faq:
        lines.append("## Frequently Asked Questions")
        for qa in faq[:12]:
            lines.append(f"\n**Q: {qa['question']}**")
            lines.append(f"A: {qa['answer']}")
        lines.append("")

    # Reviews summary
    google_reviews = [r for r in reviews if r.get("source") == "google" and r.get("rating") and not r.get("_is_summary")]
    if google_reviews:
        lines.append("## Customer Reviews")
        summary = next((r for r in reviews if r.get("_is_summary")), None)
        if summary:
            lines.append(f"Overall rating: {summary['rating']} stars")
        for review in google_reviews[:5]:
            if review.get("text"):
                lines.append(f"\n> \"{review['text'][:200]}\"")
                lines.append(f"> — {review.get('author', 'Customer')}, {review.get('rating', '')}★")
        lines.append("")

    lines.append("## Contact & Location")
    if address:
        lines.append(f"- Address: {address}{', ' + city if city else ''}")
    if phone:
        lines.append(f"- Phone: {phone}")
    if email:
        lines.append(f"- Email: {email}")
    if website:
        lines.append(f"- Website: {website}")
    if hours:
        lines.append(f"- Hours: {hours}")

    social = profile.get("raw_crawl_data", {}).get("social", {}) or {}
    if social:
        lines.append("\n## Social Media")
        for platform, url in social.items():
            if url:
                lines.append(f"- {platform.capitalize()}: {url}")

    return "\n".join(lines)
