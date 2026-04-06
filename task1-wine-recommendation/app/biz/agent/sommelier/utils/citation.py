import re

from app.biz.agent.sommelier.schemas.recommendation import WineCitation
from app.data.wines import WINE_INVENTORY

_WINE_BY_SKU: dict[str, dict] = {w["sku"]: w for w in WINE_INVENTORY}

# Matches [1](#FR-BDX-001) style citations
_CITATION_PATTERN = re.compile(r"\[(\d+)\]\(#([A-Za-z0-9-]+)\)")


def parse_citations(text: str) -> list[WineCitation]:
    """Extract wine citations from generator output text."""
    citations: list[WineCitation] = []
    seen_skus: set[str] = set()

    for match in _CITATION_PATTERN.finditer(text):
        sku = match.group(2)
        if sku in seen_skus:
            continue
        seen_skus.add(sku)

        wine = _WINE_BY_SKU.get(sku)
        if wine:
            citations.append(
                WineCitation(
                    id=sku,
                    name=wine["name"],
                    type=wine["type"],
                    region=wine.get("region", ""),
                    price_hkd=wine["price_hkd"],
                    match_reasons=wine.get("match_reasons", []),
                )
            )

    return citations
