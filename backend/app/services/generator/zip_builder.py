"""
Build ZIP export package with all generated files for download.
Users get a single ZIP to manually add files to their site.
"""
import io
import zipfile
from datetime import datetime


def build_export_zip(
    llms_txt: str,
    schema_json: str,
    robots_txt: str,
    faq_html: str,
    business_name: str = "",
    slug: str = "",
) -> bytes:
    """
    Pack all generated files into a ZIP for user download.
    Returns ZIP as bytes.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. llms.txt — place in site root
        zf.writestr("llms.txt", llms_txt)

        # 2. JSON-LD schema — can be embedded in <head> or added via GTM
        zf.writestr("schema.jsonld", schema_json)

        # 3. Patched robots.txt — replace site's existing robots.txt
        if robots_txt:
            zf.writestr("robots.txt", robots_txt)

        # 4. FAQ HTML block — embed on appropriate page
        if faq_html:
            zf.writestr("faq-block.html", faq_html)

        # 5. README with installation instructions
        readme = _build_readme(business_name, slug)
        zf.writestr("README.txt", readme)

        # 6. GTM snippet for easy schema injection
        gtm_snippet = _build_gtm_snippet(schema_json)
        zf.writestr("gtm-schema-snippet.html", gtm_snippet)

    return buf.getvalue()


def _build_readme(business_name: str, slug: str) -> str:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    hosted_url = f"https://causabi.com/b/{slug}" if slug else "https://causabi.com"

    return f"""GEO Optimizer — AI Search Visibility Package
Generated: {date_str}
Business: {business_name}
Hosted profile: {hosted_url}

=== INSTALLATION GUIDE ===

1. llms.txt
   Upload to your website root: https://yourdomain.com/llms.txt
   This file helps AI search engines (ChatGPT, Perplexity, etc.) understand your business.

2. schema.jsonld (JSON-LD structured data)
   Add to your website's <head> section:
   <script type="application/ld+json">
   [paste contents of schema.jsonld here]
   </script>

   OR use the GTM snippet (see gtm-schema-snippet.html) to inject via Google Tag Manager.

3. robots.txt
   Add the AI bot rules from robots.txt to your existing /robots.txt file.
   This allows AI crawlers to index your content.

4. faq-block.html
   Paste this HTML block on your FAQ page or About page.
   It includes both visual FAQ and embedded schema markup.

=== HOSTED PROFILE ===
Your business profile is also publicly available at:
{hosted_url}

This page is already optimized for AI indexing and submitted to IndexNow.
AI search engines can find your business directly through this URL.

=== NEED HELP? ===
Visit https://causabi.com or email support@causabi.com
"""


def _build_gtm_snippet(schema_json: str) -> str:
    """Build a Google Tag Manager custom HTML tag to inject schema."""
    return f"""<!-- Google Tag Manager Custom HTML Tag -->
<!-- Tag type: Custom HTML -->
<!-- Trigger: All Pages (or specific pages) -->

<script type="application/ld+json">
{schema_json}
</script>

<!--
  How to use:
  1. Open Google Tag Manager (tagmanager.google.com)
  2. Create new tag → Custom HTML
  3. Paste this entire block as the tag content
  4. Set trigger: All Pages (or choose specific pages)
  5. Save and Publish
-->
"""
