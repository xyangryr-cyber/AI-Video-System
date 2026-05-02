"""Tests for [SPEC-D-010] L1 Programmatic Reviewer Framework."""

import pytest


class TestAC1BaseReviewerAbstractClass:
    def test_base_reviewer_has_review_method(self):
        from src.backend.agents.base_reviewer import BaseReviewer

        assert hasattr(BaseReviewer, "review")

    def test_cannot_instantiate_abstract(self):
        from src.backend.agents.base_reviewer import BaseReviewer

        with pytest.raises(TypeError):
            BaseReviewer()


class TestAC2L1ReviewerCheckRegistration:
    def test_register_checks(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_one(self, artifact):
                return True, "ok"

            def check_two(self, artifact):
                return False, "bad"

        reviewer = TestL1()
        reviewer.register_checks(["check_one", "check_two"])
        assert len(reviewer._checks) == 2


class TestAC3L1ReviewerAggregation:
    def test_aggregate_into_standard_verdict(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_pass(self, artifact):
                return True, "all good"

        reviewer = TestL1()
        reviewer.register_checks(["check_pass"])
        result = reviewer.review({})
        assert "verdict" in result
        assert "notes" in result
        assert "blocking_issues" in result
        assert result["verdict"] == "PASS"

    def test_fail_blocks_gate(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_fail(self, artifact):
                return False, "something wrong"

        reviewer = TestL1()
        reviewer.register_checks(["check_fail"])
        result = reviewer.review({})
        assert result["verdict"] == "FAIL"
        assert len(result["blocking_issues"]) == 1


class TestAC4TokenCountZero:
    def test_token_count_is_zero(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_a(self, artifact):
                return True, "ok"

        reviewer = TestL1()
        reviewer.register_checks(["check_a"])
        result = reviewer.review({})
        assert result.get("token_count", 0) == 0


class TestAC5FailedChecksInBlockingIssues:
    def test_failed_check_name_in_blocking(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_bad(self, artifact):
                return False, "failed due to X"

        reviewer = TestL1()
        reviewer.register_checks(["check_bad"])
        result = reviewer.review({})
        assert len(result["blocking_issues"]) == 1
        assert "check_bad" in result["blocking_issues"][0]


class TestAC6SkipL2OnFail:
    def test_skip_l2_when_l1_fails(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_fail(self, artifact):
                return False, "fail"

        reviewer = TestL1()
        reviewer.register_checks(["check_fail"])
        result = reviewer.review({})
        assert result.get("skip_l2_on_fail") is True

    def test_l2_not_skipped_when_l1_passes(self):
        from src.backend.agents.l1_reviewer import L1Reviewer

        class TestL1(L1Reviewer):
            def check_pass(self, artifact):
                return True, "ok"

        reviewer = TestL1()
        reviewer.register_checks(["check_pass"])
        result = reviewer.review({})
        assert result.get("skip_l2_on_fail") is False
