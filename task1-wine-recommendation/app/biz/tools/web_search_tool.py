from app.data.wine_knowledge import PAIRING_RULES, REGION_FACTS, GRAPE_PROFILES


def search_wine_knowledge(query: str) -> str:
    """Search local wine knowledge base. Fallback for web search."""
    query_lower = query.lower()
    results = []

    # Check pairing rules
    for food, info in PAIRING_RULES.items():
        if food.replace("_", " ") in query_lower:
            if "grapes" in info:
                results.append(
                    f"**Pairing: {food.replace('_', ' ').title()}** — "
                    f"Best grapes: {', '.join(info['grapes'])}. {info['why']}"
                )
            elif "tip" in info:
                results.append(f"**{food.replace('_', ' ').title()} tip:** {info['tip']}")

    # Check region facts
    for region, fact in REGION_FACTS.items():
        if region.lower() in query_lower:
            results.append(f"**{region}:** {fact}")

    # Check grape profiles
    for grape, profile in GRAPE_PROFILES.items():
        if grape.lower() in query_lower:
            results.append(
                f"**{grape}:** {profile['description']} "
                f"Taste: {profile['taste']}. "
                f"Body: {profile['body']}. "
                f"Pairs with: {', '.join(profile['pairs_with'])}."
            )

    if not results:
        return "No specific wine knowledge found for this query."

    return "\n\n".join(results)
