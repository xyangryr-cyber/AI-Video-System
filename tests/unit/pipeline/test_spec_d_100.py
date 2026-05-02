"""Tests for [SPEC-D-100] 跨阶段 Claim 生命周期 + Gate-P8/P10/P11 阻断断言."""

from src.backend.gates.claim_checks import (
    check_hard_claims_verified,
    check_shot_claims_verified,
)


class TestAC1:
    """AC-1: P8 shot 渲染前所有 claim_refs verified；失败则仅跳过该 shot"""

    def test_p8_skips_shot_when_claim_unverified(self):
        claim_statuses = {
            "claim_p8_001": "verified",
            "claim_p8_002": "verified",
            "claim_p8_003": "failed",
        }
        shot_claim_refs = [
            {"shot_id": "shot_0", "claim_refs": ["claim_p8_001"]},
            {"shot_id": "shot_1", "claim_refs": ["claim_p8_002", "claim_p8_003"]},
            {"shot_id": "shot_2", "claim_refs": ["claim_p8_001"]},
        ]
        result = check_shot_claims_verified(
            claim_statuses=claim_statuses, shot_claim_refs=shot_claim_refs
        )
        assert result["blocked_shots"] == ["shot_1"]
        assert "shot_0" not in result["blocked_shots"]
        assert "shot_2" not in result["blocked_shots"]
        assert result["has_skips"] is True


class TestAC2:
    """AC-2: P10 合成前所有 hard blocking claims verified；否则 Gate FAIL"""

    def test_p10_fails_on_unverified_hard_claim(self):
        claim_statuses = {
            "claim_p10_h1": "verified",
            "claim_p10_h2": "failed",
            "claim_p10_h3": "verified",
        }
        hard_claim_ids = ["claim_p10_h1", "claim_p10_h2", "claim_p10_h3"]
        result = check_hard_claims_verified(
            claim_statuses=claim_statuses, hard_claim_ids=hard_claim_ids
        )
        assert result["passed"] is False
        assert result["failed_claims"] == ["claim_p10_h2"]


class TestAC3:
    """AC-3: P11 终审同 P10"""

    def test_p11_fails_on_unverified_hard_claim(self):
        claim_statuses = {
            "claim_p11_h1": "verified",
            "claim_p11_h2": "verified",
            "claim_p11_h3": "verified",
        }
        hard_claim_ids = ["claim_p11_h1", "claim_p11_h2", "claim_p11_h3"]
        result = check_hard_claims_verified(
            claim_statuses=claim_statuses, hard_claim_ids=hard_claim_ids
        )
        assert result["passed"] is True
        assert result["failed_claims"] == []

        # Now leave one unverified
        claim_statuses["claim_p11_h2"] = "failed"
        result2 = check_hard_claims_verified(
            claim_statuses=claim_statuses, hard_claim_ids=hard_claim_ids
        )
        assert result2["passed"] is False
        assert "claim_p11_h2" in result2["failed_claims"]


class TestAC4:
    """AC-4: 人为留 1 个 unverified hard claim 时 Gate 返回 BLOCK + 告警事件"""

    def test_gate_emits_block_alert_on_unverified_claim(self):
        claim_statuses = {
            "claim_blk_1": "verified",
            "claim_blk_2": "failed",
        }
        hard_claim_ids = ["claim_blk_1", "claim_blk_2"]
        result = check_hard_claims_verified(
            claim_statuses=claim_statuses, hard_claim_ids=hard_claim_ids
        )
        assert result["passed"] is False
        assert result["verdict"] == "BLOCK"
        assert result["alert_event"] is not None
        assert result["alert_event"]["type"] == "claim.block"
        assert result["alert_event"]["unverified_count"] == 1
