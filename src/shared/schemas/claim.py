"""Pydantic models for [SPEC-A-100] Claim / VerificationRecord.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-1 (SPEC-0A.8).

`Claim` is the cross-phase (P2/P7/P8/P9) first-class record for a
verifiable fact / data point / event / citation / image assertion. Each
claim can accrue many `VerificationRecord`s over its lifecycle.

Legacy compatibility: v3.15 `key_data_point.data_point_id` ("dp_*") is
accepted as a legal `claim_id` so P2 output can lift existing
data-point IDs into the claims table without a rewrite.

Mirrors `src/shared/types/claim.ts` and the SQL DDL in
`migrations/V002__create_claim_tables.sql`.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

ClaimType = Literal["fact", "data", "event", "citation", "image_backed"]
SourcePhase = Literal["P2", "P7", "P8", "P9", "user_input"]
BlockingLevel = Literal["hard", "soft", "none"]
VerificationStatus = Literal[
    "pending",
    "verifying",
    "verified",
    "failed",
    "stale",
    "superseded",
    "user_disputed",
]
VerifierType = Literal[
    "fact_check_agent",
    "financial_data_service",
    "web_search",
    "user_override",
]
Verdict = Literal["verified", "failed", "inconclusive"]

# Pattern accepts canonical `claim_{phase}_{seq}` and legacy `dp_*` IDs
# (v3.15 key_data_point.data_point_id carry-over per SPEC-A §A-BDD-1).
CLAIM_ID_PATTERN = r"^(?:claim_[A-Za-z0-9_]+|dp_[A-Za-z0-9_-]+)$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimeRange(_Strict):
    start: str = Field(min_length=1)
    end: str = Field(min_length=1)


class SourceSpan(_Strict):
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    segment_id: Optional[str] = None


class EvidenceRef(_Strict):
    url: Optional[str] = None
    doc_path: Optional[str] = None
    snippet: Optional[str] = None


class Claim(_Strict):
    claim_id: str = Field(pattern=CLAIM_ID_PATTERN)
    claim_type: ClaimType
    text: str = Field(min_length=1)
    value: Optional[Union[float, int, str]] = None
    unit: Optional[str] = None
    entity: Optional[str] = None
    time_range: Optional[TimeRange] = None
    source_phase: SourcePhase
    source_artifact: str = Field(min_length=1)
    source_span: Optional[SourceSpan] = None
    blocking_level: BlockingLevel
    verification_status: VerificationStatus
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class VerificationRecord(_Strict):
    verification_id: str = Field(min_length=1)
    claim_id: str = Field(pattern=CLAIM_ID_PATTERN)
    verifier_type: VerifierType
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    checked_at: str = Field(min_length=1)
    expires_at: Optional[str] = None
    verdict: Verdict
    reason: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


__all__ = [
    "BlockingLevel",
    "CLAIM_ID_PATTERN",
    "Claim",
    "ClaimType",
    "EvidenceRef",
    "SourcePhase",
    "SourceSpan",
    "TimeRange",
    "Verdict",
    "VerificationRecord",
    "VerificationStatus",
    "VerifierType",
]
