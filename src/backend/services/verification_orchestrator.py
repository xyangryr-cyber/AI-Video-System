"""[SPEC-C-103] VerificationOrchestrator — routing + incremental reverify + user challenge.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.Y.

Responsibilities:
1. Route Claim -> right verifier by `claim_type` (SPEC-6.Y route table).
2. Incremental reverify: given (old_claims, new_claims) by claim_id set,
   only invoke verifier on newly-added claims; mark deleted claims
   `superseded`; reuse records for unchanged claims.
3. User challenge: mark challenged claim `user_disputed`, re-run verifier,
   flip downstream artifacts referencing the claim to `status='damaged'`
   synchronously (well within the SPEC 60-second visibility budget).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

from src.shared.schemas.claim import Claim, ClaimType, VerificationRecord


class _Verifier(Protocol):
    """Duck-typed verifier: `.verify(claim) -> VerificationRecord`."""

    def verify(self, claim: Claim) -> VerificationRecord: ...


@dataclass(frozen=True)
class DownstreamArtifactRef:
    """Downstream artifact that references a set of `claim_ids`.

    When any referenced claim transitions to `user_disputed`, the artifact
    status flips to `damaged` until the claim is re-verified.
    """

    artifact_id: str
    claim_ids: list[str]


class VerificationOrchestrator:
    """Routes claims to verifiers and tracks verification records + challenges."""

    def __init__(
        self,
        *,
        financial_data_verifier: _Verifier,
        fact_check_verifier: _Verifier,
        image_backed_verifier: _Verifier,
        citation_verifier: _Verifier,
    ) -> None:
        self._route: dict[ClaimType, _Verifier] = {
            "data": financial_data_verifier,
            "fact": fact_check_verifier,
            "event": fact_check_verifier,
            "image_backed": image_backed_verifier,
            "citation": citation_verifier,
        }
        self._records: dict[str, VerificationRecord] = {}
        self._claim_status: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Primary verify
    # ------------------------------------------------------------------

    def verify(self, claim: Claim) -> VerificationRecord:
        verifier = self._route.get(claim.claim_type)
        if verifier is None:
            raise ValueError(f"no verifier for claim_type {claim.claim_type!r}")
        record = verifier.verify(claim)
        self._records[claim.claim_id] = record
        self._claim_status[claim.claim_id] = (
            "verified" if record.verdict == "verified" else "failed"
        )
        return record

    # ------------------------------------------------------------------
    # Incremental reverify (polished_script v3 -> v4)
    # ------------------------------------------------------------------

    def reverify_incremental(
        self,
        *,
        old_claims: list[Claim],
        new_claims: list[Claim],
    ) -> dict[str, list[str]]:
        old_by_id: dict[str, Claim] = {c.claim_id: c for c in old_claims}
        new_by_id: dict[str, Claim] = {c.claim_id: c for c in new_claims}

        added_ids = [cid for cid in new_by_id if cid not in old_by_id]
        removed_ids = [cid for cid in old_by_id if cid not in new_by_id]
        unchanged_ids = [cid for cid in new_by_id if cid in old_by_id]

        for cid in added_ids:
            self.verify(new_by_id[cid])

        for cid in removed_ids:
            self._claim_status[cid] = "superseded"

        return {
            "new": added_ids,
            "superseded": removed_ids,
            "unchanged": unchanged_ids,
        }

    # ------------------------------------------------------------------
    # User challenge (mark downstream 'damaged' synchronously)
    # ------------------------------------------------------------------

    def handle_user_challenge(
        self,
        *,
        claim_id: str,
        downstream_artifacts: list[DownstreamArtifactRef],
    ) -> dict[str, Any]:
        start = time.monotonic()
        self._claim_status[claim_id] = "user_disputed"

        existing_record = self._records.get(claim_id)
        claim_type: ClaimType = "fact"
        if existing_record is not None:
            mapping = {
                "financial_data_service": "data",
                "fact_check_agent": "fact",
                "web_search": "citation",
                "user_override": "fact",
            }
            claim_type = mapping.get(existing_record.verifier_type, "fact")  # type: ignore[assignment]

        verifier = self._route.get(claim_type)
        if verifier is not None:
            stub_claim = Claim(
                claim_id=claim_id,
                claim_type=claim_type,
                text="<user_disputed>",
                source_phase="user_input",
                source_artifact="challenge_claim",
                blocking_level="hard",
                verification_status="user_disputed",
                created_at=existing_record.checked_at
                if existing_record
                else "1970-01-01T00:00:00Z",
                updated_at=existing_record.checked_at
                if existing_record
                else "1970-01-01T00:00:00Z",
            )
            new_record = verifier.verify(stub_claim)
            self._records[claim_id] = new_record

        damaged: list[dict[str, str]] = []
        for art in downstream_artifacts:
            if claim_id in art.claim_ids:
                damaged.append({"artifact_id": art.artifact_id, "status": "damaged"})
            else:
                damaged.append({"artifact_id": art.artifact_id, "status": "unaffected"})

        elapsed = time.monotonic() - start
        return {
            "claim_id": claim_id,
            "claim_status": "user_disputed",
            "downstream": damaged,
            "elapsed_seconds": elapsed,
        }

    # ------------------------------------------------------------------
    # Introspection (used by tests + observability)
    # ------------------------------------------------------------------

    def claim_status(self, claim_id: str) -> str:
        return self._claim_status.get(claim_id, "pending")

    def verification_record(self, claim_id: str) -> VerificationRecord | None:
        return self._records.get(claim_id)


__all__ = ["DownstreamArtifactRef", "VerificationOrchestrator"]
