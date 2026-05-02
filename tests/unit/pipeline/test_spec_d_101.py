"""Tests for [SPEC-D-101] 用户质疑 / 补充 Phase Scenario Cards."""

from src.backend.engine.scenario_cards.challenge_claim_card import (
    ChallengeClaimCard,
)
from src.backend.engine.scenario_cards.supplement_claim_card import (
    SupplementClaimCard,
)
from src.backend.services.artifact_damage_marker import ArtifactDamageMarker


class TestAC1:
    """AC-1: challenge_claim 后 60s SLA 内下游 artifacts 标 damaged"""

    def test_challenge_marks_downstream_damaged_within_sla(self):
        marker = ArtifactDamageMarker()
        downstream = [
            {
                "artifact_id": "art_001",
                "claim_ids": ["claim_xyz"],
                "status": "complete",
            },
            {
                "artifact_id": "art_002",
                "claim_ids": ["claim_abc"],
                "status": "complete",
            },
            {
                "artifact_id": "art_003",
                "claim_ids": ["claim_xyz"],
                "status": "complete",
            },
        ]
        result = marker.mark_damaged(
            claim_id="claim_xyz", downstream_artifacts=downstream
        )
        assert result["elapsed_seconds"] < 60
        assert result["damaged_count"] == 2
        damaged_ids = {d["artifact_id"] for d in result["damaged"]}
        assert damaged_ids == {"art_001", "art_003"}


class TestAC2:
    """AC-2: supplement_claim 后新 claim 入队且下游阻断"""

    def test_supplement_enqueues_new_claim_and_blocks(self):
        card = SupplementClaimCard()
        result = card.handle(
            text="GDP grew 5.2% in 2024",
            claim_type="data",
            source_phase="user_input",
            source_artifact="supplement_claim",
        )
        assert result["new_claim"]["text"] == "GDP grew 5.2% in 2024"
        assert result["new_claim"]["claim_type"] == "data"
        assert result["new_claim"]["verification_status"] == "pending"
        assert result["new_claim"]["blocking_level"] == "hard"
        assert result["blocked"] is True


class TestAC3:
    """AC-3: 幂等规则：同 claim_id + evidence_hash 24h 内第二次质疑被丢弃"""

    def test_challenge_idempotency_within_24h(self):
        card = ChallengeClaimCard()
        claim_id = "claim_abc123"
        evidence_hash = "a1b2c3d4e5f6"

        # First challenge should be accepted
        result1 = card.challenge_with_idempotency(
            claim_id=claim_id,
            reason="data seems wrong",
            evidence_hash=evidence_hash,
        )
        assert result1["accepted"] is True

        # Second identical challenge within 24h should be discarded
        result2 = card.challenge_with_idempotency(
            claim_id=claim_id,
            reason="same issue",
            evidence_hash=evidence_hash,
        )
        assert result2["accepted"] is False
        assert "discarded" in result2["reason"]


class TestAC4:
    """AC-4: 复验两版结果不一致时保留双 verification_record"""

    def test_dual_verification_record_on_conflict(self):
        card = ChallengeClaimCard()
        old_record = {
            "verification_id": "vr_001",
            "claim_id": "claim_xyz",
            "verdict": "verified",
            "checked_at": "2024-01-01T00:00:00Z",
        }
        new_record = {
            "verification_id": "vr_002",
            "claim_id": "claim_xyz",
            "verdict": "failed",
            "checked_at": "2024-01-15T00:00:00Z",
        }
        result = card.preserve_dual_records(
            old_record=old_record,
            new_record=new_record,
        )
        assert result["preserved_count"] == 2
        assert result["records"][0]["verdict"] == "verified"
        assert result["records"][1]["verdict"] == "failed"
        assert result["conflict"] is True
