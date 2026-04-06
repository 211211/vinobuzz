"""Tests for citation parsing from generator output."""

from app.biz.agent.sommelier.utils.citation import parse_citations


class TestParseCitations:
    def test_single_citation(self):
        text = "I recommend **Chateau Margaux 2018** [1](#FR-BDX-001) — excellent wine."
        citations = parse_citations(text)
        assert len(citations) == 1
        assert citations[0].id == "FR-BDX-001"
        assert citations[0].name == "Chateau Margaux 2018"
        assert citations[0].price_hkd == 1800

    def test_multiple_citations(self):
        text = (
            "Try **Chateau Margaux 2018** [1](#FR-BDX-001) or "
            "**Chateau Leoville-Barton 2019** [2](#FR-BDX-002)."
        )
        citations = parse_citations(text)
        assert len(citations) == 2
        assert citations[0].id == "FR-BDX-001"
        assert citations[1].id == "FR-BDX-002"

    def test_no_citations(self):
        text = "What kind of wine are you looking for?"
        citations = parse_citations(text)
        assert len(citations) == 0

    def test_duplicate_citations_deduplicated(self):
        text = (
            "Try [1](#FR-BDX-001) — great wine. "
            "As I mentioned, [1](#FR-BDX-001) is perfect."
        )
        citations = parse_citations(text)
        assert len(citations) == 1

    def test_unknown_sku_ignored(self):
        text = "Try [1](#UNKNOWN-SKU) for something different."
        citations = parse_citations(text)
        assert len(citations) == 0

    def test_citation_has_correct_fields(self):
        text = "[1](#FR-BRG-001)"
        citations = parse_citations(text)
        assert len(citations) == 1
        c = citations[0]
        assert c.id == "FR-BRG-001"
        assert c.name == "Domaine Faiveley Gevrey-Chambertin 2020"
        assert c.type == "red"
        assert c.region == "Burgundy"
        assert c.price_hkd == 650
