"""[SPEC-C-021] MaterialVerifier — L1 programmatic + L2 FactChecker.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-6.

State machine (AC-3, A-015):

    pending -> verified   (L1 file exists + nonzero AND L2 FactChecker PASS)
    pending -> missing    (L1 file missing — no L2 call)
    pending -> rejected   (L1 pass AND L2 FactChecker FAIL)

Every transition is routed through
:func:`validate_verification_status_transition` so an illegal hop
raises before the manifest is touched.

The optional ``fact_checker`` dependency is a duck-typed L2 probe:

    fact_checker.check(entry, path) -> (ok: bool, reason: str)

When omitted the verifier degrades to L1-only (file existence /
non-empty). This lets unit tests exercise the missing-state branch
without supplying a no-op checker.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from src.shared.schemas.material_manifest import (
    MaterialEntry,
    VerificationStatus,
    validate_verification_status_transition,
)


class _FactChecker(Protocol):
    def check(  # pragma: no cover - protocol
        self, entry: MaterialEntry, path: Path
    ) -> tuple[bool, str]: ...


class MaterialVerifier:
    def __init__(
        self,
        *,
        project_root: Path,
        fact_checker: _FactChecker | None = None,
    ) -> None:
        self._root = Path(project_root)
        self._fact_checker = fact_checker

    @property
    def verified_dir(self) -> Path:
        return self._root / "phase_7a" / "verified_materials"

    def verify(self, entry: MaterialEntry) -> MaterialEntry:
        # L1 — file existence + non-empty.
        candidate = self._locate_file(entry.material_id)
        if candidate is None or candidate.stat().st_size == 0:
            return self._transition(entry, VerificationStatus.MISSING)

        # L2 — FactChecker (optional).
        if self._fact_checker is not None:
            ok, _reason = self._fact_checker.check(entry, candidate)
            if not ok:
                return self._transition(entry, VerificationStatus.REJECTED)

        # All layers pass.
        return self._transition(entry, VerificationStatus.VERIFIED)

    def _locate_file(self, material_id: str) -> Path | None:
        """Return the fetched file for ``material_id``, or None."""
        matches = list(self.verified_dir.glob(f"{material_id}.*"))
        if not matches:
            return None
        return matches[0]

    def _transition(
        self, entry: MaterialEntry, new_status: VerificationStatus
    ) -> MaterialEntry:
        validate_verification_status_transition(entry.verification_status, new_status)
        update: dict[str, object] = {"verification_status": new_status}
        if new_status == VerificationStatus.VERIFIED:
            update["verified_at"] = self._now_iso()
        return entry.model_copy(update=update)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


__all__ = ["MaterialVerifier"]
