"""
Build HTML FAQ block with embedded FAQ schema markup.
Used for hosted profile pages (/b/<slug>).
"""
import json


def build_faq_html(faq: list, business_name: str = "") -> str:
    """Build standalone HTML FAQ section with JSON-LD schema inline."""
    if not faq:
        return ""

    # Build FAQ schema
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"],
                },
            }
            for qa in faq
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    # Build HTML items
    items_html = "\n".join(
        f"""    <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
      <h3 class="faq-question" itemprop="name">{_escape(qa["question"])}</h3>
      <div class="faq-answer" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text">{_escape(qa["answer"])}</p>
      </div>
    </div>"""
        for qa in faq
    )

    title = f"Frequently Asked Questions — {business_name}" if business_name else "Frequently Asked Questions"

    return f"""<section class="faq-section" itemscope itemtype="https://schema.org/FAQPage">
  <h2>{_escape(title)}</h2>
{items_html}
</section>

<script type="application/ld+json">
{schema_json}
</script>"""


def _escape(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
