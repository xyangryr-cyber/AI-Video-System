"""Tests for [SPEC-D-011] L2 LLM Reviewer Framework."""


class TestAC1L2ReviewerTokenTracking:
    def test_l2_tracks_tokens(self):
        from src.backend.agents.l2_reviewer import L2Reviewer

        class TestL2(L2Reviewer):
            def review_semantic(self, artifact):
                return {"verdict": "PASS", "notes": ["semantic ok"]}

        reviewer = TestL2()
        result = reviewer.review({})
        assert "verdict" in result
        assert result.get("input_tokens", 0) >= 0
        assert result.get("output_tokens", 0) >= 0


class TestAC2L2StructuredOutput:
    def test_l2_returns_verdict_format(self):
        from src.backend.agents.l2_reviewer import L2Reviewer

        class TestL2(L2Reviewer):
            def review_semantic(self, artifact):
                return {
                    "verdict": "PASS",
                    "notes": ["semantic check passed"],
                    "blocking_issues": [],
                }

        reviewer = TestL2()
        result = reviewer.review({})
        assert result["verdict"] == "PASS"


class TestAC3DualLayerComposition:
    def test_dual_layer_l1_pass_triggers_l2(self):
        from src.backend.agents.l1_reviewer import L1Reviewer
        from src.backend.agents.l2_reviewer import L2Reviewer
        from src.backend.agents.dual_layer_reviewer import DualLayerReviewer

        class PassL1(L1Reviewer):
            def check_ok(self, artifact):
                return True, "ok"

        class PassL2(L2Reviewer):
            def review_semantic(self, artifact):
                return {"verdict": "PASS", "notes": ["l2 ok"]}

        l1 = PassL1()
        l1.register_checks(["check_ok"])
        l2 = PassL2()
        dual = DualLayerReviewer(l1_reviewer=l1, l2_reviewer=l2)
        result = dual.review({})
        assert result["verdict"] == "PASS"
        assert result["l2_triggered"] is True


class TestAC4L1FailSkipsL2:
    def test_l1_fail_returns_immediately(self):
        from src.backend.agents.l1_reviewer import L1Reviewer
        from src.backend.agents.l2_reviewer import L2Reviewer
        from src.backend.agents.dual_layer_reviewer import DualLayerReviewer

        class FailL1(L1Reviewer):
            def check_bad(self, artifact):
                return False, "bad"

        l1 = FailL1()
        l1.register_checks(["check_bad"])
        l2 = L2Reviewer()
        dual = DualLayerReviewer(l1_reviewer=l1, l2_reviewer=l2)
        result = dual.review({})
        assert result["l2_triggered"] is False
        assert result.get("l2_token_cost", 0) == 0


class TestAC5MergedBlockingIssues:
    def test_both_layers_issues_merged(self):
        from src.backend.agents.l1_reviewer import L1Reviewer
        from src.backend.agents.l2_reviewer import L2Reviewer
        from src.backend.agents.dual_layer_reviewer import DualLayerReviewer

        class FailL2(L2Reviewer):
            def review_semantic(self, artifact):
                return {"verdict": "FAIL", "blocking_issues": ["semantic mismatch"]}

        l1 = L1Reviewer()
        l1.register_checks([])
        l2 = FailL2()
        dual = DualLayerReviewer(l1_reviewer=l1, l2_reviewer=l2)
        result = dual.review({})
        assert "blocking_issues" in result
        assert "semantic mismatch" in result["blocking_issues"]


class TestAC6CostLogging:
    def test_cost_logged_per_review(self):
        from src.backend.agents.l2_reviewer import L2Reviewer

        class CostL2(L2Reviewer):
            def review_semantic(self, artifact):
                return {"verdict": "PASS"}

        reviewer = CostL2()
        result = reviewer.review({})
        assert "cost_usd" in result
        assert result["cost_usd"] >= 0
