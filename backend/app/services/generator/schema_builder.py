"""
Build JSON-LD Schema.org markup for AI and Google visibility.
"""
import json


BUSINESS_TYPE_MAP = {
    "restaurant": "Restaurant",
    "cafe": "CafeOrCoffeeShop",
    "barbershop": "HealthAndBeautyBusiness",
    "salon": "BeautySalon",
    "clinic": "MedicalClinic",
    "hospital": "Hospital",
    "shop": "Store",
    "store": "Store",
    "hotel": "LodgingBusiness",
    "gym": "SportsActivityLocation",
    "default": "LocalBusiness",
}


def build_json_ld(profile: dict, reviews: list) -> str:
    """Build complete JSON-LD with all schema types."""
    schemas = []

    # 1. Main business schema
    business_schema = _build_business_schema(profile, reviews)
    schemas.append(business_schema)

    # 2. FAQ schema (separate entity)
    faq = profile.get("faq") or []
    if faq:
        faq_schema = _build_faq_schema(faq)
        schemas.append(faq_schema)

    # 3. Product/Service schemas (if many items, build ItemList)
    products = profile.get("products_services") or []
    if products and len(products) > 2:
        items_schema = _build_items_schema(profile, products)
        schemas.append(items_schema)

    # If multiple schemas, return as array
    if len(schemas) == 1:
        return json.dumps(schemas[0], ensure_ascii=False, indent=2)
    return json.dumps(schemas, ensure_ascii=False, indent=2)


def _build_business_schema(profile: dict, reviews: list) -> dict:
    category = (profile.get("business_category") or "default").lower()
    schema_type = BUSINESS_TYPE_MAP.get(category, profile.get("business_type", "LocalBusiness"))

    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": profile.get("business_name", ""),
        "description": profile.get("description", ""),
    }

    # Contact
    if profile.get("phone"):
        schema["telephone"] = profile["phone"]
    if profile.get("email"):
        schema["email"] = profile["email"]
    if profile.get("website"):
        schema["url"] = profile["website"]

    # Address
    if profile.get("address"):
        schema["address"] = {
            "@type": "PostalAddress",
            "streetAddress": profile.get("address", ""),
            "addressLocality": profile.get("city", ""),
            "addressCountry": profile.get("country", "RU"),
        }

    # Geo coordinates
    if profile.get("latitude") and profile.get("longitude"):
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": profile["latitude"],
            "longitude": profile["longitude"],
        }

    # Opening hours
    if profile.get("hours"):
        schema["openingHours"] = profile["hours"]

    # Reviews + aggregate rating
    google_reviews = [r for r in reviews if r.get("source") == "google" and not r.get("_is_summary")]
    summary = next((r for r in reviews if r.get("_is_summary")), None)

    if summary and summary.get("rating"):
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(summary["rating"]),
            "reviewCount": str(profile.get("google_review_count", len(google_reviews))),
            "bestRating": "5",
            "worstRating": "1",
        }

    if google_reviews:
        schema["review"] = [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": r.get("author", "Customer")},
                "reviewRating": {"@type": "Rating", "ratingValue": str(r["rating"])},
                "reviewBody": r.get("text", ""),
            }
            for r in google_reviews[:5] if r.get("rating")
        ]

    # Social profiles
    social = profile.get("raw_crawl_data", {}).get("social", {}) or {}
    same_as = [v for v in social.values() if v]
    if same_as:
        schema["sameAs"] = same_as

    # Unique features as amenity
    features = profile.get("unique_features") or []
    if features:
        schema["amenityFeature"] = [
            {"@type": "LocationFeatureSpecification", "name": f, "value": True}
            for f in features
        ]

    return schema


def _build_faq_schema(faq: list) -> dict:
    return {
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


def _build_items_schema(profile: dict, products: list) -> dict:
    """Build ItemList schema for products/services — helps AI cite specific items."""
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Products and Services — {profile.get('business_name', '')}",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product" if profile.get("business_category") in ["shop", "store"] else "Service",
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "offers": {
                        "@type": "Offer",
                        "price": item.get("price", ""),
                        "priceCurrency": "RUB",
                    } if item.get("price") else None,
                },
            }
            for i, item in enumerate(products[:20])
        ],
    }
