"""Tests for [SPEC-C-102] PreferenceExtractor stage scope + writeback API.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-3 (SPEC-7.1 extension).
Task card: tasks/SPEC-C/C-102-preference-extractor-writeback.md.

AC mapping (task card -> test function):
AC-1 writeback-suggestions returns keep/update/add_stage_override
     -> test_writeback_suggestions_returns_three_categories
AC-2 STAGE_INJECTION_MATRIX runtime filter drops out-of-matrix keys
     -> test_stage_injection_matrix_runtime_filter
AC-3 TTSAgent-style call routes through unified PreferenceExtractor with v3.15 parity
     -> test_tts_agent_unified_interface_v315_parity
AC-4 stage pref for stage X must not pollute stage Y resolution
     -> test_stage_preference_does_not_pollute_other_stages
"""

from __future__ import annotations

from src.backend.agents.preference_extractor import (
    ExtractedPreference,
    PreferenceExtractor,
)
from src.backend.services.stage_preference_service import (
    StagePreferenceService,
)
from src.shared.schemas.stage_preference import StagePreference


# --------------------------------------------------------------------------
# AC-1 — writeback-suggestions returns keep/update/add_stage_override
# --------------------------------------------------------------------------


def test_writeback_suggestions_returns_three_categories() -> None:
    """All three recommended_action buckets must appear for a mixed input."""
    service = StagePreferenceService()

    historical = [
        StagePreference(
            preference_id="pref_keep",
            scope="stage",
            stage="P4_tts",
            key="tts.rate",
            value=1.0,
            source="user_explicit",
            created_at="2026-04-24T00:00:00Z",
        ),
        StagePreference(
            preference_id="pref_update",
            scope="stage",
            stage="P4_tts",
            key="tts.voice",
            value="alice",
            source="user_explicit",
            created_at="2026-04-24T00:00:00Z",
        ),
    ]

    current_settings = {
        "tts.rate": 1.0,
        "tts.voice": "bob",
        "tts.pitch": 0.9,
    }

    suggestions = service.generate_writeback_suggestions(
        project_id="proj_1",
        phase="P4_tts",
        current_settings=current_settings,
        historical_preferences=historical,
    )

    actions = {s.key: s.recommended_action for s in suggestions}
    assert actions["tts.rate"] == "keep"
    assert actions["tts.voice"] == "update"
    assert actions["tts.pitch"] == "add_stage_override"
    keep = next(s for s in suggestions if s.key == "tts.rate")
    assert keep.current == 1.0 and keep.historical == 1.0
    update = next(s for s in suggestions if s.key == "tts.voice")
    assert update.current == "bob" and update.historical == "alice"
    add = next(s for s in suggestions if s.key == "tts.pitch")
    assert add.current == 0.9 and add.historical is None


# --------------------------------------------------------------------------
# AC-2 — STAGE_INJECTION_MATRIX runtime filter
# --------------------------------------------------------------------------


def test_stage_injection_matrix_runtime_filter() -> None:
    """Extracting a stage-scoped pref whose key isn't in that stage's matrix
    row MUST be rejected. Keys whose prefix matches are accepted."""
    extractor = PreferenceExtractor()

    ok = extractor.extract(
        utterance="把语速调到 1.2",
        stage="P4_tts",
        evidence_segment_id="seg_1",
    )
    assert ok is not None
    assert ok.scope == "stage"
    assert ok.stage == "P4_tts"
    assert ok.key.startswith("tts.")

    bad = extractor.extract(
        utterance="把 BGM 音量调到 0.4",
        stage="P4_tts",
        evidence_segment_id="seg_2",
    )
    assert bad is None, (
        "bgm.* key must be rejected under P4_tts by STAGE_INJECTION_MATRIX"
    )


# --------------------------------------------------------------------------
# AC-3 — TTSAgent-style unified interface with v3.15 parity
# --------------------------------------------------------------------------


def test_tts_agent_unified_interface_v315_parity() -> None:
    """v3.15 TTSAgent captured stage preferences internally; v3.16 routes the
    same call through PreferenceExtractor. Output semantic MUST match:
    same key namespace, same stage, same evidence, same proposed_action
    policy (>0.85 auto_save else ask_writeback)."""
    extractor = PreferenceExtractor()

    high_conf = extractor.extract(
        utterance="把语速调到 1.2",
        stage="P4_tts",
        evidence_segment_id="rev_42",
        confidence=0.92,
    )
    assert high_conf is not None
    assert isinstance(high_conf, ExtractedPreference)
    assert high_conf.scope == "stage"
    assert high_conf.stage == "P4_tts"
    assert high_conf.key == "tts.rate"
    assert high_conf.value == 1.2
    assert high_conf.evidence_segment_id == "rev_42"
    assert high_conf.confidence == 0.92
    assert high_conf.proposed_action == "auto_save"

    low_conf = extractor.extract(
        utterance="把语速调到 1.2",
        stage="P4_tts",
        evidence_segment_id="rev_43",
        confidence=0.70,
    )
    assert low_conf is not None
    assert low_conf.proposed_action == "ask_writeback"

    below = extractor.extract(
        utterance="把语速调到 1.2",
        stage="P4_tts",
        evidence_segment_id="rev_44",
        confidence=0.55,
    )
    assert below is None


# --------------------------------------------------------------------------
# AC-4 — stage preference does not pollute other stages
# --------------------------------------------------------------------------


def test_stage_preference_does_not_pollute_other_stages() -> None:
    """A stage=P5_bgm preference MUST NOT be injected into P4_tts resolution.
    The runtime injection pass MUST only surface preferences whose
    scope/stage pair is compatible with the runtime stage under
    STAGE_INJECTION_MATRIX."""
    service = StagePreferenceService()

    p5_pref = StagePreference(
        preference_id="pref_p5",
        scope="stage",
        stage="P5_bgm",
        key="bgm.tempo",
        value=120,
        source="user_explicit",
        created_at="2026-04-24T00:00:00Z",
    )
    p4_pref = StagePreference(
        preference_id="pref_p4",
        scope="stage",
        stage="P4_tts",
        key="tts.rate",
        value=1.1,
        source="user_explicit",
        created_at="2026-04-24T00:00:00Z",
    )

    injected_p4 = service.inject_preferences(
        stage="P4_tts",
        available=[p5_pref, p4_pref],
    )
    keys = [p.key for p in injected_p4]
    assert "tts.rate" in keys, "legal P4 pref must be injected"
    assert "bgm.tempo" not in keys, (
        "P5 pref must NOT leak into P4 injection (STAGE_INJECTION_MATRIX)"
    )

    injected_p5 = service.inject_preferences(
        stage="P5_bgm",
        available=[p5_pref, p4_pref],
    )
    keys5 = [p.key for p in injected_p5]
    assert "bgm.tempo" in keys5
    assert "tts.rate" not in keys5
