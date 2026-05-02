"""Shared test implementations for [SPEC-A-100] Claim/VerificationRecord contracts.

Covers AC-1 (Claim pydantic round-trip), AC-2 (VerificationRecord
pydantic round-trip), and AC-5 (TS interface parity with pydantic).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
CLAIM_TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "claim.ts"


def _base_claim_payload() -> Dict[str, Any]:
    return {
        "claim_id": "claim_P2_001",
        "claim_type": "data",
        "text": "Gold price 3421.5 USD",
        "value": "3421.5",
        "unit": "USD",
        "entity": "Gold",
        "time_range": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-02T00:00:00Z",
        },
        "source_phase": "P2",
        "source_artifact": "polished_script.json",
        "source_span": {"start_char": 0, "end_char": 18, "segment_id": "seg_1"},
        "blocking_level": "hard",
        "verification_status": "pending",
        "created_at": "2026-04-20T00:00:00Z",
        "updated_at": "2026-04-20T00:00:00Z",
    }


def _base_verification_payload() -> Dict[str, Any]:
    return {
        "verification_id": "ver_001",
        "claim_id": "claim_P2_001",
        "verifier_type": "fact_check_agent",
        "evidence_refs": [{"url": "https://example.com/a", "snippet": "gold"}],
        "checked_at": "2026-04-20T00:00:00Z",
        "expires_at": "2026-05-20T00:00:00Z",
        "verdict": "verified",
        "reason": "matched source",
        "confidence": 0.95,
    }


def _ts_interface_fields(src: str, name: str) -> set[str]:
    """Return top-level field names of a TS interface with no nested braces."""
    m = re.search(rf"export interface {re.escape(name)}\s*\{{([^{{}}]+)\}}", src)
    assert m, f"{name} interface not found in claim.ts (or contains nested braces)"
    return set(re.findall(r"^\s*(\w+)\??:", m.group(1), flags=re.M))


class TestAC1ClaimPydantic:
    """AC-1: Claim pydantic model — mandatory fields + round-trip."""

    def test_claim_pydantic_rejects_missing_blocking_level(self) -> None:
        from src.shared.schemas.claim import Claim

        payload = _base_claim_payload()
        del payload["blocking_level"]
        with pytest.raises(ValidationError):
            Claim(**payload)

    def test_claim_pydantic_round_trip(self) -> None:
        from src.shared.schemas.claim import Claim

        payload = _base_claim_payload()
        model = Claim(**payload)
        got = json.loads(model.model_dump_json(exclude_none=True))
        assert got == payload


class TestAC2VerificationRecordPydantic:
    """AC-2: VerificationRecord pydantic round-trip."""

    def test_verification_record_pydantic_round_trip(self) -> None:
        from src.shared.schemas.claim import VerificationRecord

        payload = _base_verification_payload()
        model = VerificationRecord(**payload)
        got = json.loads(model.model_dump_json(exclude_none=True))
        assert got == payload


class TestAC5TsInterfaceMatchesPydantic:
    """AC-5: TS interface mirrors pydantic field names exactly."""

    def test_ts_interface_matches_pydantic_fields(self) -> None:
        from src.shared.schemas.claim import Claim, VerificationRecord

        assert CLAIM_TS_PATH.exists(), f"missing TS file: {CLAIM_TS_PATH}"
        src = CLAIM_TS_PATH.read_text(encoding="utf-8")

        ts_claim = _ts_interface_fields(src, "Claim")
        ts_vr = _ts_interface_fields(src, "VerificationRecord")

        py_claim = set(Claim.model_fields.keys())
        py_vr = set(VerificationRecord.model_fields.keys())

        assert ts_claim == py_claim, (
            f"Claim field mismatch — ts-only={ts_claim - py_claim}, "
            f"py-only={py_claim - ts_claim}"
        )
        assert ts_vr == py_vr, (
            f"VerificationRecord field mismatch — ts-only={ts_vr - py_vr}, "
            f"py-only={py_vr - ts_vr}"
        )
