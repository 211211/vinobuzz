from typing import Optional

from app.data.wines import WINE_INVENTORY


def search_wines(
    query: Optional[str] = None,
    type_filter: Optional[str] = None,
    budget_min: Optional[int] = None,
    budget_max: Optional[int] = None,
    country_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
    occasion_tags: Optional[list[str]] = None,
    grape_filter: Optional[str] = None,
    body_filter: Optional[str] = None,
    sweetness_filter: Optional[str] = None,
    food_pairing_filter: Optional[str] = None,
    exclude_skus: Optional[list[str]] = None,
    top_k: int = 5,
) -> dict:
    """Filter + rank wines from inventory. Returns top_k sorted by score."""
    occasion_tags = occasion_tags or []
    exclude_skus = exclude_skus or []
    results = _score_wines(
        query=query,
        type_filter=type_filter,
        budget_min=budget_min,
        budget_max=budget_max,
        country_filter=country_filter,
        region_filter=region_filter,
        occasion_tags=occasion_tags,
        grape_filter=grape_filter,
        body_filter=body_filter,
        sweetness_filter=sweetness_filter,
        food_pairing_filter=food_pairing_filter,
        exclude_skus=exclude_skus,
    )

    if len(results) < 3:
        relaxed_results = _relax_and_search(
            query=query,
            type_filter=type_filter,
            budget_min=budget_min,
            budget_max=budget_max,
            country_filter=country_filter,
            region_filter=region_filter,
            occasion_tags=occasion_tags,
            grape_filter=grape_filter,
            body_filter=body_filter,
            sweetness_filter=sweetness_filter,
            food_pairing_filter=food_pairing_filter,
            exclude_skus=exclude_skus,
        )
        if len(relaxed_results) > len(results):
            return {"wines": relaxed_results[:top_k], "relaxed": True}

    return {"wines": results[:top_k], "relaxed": False}


def _score_wines(
    query: Optional[str],
    type_filter: Optional[str],
    budget_min: Optional[int],
    budget_max: Optional[int],
    country_filter: Optional[str],
    region_filter: Optional[str],
    occasion_tags: list[str],
    grape_filter: Optional[str],
    body_filter: Optional[str],
    sweetness_filter: Optional[str],
    food_pairing_filter: Optional[str],
    exclude_skus: list[str],
) -> list[dict]:
    scored = []
    for wine in WINE_INVENTORY:
        if wine["sku"] in exclude_skus:
            continue
        if not wine.get("in_stock", True):
            continue

        score = 0
        match_reasons = []

        # Type match
        if type_filter and wine["type"].lower() == type_filter.lower():
            score += 10
            match_reasons.append(f"{wine['type'].title()} wine as requested")
        elif type_filter:
            continue  # Hard filter — skip wines that don't match type

        # Budget match
        price = wine["price_hkd"]
        if budget_max and price <= budget_max:
            score += 8
            match_reasons.append(f"Within budget (HK${price})")
        elif budget_max and price > budget_max:
            continue  # Hard filter
        if budget_min and price >= budget_min:
            score += 2

        # Region match (hard filter)
        if region_filter and wine["region"].lower() == region_filter.lower():
            score += 6
            match_reasons.append(f"From {wine['region']} as requested")
        elif region_filter:
            continue

        # Country match (hard filter)
        if country_filter and wine["country"].lower() == country_filter.lower():
            score += 4
            match_reasons.append(f"{wine['country']} wine as requested")
        elif country_filter:
            continue

        # Occasion match
        for tag in occasion_tags:
            if tag.lower() in [o.lower() for o in wine.get("occasions", [])]:
                score += 5
                match_reasons.append(f"Great for {tag}")

        # Grape match (hard filter)
        if grape_filter and grape_filter.lower() in wine.get("grape", "").lower():
            score += 4
            match_reasons.append(f"Made from {wine['grape']}")
        elif grape_filter:
            continue

        # Body match
        if body_filter and wine.get("body", "").lower() == body_filter.lower():
            score += 3
            match_reasons.append(f"{wine['body'].title()}-bodied as preferred")

        # Sweetness match
        if sweetness_filter and wine.get("sweetness", "").lower() == sweetness_filter.lower():
            score += 3
            match_reasons.append(f"{wine['sweetness'].title()} style")

        # Food pairing match
        if food_pairing_filter:
            pairings = [p.lower() for p in wine.get("food_pairing", [])]
            if food_pairing_filter.lower() in pairings:
                score += 3
                match_reasons.append(f"Pairs well with {food_pairing_filter}")

        # Free-text fuzzy match
        if query:
            keywords = query.lower().split()
            searchable = f"{wine['name']} {wine.get('grape', '')} {wine.get('tasting_notes', '')} {wine.get('region', '')} {wine.get('country', '')}".lower()
            for kw in keywords:
                if kw in searchable:
                    score += 2
                    match_reasons.append(f"Matches '{kw}'")

        # In-stock bonus
        if wine.get("in_stock"):
            score += 1

        # Rating bonus
        score += wine.get("rating", 0)

        if score > 0:
            scored.append({**wine, "score": round(score, 1), "match_reasons": match_reasons})

    scored.sort(key=lambda w: w["score"], reverse=True)
    return scored


