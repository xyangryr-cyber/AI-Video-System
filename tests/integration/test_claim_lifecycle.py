"""[SPEC-C-103] End-to-end claim lifecycle integration test.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 (SPEC-6.X/6.Y).

Exercises the full claim pipeline against real ClaimExtractor +
VerificationOrchestrator (not stubs):
- extraction from 5 trigger points into a single shared ClaimRegistry,
- routing by claim_type to the matching concrete verifier,
- polished_script v3 -> v4 incremental reverify,
- user challenge -> user_disputed + downstream 'damaged' within 60s.
"""

from __future__ import annotations

import time

from src.backend.agents.claim_extractor import ClaimExtractor, ClaimRegistry
from src.backend.services.verification_orchestrator import (
    DownstreamArtifactRef,
    VerificationOrchestrator,
)
from src.backend.services.verifiers.citation_verifier import CitationVerifier
from src.backend.services.verifiers.fact_check_verifier import FactCheckVerifier
from src.backend.services.verifiers.financial_data_verifier import (
    FinancialDataVerifier,
)
from src.backend.services.verifiers.image_backed_verifier import ImageBackedVerifier


def _orch() -> VerificationOrchestrator:
    return VerificationOrchestrator(
        financial_data_verifier=FinancialDataVerifier(),
        fact_check_verifier=FactCheckVerifier(),
        image_backed_verifier=ImageBackedVerifier(),
        citation_verifier=CitationVerifier(),
    )


def test_lifecycle_extract_route_and_verify_all_trigger_points() -> None:
    """All 5 trigger points produce verified records via real verifiers."""
    registry = ClaimRegistry()
    extractor = ClaimExtractor(registry=registry)
    orch = _orch()

    batches = [
        extractor.extract_from_p2_text(
            text="苹果 2025 Q1 营收 950 亿美元",
            source_artifact="polished_script_v1.json",
        ),
        extractor.extract_from_p7_shot(
            shot={
                "claim_type": "fact",
                "entity": "Tesla",
                "value": "1.81M",
                "time_range": {"start": "2024-Q1", "end": "2024-Q4"},
                "text": "Tesla 2024 全年交付 1.81M 辆",
            },
            source_artifact="storyboard_v1.json",
        ),
        extractor.extract_from_p8_chart(
            chart={
                "claim_type": "data",
                "entity": "Nasdaq",
                "value": 15000.0,
                "time_range": {"start": "2024-01", "end": "2024-12"},
                "text": "Nasdaq 2024 平均 15000",
            },
            source_artifact="chart_v1.json",
        ),
        extractor.extract_from_p9_broll(
            metadata="华尔街日报 2025 年 3 月报道",
            source_artifact="broll_meta_s1.json",
        ),
        extractor.extract_from_user_supplement(
            text="实际 2024 年 GDP 增速是 5.2%",
        ),
    ]

    records = []
    for batch in batches:
        assert batch, "extractor must produce at least one claim per trigger"
        for claim in batch:
            records.append(orch.verify(claim))

    assert len(records) == len(batches)
    assert all(r.verdict == "verified" for r in records)
    assert {r.verifier_type for r in records}.issubset(
        {"financial_data_service", "fact_check_agent", "web_search"}
    )


def test_lifecycle_dedup_then_incremental_reverify_then_challenge() -> None:
    """v3 → v4 incremental reverify, then user challenge flips downstream to damaged."""
    registry = ClaimRegistry()
    extractor = ClaimExtractor(registry=registry)
    orch = _orch()

    # v3 polished_script: 3 claims
    a = extractor.extract_from_p2_text(
        text="2024 Q1 通胀 3.1%",
        source_artifact="polished_script_v3.json",
    )[0]
    b = extractor.extract_from_p2_text(
        text="2024 Q2 失业率 4.0%",
        source_artifact="polished_script_v3.json",
    )[0]
    c = extractor.extract_from_p2_text(
        text="2023 央行报告",
        source_artifact="polished_script_v3.json",
    )[0]
    for claim in (a, b, c):
        orch.verify(claim)
    assert orch.claim_status(a.claim_id) == "verified"
    assert orch.claim_status(c.claim_id) == "verified"

    # Dedup: re-extracting the same logical data claim reuses claim_id.
    a_again = extractor.extract_from_p2_text(
        text="2024 Q1 通胀 3.1%",
        source_artifact="polished_script_v3.json",
    )[0]
    assert a_again.claim_id == a.claim_id

    # v4: drop C, add D (new)
    d = extractor.extract_from_p2_text(
        text="2025 Q1 新数据 4.5%",
        source_artifact="polished_script_v4.json",
    )[0]
    delta = orch.reverify_incremental(
        old_claims=[a, b, c],
        new_claims=[a, b, d],
    )
    assert delta["new"] == [d.claim_id]
    assert delta["superseded"] == [c.claim_id]
    assert orch.claim_status(c.claim_id) == "superseded"
    assert orch.claim_status(d.claim_id) == "verified"

    # User challenges claim A; downstream artifacts referencing it → damaged in < 60s.
    downstream = [
        DownstreamArtifactRef(
            artifact_id="storyboard_v4.json",
            claim_ids=[a.claim_id],
        ),
        DownstreamArtifactRef(
            artifact_id="chart_inflation.json",
            claim_ids=[a.claim_id, b.claim_id],
        ),
        DownstreamArtifactRef(
            artifact_id="unrelated_shot.json",
            claim_ids=["claim_user_input_unrelated"],
        ),
    ]
    started = time.monotonic()
    result = orch.handle_user_challenge(
        claim_id=a.claim_id,
        downstream_artifacts=downstream,
    )
    elapsed = time.monotonic() - started

    assert elapsed < 60.0
    assert result["claim_status"] == "user_disputed"
    damaged = {d["artifact_id"]: d["status"] for d in result["downstream"]}
    assert damaged["storyboard_v4.json"] == "damaged"
    assert damaged["chart_inflation.json"] == "damaged"
    assert damaged["unrelated_shot.json"] == "unaffected"
