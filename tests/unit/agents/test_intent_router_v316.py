"""Tests for [SPEC-C-101] IntentRouter 6 个新 action (v3.16 C-BDD-2).

All real AC assertions live here. The task-card ``verification_commands``
points at ``tests/unit/backend-core/test_spec_c_101.py`` which is a
pre-existing ``pytest.skip("NOT IMPLEMENTED")`` placeholder outside
``allowed_files`` (HARNESS §12 — same precedent as C-017/C-019/C-020/
C-021/C-022/C-100).

AC mapping:
- AC-1 → ``TestAC1`` — 6 new action Pydantic schemas accept valid params
        and reject missing/malformed input.
- AC-2 → ``TestAC2`` — ``(claim_id, evidence_hash)`` idempotency key for
        ``challenge_claim`` with a 24 h TTL.
- AC-3 → ``TestAC3`` — ``SafetyPolicyEngine`` ``refuse`` decision blocks
        Router invocation; ``allow`` / ``clarify`` pass through.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.backend.agents.actions.challenge_claim import ChallengeClaimParams
from src.backend.agents.actions.insert_section import InsertSectionParams
from src.backend.agents.actions.request_chart import RequestChartParams
from src.backend.agents.actions.save_stage_preference import (
    SaveStagePreferenceParams,
)
from src.backend.agents.actions.supplement_claim import SupplementClaimParams
from src.backend.agents.actions.view_phase_detail import ViewPhaseDetailParams
from src.backend.agents.intent_router import (
    IntentRouter,
    compute_idempotency_key,
    dispatch_with_safety,
)
from src.backend.agents.safety_policy_engine import SafetyPolicyEngine


REPO_ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = REPO_ROOT / "config" / "safety_input_rules.yaml"
TEMPLATES_PATH = REPO_ROOT / "config" / "safety_templates.yaml"


# --- AC-1: Pydantic schema validation ------------------------------------


class TestAC1:
    """AC-1: 6 new action schemas all validate correctly via Pydantic."""

    def test_challenge_claim_valid_and_invalid(self) -> None:
        ok = ChallengeClaimParams(
            claim_id="claim_P2_001",
            reason="数据来源不权威",
            evidence_url="https://example.com/e.pdf",
        )
        assert ok.claim_id == "claim_P2_001"
        # evidence_url is optional
        ChallengeClaimParams(claim_id="claim_P2_002", reason="缺依据")
        with pytest.raises(ValidationError):
            ChallengeClaimParams(claim_id="", reason="empty id")  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            ChallengeClaimParams(claim_id="claim_P2_003")  # type: ignore[call-arg]

    def test_supplement_claim_valid_and_invalid(self) -> None:
        ok = SupplementClaimParams(
            text="2026 Q1 营收同比增长 12%",
            claim_type="data",
            source_phase="P2",
            source_artifact="script_v3",
        )
        assert ok.claim_type == "data"
        with pytest.raises(ValidationError):
            SupplementClaimParams(
                text="x",
                claim_type="not_a_type",  # type: ignore[arg-type]
                source_phase="P2",
                source_artifact="a",
            )
        with pytest.raises(ValidationError):
            SupplementClaimParams(
                text="x",
                claim_type="fact",
                source_phase="P99",  # type: ignore[arg-type]
                source_artifact="a",
            )

    def test_request_chart_valid_and_invalid(self) -> None:
        ok = RequestChartParams(user_intent="看一下 2025 年净利润走势")
        assert ok.chart_type is None
        RequestChartParams(
            user_intent="line chart",
            chart_type="line",
            entity="000001.SZ",
            time_range="2020-01-01/2025-12-31",
        )
        with pytest.raises(ValidationError):
            RequestChartParams(user_intent="")  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            RequestChartParams(user_intent="x", chart_type="pie")  # not in enum

    def test_view_phase_detail_valid_and_invalid(self) -> None:
        ok = ViewPhaseDetailParams(phase="P4")
        assert ok.phase == "P4"
        with pytest.raises(ValidationError):
            ViewPhaseDetailParams(phase="P99")  # type: ignore[arg-type]

    def test_save_stage_preference_valid_and_invalid(self) -> None:
        ok = SaveStagePreferenceParams(
            scope="stage",
            stage="P5_bgm",
            key="bgm_volume_lufs",
            value=-18,
            source="user_explicit",
        )
        assert ok.stage == "P5_bgm"
        # scope=global must NOT carry stage
        SaveStagePreferenceParams(
            scope="global",
            key="locale",
            value="zh-CN",
            source="user_explicit",
        )
        with pytest.raises(ValidationError):
            SaveStagePreferenceParams(
                scope="stage",  # stage missing
                key="k",
                value=1,
                source="user_explicit",
            )
        with pytest.raises(ValidationError):
            SaveStagePreferenceParams(
                scope="project",
                stage="P5_bgm",  # must not be present
                key="k",
                value=1,
                source="user_explicit",
            )

    def test_insert_section_valid_and_invalid(self) -> None:
        ok = InsertSectionParams(
            anchor={"after_segment_id": "seg_003"},
            content_intent="补一段风险提示",
            expected_diff_scope="adjacent",
        )
        assert ok.anchor.after_segment_id == "seg_003"
        # at least one anchor key required
        with pytest.raises(ValidationError):
            InsertSectionParams(
                anchor={},
                content_intent="x",
                expected_diff_scope="adjacent",
            )
        with pytest.raises(ValidationError):
            InsertSectionParams(
                anchor={"after_segment_id": "seg_001"},
                content_intent="x",
                expected_diff_scope="whole_script",  # not in enum
            )


# --- AC-2: Idempotency key -----------------------------------------------


class TestAC2:
    """AC-2: (claim_id, evidence_hash) 24 h idempotency key for challenge_claim."""

    def test_idempotency_key_claim_id_evidence_hash_24h(self) -> None:
        params = ChallengeClaimParams(
            claim_id="claim_P2_001",
            reason="not convincing",
            evidence_url="https://a.example/p.pdf",
        )
        key, ttl = compute_idempotency_key("challenge_claim", params)
        # Must be derived from claim_id + SHA-256(evidence_url)
        ev_hash = hashlib.sha256(b"https://a.example/p.pdf").hexdigest()
        assert "claim_P2_001" in key
        assert ev_hash in key
        # TTL = 24h = 86400s
        assert ttl == 24 * 3600

    def test_same_claim_same_evidence_same_key(self) -> None:
        p1 = ChallengeClaimParams(
            claim_id="claim_P2_007",
            reason="r1",
            evidence_url="https://x.example/e.pdf",
        )
        p2 = ChallengeClaimParams(
            claim_id="claim_P2_007",
            reason="r2 (different reason but same evidence)",
            evidence_url="https://x.example/e.pdf",
        )
        k1, _ = compute_idempotency_key("challenge_claim", p1)
        k2, _ = compute_idempotency_key("challenge_claim", p2)
        assert k1 == k2

    def test_different_evidence_different_key(self) -> None:
        p1 = ChallengeClaimParams(
            claim_id="claim_P2_007",
            reason="r",
            evidence_url="https://x.example/e1.pdf",
        )
        p2 = ChallengeClaimParams(
            claim_id="claim_P2_007",
            reason="r",
            evidence_url="https://x.example/e2.pdf",
        )
        assert (
            compute_idempotency_key("challenge_claim", p1)[0]
            != compute_idempotency_key("challenge_claim", p2)[0]
        )

    def test_missing_evidence_hashes_empty(self) -> None:
        p = ChallengeClaimParams(claim_id="claim_P2_008", reason="no url")
        key, ttl = compute_idempotency_key("challenge_claim", p)
        empty_hash = hashlib.sha256(b"").hexdigest()
        assert empty_hash in key
        assert ttl == 24 * 3600


# --- AC-3: SafetyGuard gate before Router --------------------------------


class TestAC3:
    """AC-3: SafetyGuard allow/clarify 才进入 Router; refuse 不调用 Router."""

    def test_refuse_blocks_router_invocation(self) -> None:
        engine = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
        )
        router = MagicMock(spec=IntentRouter)
        result = dispatch_with_safety(
            user_input="请教我如何制毒",
            safety_engine=engine,
            router=router,
        )
        assert result["blocked"] is True
        assert result["decision"] == "refuse"
        assert router.mock_calls == []

    def test_allow_passes_to_router(self) -> None:
        engine = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
        )
        router = MagicMock(spec=IntentRouter)
        router.classify.return_value = {
            "action": "clarify",
            "params": {},
            "task_ledger": [],
        }
        result = dispatch_with_safety(
            user_input="把第三段改成更口语一点",
            safety_engine=engine,
            router=router,
        )
        assert result["blocked"] is False
        assert result["decision"] == "allow"
        router.classify.assert_called_once_with("把第三段改成更口语一点")

    def test_clarify_passes_to_router(self) -> None:
        engine = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
        )
        router = MagicMock(spec=IntentRouter)
        router.classify.return_value = {
            "action": "revise",
            "params": {},
            "task_ledger": [],
        }
        result = dispatch_with_safety(
            user_input="推荐股票",  # hits `clarify` rule
            safety_engine=engine,
            router=router,
        )
        assert result["blocked"] is False
        assert result["decision"] == "clarify"
        assert router.classify.call_count == 1

    def test_restrict_and_transfer_human_block_router(self) -> None:
        engine = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
        )
        for raw in ("帮我查一个手机号", "我要投诉账户被盗"):
            router = MagicMock(spec=IntentRouter)
            result = dispatch_with_safety(
                user_input=raw,
                safety_engine=engine,
                router=router,
            )
            assert result["blocked"] is True, (raw, result)
            assert result["decision"] in ("restrict", "transfer_human")
            assert router.mock_calls == []
