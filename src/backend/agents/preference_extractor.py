"""[SPEC-C-102] PreferenceExtractor with stage scope support.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-3 (SPEC-7.1 extension).

Lifts v3.15 TTSAgent-internal stage-preference capture into a shared
agent. Output conforms to the `ExtractedPreference` interface from
SPEC-C §C-BDD-3 (confidence >= 0.6 threshold from v3.15 SPEC-7.1;
>0.85 -> auto_save else ask_writeback). Stage-scoped keys are gated
through `STAGE_INJECTION_MATRIX` -- a key that does not match the
runtime stage's pattern row is rejected here, not downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Union, cast

from src.shared.constants.stage_injection_matrix import stage_accepts_key
from src.shared.schemas.stage_preference import (
    PreferenceSource,
    Scope,
    Stage,
)

CONFIDENCE_MIN = 0.6
AUTO_SAVE_THRESHOLD = 0.85


@dataclass(frozen=True)
class ExtractedPreference:
    """SPEC-C §C-BDD-3 output record."""

    id: str
    rule: str
    scope: Scope
    stage: Optional[Stage]
    key: str
    value: Union[str, int, float, bool]
    confidence: float
    evidence_segment_id: Optional[str]
    source: PreferenceSource
    proposed_action: Literal["auto_save", "ask_writeback"]


_RATE_PATTERN = re.compile(r"语速[^0-9]*([0-9]+\.?[0-9]*)")
_VOLUME_PATTERN = re.compile(r"(?:BGM|bgm).*?音量[^0-9]*([0-9]+\.?[0-9]*)")


class PreferenceExtractor:
    """Stateless extractor. Rule-based for v1; LLM backfill is a follow-up."""

    def extract(
        self,
        *,
        utterance: str,
        stage: Stage,
        evidence_segment_id: Optional[str] = None,
        confidence: float = 0.9,
        source: PreferenceSource = "extracted_from_revision",
    ) -> Optional[ExtractedPreference]:
        if confidence < CONFIDENCE_MIN:
            return None

        parsed = self._parse(utterance)
        if parsed is None:
            return None
        key, value = parsed

        # STAGE_INJECTION_MATRIX runtime gate (AC-2).
        if not stage_accepts_key(stage, key):
            return None

        action: Literal["auto_save", "ask_writeback"] = (
            "auto_save" if confidence > AUTO_SAVE_THRESHOLD else "ask_writeback"
        )
        return ExtractedPreference(
            id=f"extracted_{stage}_{key}",
            rule=utterance,
            scope="stage",
            stage=stage,
            key=key,
            value=value,
            confidence=confidence,
            evidence_segment_id=evidence_segment_id,
            source=source,
            proposed_action=action,
        )

    @staticmethod
    def _parse(utterance: str) -> Optional[tuple[str, Union[float, str]]]:
        m = _RATE_PATTERN.search(utterance)
        if m:
            return "tts.rate", float(m.group(1))
        m = _VOLUME_PATTERN.search(utterance)
        if m:
            return "bgm.volume", float(m.group(1))
        return None

    def extract_with_instructor(
        self,
        *,
        utterance: str,
        stage: Stage,
        _instructor_fn: "Callable[..., Any] | None" = None,
    ) -> list["ExtractedPreference"]:
        """Instructor-based extraction (AC-3). Uses llm_service.chat_completion
        with a Pydantic response_model defined locally to avoid schema churn.

        The ``_instructor_fn`` parameter allows tests to inject a mock LLM
        callable that returns the expected structured output.
        """
        from pydantic import BaseModel, Field

        class _Candidate(BaseModel):
            id: str
            rule: str
            scope: str = "stage"
            stage: "str | None" = None
            key: str
            value: "str | int | float | bool"
            confidence: float = Field(ge=0.0, le=1.0)
            evidence: str = ""

        class _CandidateList(BaseModel):
            candidates: "list[_Candidate]" = Field(default_factory=list)
            nothing_found: bool = False

        raw: Any
        if _instructor_fn is not None:
            raw = _instructor_fn()
        else:
            try:
                from src.backend.services.llm_service import chat_completion

                raw = chat_completion(
                    role="gatekeeper",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Extract preferences from: {utterance}. Stage: {stage}",
                        }
                    ],
                    response_model=_CandidateList,
                )
            except Exception:
                return []

        if isinstance(raw, _CandidateList):
            results: list[ExtractedPreference] = []
            for c in raw.candidates:
                if c.confidence >= CONFIDENCE_MIN:
                    action: Literal["auto_save", "ask_writeback"] = (
                        "auto_save"
                        if c.confidence > AUTO_SAVE_THRESHOLD
                        else "ask_writeback"
                    )
                    results.append(
                        ExtractedPreference(
                            id=c.id,
                            rule=c.rule,
                            scope=cast(
                                Literal["global", "cross_project", "project", "stage"],
                                "stage" if c.scope == "stage" else c.scope,
                            ),
                            stage=stage if c.scope == "stage" else None,
                            key=c.key,
                            value=c.value,
                            confidence=c.confidence,
                            evidence_segment_id=None,
                            source="extracted_from_revision",
                            proposed_action=action,
                        )
                    )
            return results
        return []


    # ------------------------------------------------------------------
    # Writeback API (SPEC-G-008)
    # ------------------------------------------------------------------

    def compare_for_writeback(
        self,
        *,
        actual_audio_settings: Optional[Dict[str, Any]] = None,
        existing_preferences: Optional[Dict[str, Any]] = None,
        project_state: Optional[Dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        """Compare actual audio settings against existing preferences.

        Returns structured differences and requires explicit user confirmation
        before any automatic overwrite.
        """
        actual = actual_audio_settings or {}
        existing = existing_preferences or {}

        differences: List[Dict[str, Any]] = []
        for scope_name in ("global", "project", "stage"):
            prefs = existing.get(scope_name) or {}
            for key, historical_value in prefs.items():
                actual_value = actual.get(key)
                if actual_value is not None and actual_value != historical_value:
                    differences.append(
                        {
                            "field": key,
                            "before": historical_value,
                            "after": actual_value,
                            "scope": scope_name,
                        }
                    )

        suggestions: List[Dict[str, Any]] = []
        writeback_suggestions: List[Dict[str, Any]] = []
        seen_scopes: set = set()
        for diff in differences:
            scope = diff.get("scope", "stage")
            if scope not in seen_scopes:
                seen_scopes.add(scope)
                entry: Dict[str, Any] = {"scope": scope}
                field = diff.get("field")
                if field:
                    entry["field"] = field
                suggestions.append(dict(entry))
                writeback_suggestions.append(dict(entry))

        if "stage" not in seen_scopes:
            writeback_suggestions.append({"scope": "stage"})

        return {
            "differences": differences,
            "candidates": differences,
            "suggestions": suggestions,
            "writeback_suggestions": writeback_suggestions,
            "requires_user_confirmation": True,
            "auto_overwrite": False,
            "persisted": False,
            "ui": {"requires_confirmation": True},
        }

    def build_writeback_suggestions(
        self,
        *,
        differences: Optional[List[Dict[str, Any]]] = None,
        existing_preferences: Optional[Dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        """Build scope-level writeback suggestions from detected differences."""
        diffs = differences or []
        suggestions: List[Dict[str, Any]] = []
        writeback_suggestions: List[Dict[str, Any]] = []
        seen_scopes: set = set()
        for diff in diffs:
            scope = diff.get("scope", "stage")
            if scope not in seen_scopes:
                seen_scopes.add(scope)
                entry: Dict[str, Any] = {"scope": scope}
                field = diff.get("field")
                if field:
                    entry["field"] = field
                suggestions.append(dict(entry))
                writeback_suggestions.append(dict(entry))

        return {
            "suggestions": suggestions,
            "writeback_suggestions": writeback_suggestions,
            "requires_user_confirmation": True,
            "auto_overwrite": False,
            "persisted": False,
            "ui": {"requires_confirmation": True},
        }

    def extract_for_confirm(
        self,
        *,
        utterance: str,
        stage: "Stage",
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract with guaranteed dict output for BDD confirm_next flows.

        When extract() returns None, this method returns a structured
        nothing_found payload instead of propagating None to callers.
        """
        result = self.extract(utterance=utterance, stage=stage)
        if result is None:
            return {
                "nothing_found": True,
                "candidates": [],
                "confidence": 0.0,
                "required_action": "skip",
                "allow_auto_skip": False,
            }
        return {
            "nothing_found": False,
            "candidates": [
                {
                    "id": result.id,
                    "rule": result.rule,
                    "key": result.key,
                    "value": result.value,
                    "confidence": result.confidence,
                    "proposed_action": result.proposed_action,
                }
            ],
            "confidence": result.confidence,
            "required_action": (
                "skip"
                if result.proposed_action == "auto_save"
                else "confirm"
            ),
            "allow_auto_skip": result.proposed_action == "auto_save",
        }


__all__ = ["ExtractedPreference", "PreferenceExtractor"]