def _relax_and_search(
    query: Optional[str],
    type_filter: Optional[str],
    budget_min: Optional[int],
    budget_max: Optional[int],
    country_filter: Optional[str],
    region_filter: Optional[str],
    occasion_tags: list[str],
    grape_filter: Optional[str],
    body_filter: Optional[str],
    sweetness_filter: Optional[str],
    food_pairing_filter: Optional[str],
    exclude_skus: list[str],
) -> list[dict]:
    """Progressively relax filters to find more results."""
    # Step 1: Drop region, keep country
    results = _score_wines(
        query=query, type_filter=type_filter, budget_min=budget_min,
        budget_max=budget_max, country_filter=country_filter, region_filter=None,
        occasion_tags=occasion_tags, grape_filter=grape_filter,
        body_filter=body_filter, sweetness_filter=sweetness_filter,
        food_pairing_filter=food_pairing_filter, exclude_skus=exclude_skus,
    )
    if len(results) >= 3:
        return results

    # Step 2: Expand budget by ±20%
    expanded_min = int(budget_min * 0.8) if budget_min else None
    expanded_max = int(budget_max * 1.2) if budget_max else None
    results = _score_wines(
        query=query, type_filter=type_filter, budget_min=expanded_min,
        budget_max=expanded_max, country_filter=country_filter, region_filter=None,
        occasion_tags=occasion_tags, grape_filter=grape_filter,
        body_filter=body_filter, sweetness_filter=sweetness_filter,
        food_pairing_filter=food_pairing_filter, exclude_skus=exclude_skus,
    )
    if len(results) >= 3:
        return results

    # Step 3: Drop grape/body/sweetness
    results = _score_wines(
        query=query, type_filter=type_filter, budget_min=expanded_min,
        budget_max=expanded_max, country_filter=country_filter, region_filter=None,
        occasion_tags=occasion_tags, grape_filter=None,
        body_filter=None, sweetness_filter=None,
        food_pairing_filter=food_pairing_filter, exclude_skus=exclude_skus,
    )
    if len(results) >= 3:
        return results

    # Step 4: Keep only type filter
    results = _score_wines(
        query=query, type_filter=type_filter, budget_min=None,
        budget_max=None, country_filter=None, region_filter=None,
        occasion_tags=[], grape_filter=None,
        body_filter=None, sweetness_filter=None,
        food_pairing_filter=None, exclude_skus=exclude_skus,
    )
    return results


def format_wine_context(wines: list[dict]) -> str:
    """Format wine list into context string for LLM injection."""
    parts = []
    for wine in wines:
        parts.append(
            f"<<<WINE>>>\n"
            f"SKU: {wine['sku']}\n"
            f"Name: {wine['name']}\n"
            f"Type: {wine['type'].title()} | Region: {wine.get('region', 'N/A')}, {wine.get('country', 'N/A')}\n"
            f"Price: HK${wine['price_hkd']:,}\n"
            f"Grape: {wine.get('grape', 'N/A')}\n"
            f"Tasting: {wine.get('tasting_notes', 'N/A')}\n"
            f"Occasions: {', '.join(wine.get('occasions', []))}\n"
            f"Food pairing: {', '.join(wine.get('food_pairing', []))}\n"
            f"Rating: {wine.get('rating', 'N/A')}/5\n"
            f"<<<END WINE>>>"
        )
    return "\n\n".join(parts)
