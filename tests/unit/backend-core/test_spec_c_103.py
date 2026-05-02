"""Tests for [SPEC-C-103] ClaimExtractor + VerificationOrchestrator.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 (SPEC-6.X/6.Y).
Task card: tasks/SPEC-C/C-103-claim-extractor-orchestrator.md.

AC mapping (task card -> test function):
AC-1 5 trigger points produce Claims  -> test_five_trigger_points_create_claim
AC-2 dedup key reuses claim_id        -> test_dedup_key_reuses_claim_id
AC-3 polished_script v3->v4 incremental reverify fires verifier
     only on added/removed claims     -> test_incremental_reverify_v3_to_v4
AC-4 user challenge marks downstream
     artifacts 'damaged' within 60s   -> test_user_challenge_marks_downstream_damaged_within_60s
"""

from __future__ import annotations

import time

from src.backend.agents.claim_extractor import ClaimExtractor
from src.backend.services.verification_orchestrator import (
    DownstreamArtifactRef,
    VerificationOrchestrator,
)
from src.shared.schemas.claim import VerificationRecord


# ---------------------------------------------------------------------------
# Helpers — a counting verifier reused by AC-3 / AC-4.
# ---------------------------------------------------------------------------


class _CountingVerifier:
    """Verifier stub that records call count and returns a stock record."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def verify(self, claim) -> VerificationRecord:
        self.calls.append(claim.claim_id)
        return VerificationRecord(
            verification_id=f"ver_{claim.claim_id}",
            claim_id=claim.claim_id,
            verifier_type="fact_check_agent",
            checked_at="2026-04-24T00:00:00Z",
            verdict="verified",
        )


def _make_orch(v: _CountingVerifier) -> VerificationOrchestrator:
    return VerificationOrchestrator(
        financial_data_verifier=v,
        fact_check_verifier=v,
        image_backed_verifier=v,
        citation_verifier=v,
    )


# ---------------------------------------------------------------------------
# AC-1 — ClaimExtractor exposes 5 trigger-point entries.
# ---------------------------------------------------------------------------


def test_five_trigger_points_create_claim() -> None:
    extractor = ClaimExtractor()

    # Trigger 1: P2 文本完成 (ScriptAgent 产物 / 文本)
    p2 = extractor.extract_from_p2_text(
        text="苹果 2025 年营收 3940 亿美元。",
        source_artifact="polished_script.json",
    )
    assert len(p2) >= 1
    assert p2[0].source_phase == "P2"

    # Trigger 2: P7 shot (ShotAgent 新增含事实描述的 shot)
    p7 = extractor.extract_from_p7_shot(
        shot={
            "claim_type": "fact",
            "entity": "Tesla",
            "value": "1.81M",
            "time_range": {"start": "2024-Q1", "end": "2024-Q4"},
            "text": "Tesla 2024 全年交付 1.81M 辆。",
        },
        source_artifact="storyboard.json",
    )
    assert len(p7) >= 1
    assert p7[0].source_phase == "P7"

    # Trigger 3: P8 chart (ChartAgent 产物含数值序列)
    p8 = extractor.extract_from_p8_chart(
        chart={
            "claim_type": "data",
            "entity": "Nasdaq",
            "value": 15000.0,
            "time_range": {"start": "2024-01", "end": "2024-12"},
            "text": "Nasdaq 收盘 15000",
        },
        source_artifact="chart.json",
    )
    assert len(p8) >= 1
    assert p8[0].source_phase == "P8"

    # Trigger 4: P9 B-Roll metadata (BRollAgent 写入含事实说明的元数据)
    p9 = extractor.extract_from_p9_broll(
        metadata="华尔街日报 2025 年 3 月报道: 通胀率 3.1%。",
        source_artifact="broll_meta_s1.json",
    )
    assert len(p9) >= 1
    assert p9[0].source_phase == "P9"

    # Trigger 5: 用户 supplement_claim (IntentRouter → supplement_claim)
    user = extractor.extract_from_user_supplement(
        text="实际 2024 年 GDP 增速是 5.2%。",
    )
    assert len(user) >= 1
    assert user[0].source_phase == "user_input"

    # Universal dispatch entry (SPEC-6.X signature) also works.
    unified = extractor.extract(
        raw_input="英伟达 2025 Q1 营收 260 亿美元",
        source_phase="P2",
        source_artifact="polished_script.json",
    )
    assert len(unified) >= 1


# ---------------------------------------------------------------------------
# AC-2 — Dedup: (claim_type, entity, value, time_range) → same claim_id.
# ---------------------------------------------------------------------------


def test_dedup_key_reuses_claim_id() -> None:
    extractor = ClaimExtractor()
    shot_payload = {
        "claim_type": "data",
        "entity": "AAPL",
        "value": 3940,
        "time_range": {"start": "2025-01", "end": "2025-12"},
        "text": "AAPL 2025 营收 3940",
    }
    chart_payload = {
        "claim_type": "data",
        "entity": "AAPL",
        "value": 3940,
        "time_range": {"start": "2025-01", "end": "2025-12"},
        "text": "AAPL 2025 营收 3940 (chart)",
    }
    first = extractor.extract_from_p7_shot(
        shot=shot_payload,
        source_artifact="storyboard.json",
    )
    second = extractor.extract_from_p8_chart(
        chart=chart_payload,
        source_artifact="chart.json",
    )
    assert first and second
    assert first[0].claim_id == second[0].claim_id, "dedup hit must reuse claim_id"

    # Negative: changing time_range yields a new claim_id.
    chart_diff = dict(chart_payload, time_range={"start": "2024-01", "end": "2024-12"})
    third = extractor.extract_from_p8_chart(
        chart=chart_diff,
        source_artifact="chart_b.json",
    )
    assert third and third[0].claim_id != first[0].claim_id


# ---------------------------------------------------------------------------
# AC-3 — Incremental reverify on polished_script v3 → v4.
# ---------------------------------------------------------------------------


def test_incremental_reverify_v3_to_v4() -> None:
    extractor = ClaimExtractor()

    # v3 claims A (kept), B (kept), C (removed in v4)
    a = extractor.extract_from_p2_text(
        text="事件 A 发生于 2024 Q1",
        source_artifact="polished_script_v3.json",
    )[0]
    b = extractor.extract_from_p2_text(
        text="通胀率 3.1%",
        source_artifact="polished_script_v3.json",
    )[0]
    c = extractor.extract_from_p2_text(
        text="引用 2023 年央行报告",
        source_artifact="polished_script_v3.json",
    )[0]
    v3_claims = [a, b, c]

    # v4 claims: A, B kept; C dropped; D added
    d = extractor.extract_from_p2_text(
        text="新增数据 4.5% 2025 Q1",
        source_artifact="polished_script_v4.json",
    )[0]
    v4_claims = [a, b, d]

    verifier = _CountingVerifier()
    orch = _make_orch(verifier)

    # Baseline run on v3: 3 verifier invocations.
    for claim in v3_claims:
        orch.verify(claim)
    assert len(verifier.calls) == 3

    # Incremental run from v3 → v4: only D should trigger the verifier.
    delta = orch.reverify_incremental(old_claims=v3_claims, new_claims=v4_claims)

    assert len(verifier.calls) == 4, (
        f"only the added claim D should fire the verifier, total calls={verifier.calls}"
    )
    assert verifier.calls[-1] == d.claim_id
    assert delta["new"] == [d.claim_id]
    assert delta["superseded"] == [c.claim_id]
    assert set(delta["unchanged"]) == {a.claim_id, b.claim_id}


# ---------------------------------------------------------------------------
# AC-4 — User challenge marks downstream artifacts 'damaged' within 60s.
# ---------------------------------------------------------------------------


def test_user_challenge_marks_downstream_damaged_within_60s() -> None:
    extractor = ClaimExtractor()
    claims = extractor.extract_from_p2_text(
        text="某公司 2025 年净利润 50 亿美元",
        source_artifact="polished_script.json",
    )
    assert claims
    target = claims[0]

    verifier = _CountingVerifier()
    orch = _make_orch(verifier)
    orch.verify(target)

    downstream = [
        DownstreamArtifactRef(
            artifact_id="storyboard_v2.json",
            claim_ids=[target.claim_id],
        ),
        DownstreamArtifactRef(
            artifact_id="chart_revenue.json",
            claim_ids=[target.claim_id],
        ),
    ]

    start = time.monotonic()
    result = orch.handle_user_challenge(
        claim_id=target.claim_id,
        downstream_artifacts=downstream,
    )
    elapsed = time.monotonic() - start

    assert elapsed < 60.0, f"handle_user_challenge took {elapsed:.3f}s > 60s"
    assert result["claim_status"] == "user_disputed"
    assert result["elapsed_seconds"] < 60.0
    assert {d["artifact_id"] for d in result["downstream"]} == {
        "storyboard_v2.json",
        "chart_revenue.json",
    }
    assert all(d["status"] == "damaged" for d in result["downstream"])

    # Verifier must have been re-run on the challenged claim.
    assert verifier.calls.count(target.claim_id) >= 2
