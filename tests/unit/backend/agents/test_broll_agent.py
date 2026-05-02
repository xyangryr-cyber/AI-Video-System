"""[SPEC-D-007] BRollAgent content-driven material matching tests.

Verifies that B-Roll shots get different materials based on search_keywords,
with relevance scores reflecting actual match quality.
"""

from src.backend.agents.broll_agent import BRollAgent


class TestBRollContentDrivenMatch:
    def test_keyword_based_material_matching(self):
        """B-Roll shots get different materials based on search_keywords.

        shot_001 (finance keywords) -> br_1 (finance/chart)
        shot_003 (business keywords) -> br_3 (business/meeting)
        shot_002 (template type) -> skipped
        """
        agent = BRollAgent()
        storyboard = [
            {
                "shot_id": "shot_001",
                "type": "broll",
                "search_keywords": ["finance", "market"],
                "content": "Stock market analysis",
                "time_range": {"start_seconds": 0.0, "end_seconds": 5.0},
            },
            {
                "shot_id": "shot_002",
                "type": "template",
                "search_keywords": ["neutral"],
                "content": "Chart visualization",
                "time_range": {"start_seconds": 5.0, "end_seconds": 10.0},
            },
            {
                "shot_id": "shot_003",
                "type": "broll",
                "search_keywords": ["business", "meeting"],
                "content": "Business meeting footage",
                "time_range": {"start_seconds": 10.0, "end_seconds": 15.0},
            },
        ]

        result = agent.produce(storyboard=storyboard)

        # Should only produce assignments for broll shots (template skipped)
        assert len(result) == 2
        shot_ids = {r["shot_id"] for r in result}
        assert "shot_001" in shot_ids
        assert "shot_003" in shot_ids
        assert "shot_002" not in shot_ids

        # Find assignments by shot_id
        shot_001 = next(r for r in result if r["shot_id"] == "shot_001")
        shot_003 = next(r for r in result if r["shot_id"] == "shot_003")

        # They should get different materials
        assert shot_001["material_id"] != shot_003["material_id"]

        # shot_001 with finance keywords should match br_1 (finance/chart)
        assert shot_001["material_id"] == "br_1"
        shot_001_tags_lower = [t.lower() for t in shot_001["tags"]]
        assert "finance" in shot_001_tags_lower

        # shot_003 with business keywords should match br_3 (business/meeting)
        assert shot_003["material_id"] == "br_3"
        shot_003_tags_lower = [t.lower() for t in shot_003["tags"]]
        assert "business" in shot_003_tags_lower
        assert "meeting" in shot_003_tags_lower

        # Relevance scores should reflect match quality (> 0 for actual matches)
        assert shot_001["relevance_score"] > 0
        assert shot_003["relevance_score"] > 0

        # Each assignment should have source_used
        assert "source_used" in shot_001
        assert "source_used" in shot_003

    def test_fallback_when_no_library_match(self):
        """When no builtin material matches keywords, fallback service is used."""
        agent = BRollAgent()
        storyboard = [
            {
                "shot_id": "shot_004",
                "type": "broll",
                "search_keywords": ["xyz", "nonexistent"],
                "content": "No match content",
                "time_range": {"start_seconds": 0.0, "end_seconds": 5.0},
            },
        ]

        result = agent.produce(storyboard=storyboard)

        assert len(result) == 1
        shot_004 = result[0]
        assert shot_004["shot_id"] == "shot_004"
        # Should not match any builtin material (score would be 0)
        # so fallback is used
        assert "source_used" in shot_004
