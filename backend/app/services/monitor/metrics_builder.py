"""
AI Visibility Score — composite metric showing how visible a business is
in AI search engines. Core value metric of the product.

Score components:
- Mention rate: % of queries where business is mentioned (0-100)
- Position score: weighted by rank position (1st = full, 5th = partial)
- Product coverage: % of products mentioned across all queries
- Engine diversity: bonus for being mentioned on multiple AI engines
- Trend: score change vs previous week

Final score: 0–100
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


async def build_visibility_report(site_id: str, db: AsyncSession) -> dict:
    """
    Build complete AI visibility report for a site.
    Returns score, trend, per-query breakdown, per-product breakdown, competitors.
    """
    from app.models import MonitoringResult, SiteProfile

    # Load profile for product names and target queries
    profile_result = await db.execute(
        select(SiteProfile).where(SiteProfile.site_id == site_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        return _empty_report(site_id)

    products = [p.get("name", "") for p in (profile.products_services or [])]
    target_queries = profile.target_queries or []

    # All results for this site
    all_results_q = await db.execute(
        select(MonitoringResult)
        .where(MonitoringResult.site_id == site_id)
        .order_by(MonitoringResult.checked_at.desc())
    )
    all_results = all_results_q.scalars().all()

    if not all_results:
        return _empty_report(site_id, profile=profile)

    # Latest check per query+engine (most recent snapshot)
    latest = _get_latest_per_query(all_results)

    # Score components
    mention_rate = _calc_mention_rate(latest)
    position_score = _calc_position_score(latest)
    product_coverage = _calc_product_coverage(latest, products)
    engine_diversity = _calc_engine_diversity(latest)

    # Composite score (weighted)
    score = round(
        mention_rate * 0.40
        + position_score * 0.30
        + product_coverage * 0.20
        + engine_diversity * 0.10,
        1,
    )

    # Trend: compare to results from 7+ days ago
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    old_results = [r for r in all_results if r.checked_at < cutoff]
    old_latest = _get_latest_per_query(old_results)
    old_score = None
    if old_latest:
        old_mention = _calc_mention_rate(old_latest)
        old_pos = _calc_position_score(old_latest)
        old_prod = _calc_product_coverage(old_latest, products)
        old_div = _calc_engine_diversity(old_latest)
        old_score = round(
            old_mention * 0.40 + old_pos * 0.30 + old_prod * 0.20 + old_div * 0.10, 1
        )

    trend = round(score - old_score, 1) if old_score is not None else None
    trend_label = _trend_label(trend)

    # Per-query breakdown
    per_query = _build_per_query(latest, target_queries)

    # Per-product breakdown
    per_product = _build_per_product(latest, products)

    # Competitors seen across all results
    competitors = _collect_competitors(latest)

    # Engine breakdown
    by_engine = _build_engine_breakdown(latest)

    # Historical timeline (last 30 checks, grouped by date)
    timeline = _build_timeline(all_results)

    return {
        "site_id": site_id,
        "business_name": profile.business_name,
        "score": score,
        "score_label": _score_label(score),
        "trend": trend,
        "trend_label": trend_label,
        "components": {
            "mention_rate": round(mention_rate, 1),
            "position_score": round(position_score, 1),
            "product_coverage": round(product_coverage, 1),
            "engine_diversity": round(engine_diversity, 1),
        },
        "per_query": per_query,
        "per_product": per_product,
        "by_engine": by_engine,
        "top_competitors": competitors[:10],
        "timeline": timeline,
        "last_checked": max(r.checked_at for r in all_results).isoformat(),
        "total_checks": len(all_results),
    }


def _get_latest_per_query(results: list) -> list:
    """Keep only the most recent result per (query, engine) pair."""
    seen: dict[tuple, object] = {}
    for r in sorted(results, key=lambda x: x.checked_at, reverse=True):
        key = (r.query, r.engine)
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def _calc_mention_rate(results: list) -> float:
    if not results:
        return 0.0
    mentioned = sum(1 for r in results if r.mentioned)
    return (mentioned / len(results)) * 100


def _calc_position_score(results: list) -> float:
    """Score based on position: 1st=100, 2nd=75, 3rd=50, 4th=25, else=10."""
    position_weights = {1: 100, 2: 75, 3: 50, 4: 25}
    if not results:
        return 0.0
    total = 0.0
    for r in results:
        if r.mentioned and r.position:
            total += position_weights.get(r.position, 10)
        elif r.mentioned:
            total += 15  # mentioned but position unknown
    return min(total / len(results), 100.0)


def _calc_product_coverage(results: list, products: list) -> float:
    """% of products that were mentioned at least once."""
    if not products:
        return 50.0  # neutral if no products defined
    mentioned_products: set[str] = set()
    for r in results:
        for pm in (r.product_mentions or []):
            if pm.get("mentioned") and pm.get("product"):
                mentioned_products.add(pm["product"].lower())
    coverage = sum(
        1 for p in products if p.lower() in mentioned_products
    ) / len(products)
    return coverage * 100


def _calc_engine_diversity(results: list) -> float:
    """Bonus for being mentioned across multiple AI engines."""
    mentioned_engines = {r.engine for r in results if r.mentioned}
    engine_count = len(mentioned_engines)
    if engine_count >= 3:
        return 100.0
    elif engine_count == 2:
        return 66.0
    elif engine_count == 1:
        return 33.0
    return 0.0


def _build_per_query(results: list, target_queries: list) -> list:
    """Build per-query breakdown: is business mentioned, at what position, on which engines."""
    grouped: dict[str, list] = {}
    for r in results:
        grouped.setdefault(r.query, []).append(r)

    output = []
    for query in (target_queries or list(grouped.keys())):
        query_results = grouped.get(query, [])
        engines_data = []
        for r in query_results:
            engines_data.append({
                "engine": r.engine,
                "mentioned": r.mentioned,
                "position": r.position,
                "snippet": r.snippet,
                "checked_at": r.checked_at.isoformat() if r.checked_at else None,
            })
        is_mentioned = any(r.mentioned for r in query_results)
        best_position = min(
            (r.position for r in query_results if r.mentioned and r.position),
            default=None,
        )
        output.append({
            "query": query,
            "mentioned": is_mentioned,
            "best_position": best_position,
            "engines": engines_data,
        })

    return output


def _build_per_product(results: list, products: list) -> list:
    """Build per-product visibility: how often each product/service is mentioned."""
    if not products:
        return []

    product_stats: dict[str, dict] = {
        p: {"name": p, "mention_count": 0, "queries": []} for p in products
    }

    for r in results:
        for pm in (r.product_mentions or []):
            name = pm.get("product", "")
            # Match against known products (case-insensitive substring)
            for p in products:
                if name.lower() in p.lower() or p.lower() in name.lower():
                    if pm.get("mentioned"):
                        product_stats[p]["mention_count"] += 1
                        if r.query not in product_stats[p]["queries"]:
                            product_stats[p]["queries"].append(r.query)

    total_checks = max(len(results), 1)
    output = []
    for p, stats in product_stats.items():
        output.append({
            "name": p,
            "mention_count": stats["mention_count"],
            "mention_rate": round((stats["mention_count"] / total_checks) * 100, 1),
            "mentioned_in_queries": stats["queries"],
        })

    return sorted(output, key=lambda x: x["mention_count"], reverse=True)


def _collect_competitors(results: list) -> list:
    """Collect all competitor names mentioned across results, sorted by frequency."""
    counter: dict[str, int] = {}
    for r in results:
        for comp in (r.competitor_mentions or []):
            if comp:
                counter[comp] = counter.get(comp, 0) + 1
    return sorted(counter.keys(), key=lambda k: -counter[k])


def _build_engine_breakdown(results: list) -> dict:
    """Per-engine mention statistics."""
    engines: dict[str, dict] = {}
    for r in results:
        e = r.engine
        if e not in engines:
            engines[e] = {"total": 0, "mentioned": 0, "avg_position": []}
        engines[e]["total"] += 1
        if r.mentioned:
            engines[e]["mentioned"] += 1
        if r.mentioned and r.position:
            engines[e]["avg_position"].append(r.position)

    output = {}
    for e, stats in engines.items():
        positions = stats["avg_position"]
        output[e] = {
            "total_checks": stats["total"],
            "mentions": stats["mentioned"],
            "mention_rate": round((stats["mentioned"] / stats["total"]) * 100, 1) if stats["total"] else 0,
            "avg_position": round(sum(positions) / len(positions), 1) if positions else None,
        }
    return output


def _build_timeline(results: list) -> list:
    """Group results by date and compute daily mention rate."""
    by_date: dict[str, list] = {}
    for r in results:
        date_str = r.checked_at.strftime("%Y-%m-%d")
        by_date.setdefault(date_str, []).append(r)

    timeline = []
    for date_str in sorted(by_date.keys()):
        day_results = by_date[date_str]
        mentioned = sum(1 for r in day_results if r.mentioned)
        timeline.append({
            "date": date_str,
            "checks": len(day_results),
            "mentions": mentioned,
            "mention_rate": round((mentioned / len(day_results)) * 100, 1),
        })
    return timeline[-30:]  # last 30 days


def _score_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    elif score >= 20:
        return "Poor"
    return "Not visible"


def _trend_label(trend: float | None) -> str:
    if trend is None:
        return "new"
    if trend > 5:
        return "up"
    elif trend < -5:
        return "down"
    return "stable"


def _empty_report(site_id: str, profile=None) -> dict:
    return {
        "site_id": site_id,
        "business_name": profile.business_name if profile else None,
        "score": 0,
        "score_label": "Not visible",
        "trend": None,
        "trend_label": "new",
        "components": {
            "mention_rate": 0,
            "position_score": 0,
            "product_coverage": 0,
            "engine_diversity": 0,
        },
        "per_query": [],
        "per_product": [],
        "by_engine": {},
        "top_competitors": [],
        "timeline": [],
        "last_checked": None,
        "total_checks": 0,
    }
