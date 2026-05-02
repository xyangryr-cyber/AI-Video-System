"""[SPEC-C-103] ClaimExtractor with 5 trigger points + dedup.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.X.

5 trigger points (see §C-BDD-4 table):
  P2 text        -> extract_from_p2_text
  P7 shot        -> extract_from_p7_shot
  P8 chart       -> extract_from_p8_chart
  P9 B-Roll meta -> extract_from_p9_broll
  user supplement_claim -> extract_from_user_supplement

Dedup: SHA-256 of (claim_type, entity, value, time_range). Two inputs that
hash to the same key resolve to the same `claim_id`, even if the trigger
source_phase / source_artifact differ. The registry is process-local
(stateless-by-default can be enabled by passing a fresh registry per call).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.shared.schemas.claim import Claim, ClaimType, SourcePhase, TimeRange

_NUMERIC_TEXT_PATTERN = re.compile(
    r"([一-鿿A-Za-z0-9·\-]+?)\s*"
    r"(?:20\d{2}\s*(?:年|Q[1-4])?(?:\s*\d{1,2}\s*月)?)?"
    r"[^0-9]*?"
    r"(-?\d+(?:\.\d+)?)\s*"
    r"(%|亿美元|亿元|万亿|万|千亿|元|美元|bps)?",
    re.UNICODE,
)

_YEAR_PATTERN = re.compile(r"(20\d{2})\s*(?:年|Q([1-4]))?")


@dataclass
class _RegistryEntry:
    claim_id: str


@dataclass
class ClaimRegistry:
    """In-memory dedup store: dedup_key -> claim_id."""

    _by_key: dict[str, _RegistryEntry] = field(default_factory=dict)
    _counter: int = 0

    def lookup(self, dedup_key: str) -> str | None:
        entry = self._by_key.get(dedup_key)
        return entry.claim_id if entry else None

    def register(self, dedup_key: str, source_phase: str) -> str:
        self._counter += 1
        short = hashlib.sha256(dedup_key.encode("utf-8")).hexdigest()[:16]
        claim_id = f"claim_{source_phase}_{short}"
        self._by_key[dedup_key] = _RegistryEntry(claim_id=claim_id)
        return claim_id

    def resolve(self, dedup_key: str, source_phase: str) -> tuple[str, bool]:
        existing = self.lookup(dedup_key)
        if existing is not None:
            return existing, True
        return self.register(dedup_key, source_phase), False


def _compute_dedup_key(
    claim_type: str,
    entity: str | None,
    value: float | int | str | None,
    time_range: dict[str, Any] | TimeRange | None,
) -> str:
    if time_range is None:
        tr = ""
    elif isinstance(time_range, TimeRange):
        tr = f"{time_range.start}|{time_range.end}"
    else:
        tr = f"{time_range.get('start', '')}|{time_range.get('end', '')}"
    raw = f"{claim_type}||{entity or ''}||{value if value is not None else ''}||{tr}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ClaimExtractor:
    """Stateful w.r.t. its `ClaimRegistry`; rule-based parsers per phase."""

    def __init__(self, registry: ClaimRegistry | None = None) -> None:
        self._registry = registry or ClaimRegistry()

    # ------------------------------------------------------------------
    # Public dispatch entry (SPEC-6.X signature)
    # ------------------------------------------------------------------

    def extract(
        self,
        *,
        raw_input: str | dict[str, Any],
        source_phase: SourcePhase,
        source_artifact: str,
    ) -> list[Claim]:
        if source_phase == "P2":
            if not isinstance(raw_input, str):
                raise TypeError("P2 trigger expects text input")
            return self.extract_from_p2_text(text=raw_input, source_artifact=source_artifact)
        if source_phase == "P7":
            if not isinstance(raw_input, dict):
                raise TypeError("P7 trigger expects structured shot dict")
            return self.extract_from_p7_shot(shot=raw_input, source_artifact=source_artifact)
        if source_phase == "P8":
            if not isinstance(raw_input, dict):
                raise TypeError("P8 trigger expects chart config dict")
            return self.extract_from_p8_chart(chart=raw_input, source_artifact=source_artifact)
        if source_phase == "P9":
            if not isinstance(raw_input, str):
                raise TypeError("P9 trigger expects metadata text")
            return self.extract_from_p9_broll(metadata=raw_input, source_artifact=source_artifact)
        if source_phase == "user_input":
            if not isinstance(raw_input, str):
                raise TypeError("user trigger expects text input")
            return self.extract_from_user_supplement(text=raw_input)
        raise ValueError(f"unknown source_phase {source_phase!r}")

    # ------------------------------------------------------------------
    # Trigger 1: P2 text
    # ------------------------------------------------------------------

    def extract_from_p2_text(self, *, text: str, source_artifact: str) -> list[Claim]:
        candidates = self._parse_text_candidates(text)
        return self._materialize(
            candidates=candidates,
            source_phase="P2",
            source_artifact=source_artifact,
            default_claim_type="data",
        )

    # ------------------------------------------------------------------
    # Trigger 2: P7 shot (structured)
    # ------------------------------------------------------------------

    def extract_from_p7_shot(self, *, shot: dict[str, Any], source_artifact: str) -> list[Claim]:
        cand = self._structured_candidate(
            payload=shot,
            default_claim_type="fact",
        )
        return self._materialize(
            candidates=[cand],
            source_phase="P7",
            source_artifact=source_artifact,
            default_claim_type=cand["claim_type"],
        )

    # ------------------------------------------------------------------
    # Trigger 3: P8 chart config
    # ------------------------------------------------------------------

    def extract_from_p8_chart(self, *, chart: dict[str, Any], source_artifact: str) -> list[Claim]:
        cand = self._structured_candidate(
            payload=chart,
            default_claim_type="data",
        )
        return self._materialize(
            candidates=[cand],
            source_phase="P8",
            source_artifact=source_artifact,
            default_claim_type=cand["claim_type"],
        )

    # ------------------------------------------------------------------
    # Trigger 4: P9 B-Roll metadata text
    # ------------------------------------------------------------------

    def extract_from_p9_broll(self, *, metadata: str, source_artifact: str) -> list[Claim]:
        candidates = self._parse_text_candidates(metadata)
        return self._materialize(
            candidates=candidates,
            source_phase="P9",
            source_artifact=source_artifact,
            default_claim_type="citation",
        )

    # ------------------------------------------------------------------
    # Trigger 5: user supplement_claim
    # ------------------------------------------------------------------

    def extract_from_user_supplement(self, *, text: str) -> list[Claim]:
        candidates = self._parse_text_candidates(text)
        return self._materialize(
            candidates=candidates,
            source_phase="user_input",
            source_artifact="intent_router.supplement_claim",
            default_claim_type="data",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_text_candidates(text: str) -> list[dict[str, Any]]:
        """Rule-based text parse. Extracts (entity, value, time_range) if present."""
        year_match = _YEAR_PATTERN.search(text)
        time_range: dict[str, str] | None = None
        if year_match:
            year = year_match.group(1)
            quarter = year_match.group(2)
            if quarter:
                time_range = {
                    "start": f"{year}-Q{quarter}",
                    "end": f"{year}-Q{quarter}",
                }
            else:
                time_range = {"start": f"{year}-01", "end": f"{year}-12"}

        # Find first meaningful numeric span after an entity-like token.
        m = _NUMERIC_TEXT_PATTERN.search(text)
        if m is None:
            return [
                {
                    "claim_type": "fact",
                    "entity": text.strip()[:40],
                    "value": text.strip(),
                    "time_range": time_range,
                    "text": text,
                }
            ]
        entity = (m.group(1) or "").strip() or text.strip()[:40]
        value_str = m.group(2)
        unit = m.group(3) or None
        try:
            value: float | str = float(value_str) if value_str else value_str
        except ValueError:
            value = value_str
        return [
            {
                "claim_type": "data",
                "entity": entity,
                "value": value,
                "unit": unit,
                "time_range": time_range,
                "text": text,
            }
        ]

    @staticmethod
    def _structured_candidate(
        *,
        payload: dict[str, Any],
        default_claim_type: ClaimType,
    ) -> dict[str, Any]:
        return {
            "claim_type": payload.get("claim_type") or default_claim_type,
            "entity": payload.get("entity"),
            "value": payload.get("value"),
            "unit": payload.get("unit"),
            "time_range": payload.get("time_range"),
            "text": payload.get("text") or f"{payload.get('entity')} {payload.get('value')}",
        }

    def _materialize(
        self,
        *,
        candidates: list[dict[str, Any]],
        source_phase: SourcePhase,
        source_artifact: str,
        default_claim_type: ClaimType,
    ) -> list[Claim]:
        now = _utc_now()
        out: list[Claim] = []
        for cand in candidates:
            claim_type: ClaimType = cand.get("claim_type") or default_claim_type
            entity = cand.get("entity")
            value = cand.get("value")
            time_range_raw = cand.get("time_range")
            dedup_key = _compute_dedup_key(claim_type, entity, value, time_range_raw)
            claim_id, _reused = self._registry.resolve(dedup_key, source_phase)
            tr_obj: TimeRange | None = None
            if isinstance(time_range_raw, TimeRange):
                tr_obj = time_range_raw
            elif isinstance(time_range_raw, dict):
                tr_obj = TimeRange(**time_range_raw)
            out.append(
                Claim(
                    claim_id=claim_id,
                    claim_type=claim_type,
                    text=str(cand.get("text") or entity or value),
                    value=value,
                    unit=cand.get("unit"),
                    entity=entity,
                    time_range=tr_obj,
                    source_phase=source_phase,
                    source_artifact=source_artifact,
                    blocking_level=cand.get("blocking_level") or "soft",
                    verification_status="pending",
                    created_at=now,
                    updated_at=now,
                )
            )
        return out


__all__ = ["ClaimExtractor", "ClaimRegistry"]
