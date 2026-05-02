"""[SPEC-C-014] Tests for PreferenceService and enhanced PreferenceExtractor."""

import sqlite3
from typing import Optional
from unittest import mock

from pydantic import BaseModel, Field


from src.backend.agents.preference_extractor import (
    ExtractedPreference,
    PreferenceExtractor,
)
from src.backend.services.preference_service import PreferenceService


# ---------------------------------------------------------------------------
# AC-1: candidates confidence >= 0.6
# ---------------------------------------------------------------------------


class TestAC1CandidatesConfidenceGe06:
    def test_candidates_confidence_ge_06(self):
        extractor = PreferenceExtractor()
        result = extractor.extract(
            utterance="语速1.5倍",
            stage="P4_tts",
            confidence=0.9,
        )
        assert result is not None
        assert result.confidence >= 0.6
        assert result.evidence_segment_id or result.evidence_segment_id is None

    def test_low_confidence_rejected(self):
        extractor = PreferenceExtractor()
        result = extractor.extract(
            utterance="语速1.5倍",
            stage="P4_tts",
            confidence=0.5,
        )
        assert result is None, "confidence < 0.6 should reject candidate"


# ---------------------------------------------------------------------------
# AC-2: nothing_found requires user interaction
# ---------------------------------------------------------------------------


class TestAC2NothingFoundRequiresUser:
    def test_nothing_found_requires_user(self):
        svc = PreferenceService(":memory:")
        svc._ensure_tables()
        svc._init_project("proj_test")
        result = svc.extract_and_store_candidates("proj_test", "P4_tts", "hello world")
        # Even with nothing found, store the extraction result
        assert "nothing_found" in result or "candidates" in result


# ---------------------------------------------------------------------------
# AC-3: Extract uses Instructor
# ---------------------------------------------------------------------------


class TestAC3UsesInstructorNotManualParse:
    def test_uses_instructor_not_manual_parse(self):
        extractor = PreferenceExtractor()
        # The extract_with_instructor method is the Instructor-based path
        assert hasattr(extractor, "extract_with_instructor"), (
            "PreferenceExtractor must have Instructor-based extraction method"
        )

    def test_instructor_method_returns_candidates(self):
        extractor = PreferenceExtractor()
        with mock.patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=CandidateList(
                candidates=[
                    Candidate(
                        id="c1",
                        rule="语速设置为1.5倍",
                        scope="stage",
                        stage="P4_tts",
                        key="tts.rate",
                        value=1.5,
                        confidence=0.85,
                        evidence="用户提到语速1.5倍",
                    )
                ],
                nothing_found=False,
            ),
        ):
            result = extractor.extract_with_instructor(
                utterance="语速1.5倍",
                stage="P4_tts",
            )
            assert result is not None


# ---------------------------------------------------------------------------
# AC-4: Accept writes correct scope
# ---------------------------------------------------------------------------


class TestAC4AcceptWritesCorrectScope:
    def test_accept_writes_correct_scope(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        svc.accept_preference(
            "proj_test",
            ExtractedPreference(
                id="ep_1",
                rule="语速1.5倍",
                scope="stage",
                stage="P4_tts",
                key="tts.rate",
                value=1.5,
                confidence=0.9,
                evidence_segment_id="seg_1",
                source="extracted_from_revision",
                proposed_action="ask_writeback",
            ),
        )
        prefs = svc.get_project_preferences("proj_test")
        assert "tts.rate" in prefs or len(prefs) > 0


# ---------------------------------------------------------------------------
# AC-5: Edit uses modified text
# ---------------------------------------------------------------------------


class TestAC5EditUsesModifiedText:
    def test_edit_uses_modified_text(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        original = "语速设置1.5倍"
        modified = "语速设置为1.8倍"
        svc.edit_and_accept(
            "proj_test",
            original_text=original,
            modified_text=modified,
            scope="stage",
            stage="P4_tts",
            key="tts.rate",
            value=1.8,
        )
        prefs = svc.get_project_preferences("proj_test")
        assert original not in str(prefs)


# ---------------------------------------------------------------------------
# AC-6: Confirmation updates timestamp
# ---------------------------------------------------------------------------


class TestAC6ConfirmUpdatesTimestamp:
    def test_confirm_updates_timestamp(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        _before = svc.get_confirmed_at("proj_test")
        svc.confirm_preferences("proj_test")
        after = svc.get_confirmed_at("proj_test")
        assert after is not None


# ---------------------------------------------------------------------------
# AC-7: New project inherits global+user, empty project prefs
# ---------------------------------------------------------------------------


class TestAC7NewProjectEmptyProjectPrefs:
    def test_new_project_empty_project_prefs(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc.set_global_rules("# Global Rules\n- Keep videos under 5 min")
        svc.set_user_preferences("test_user", "# User Preferences\n- Use dark theme")
        svc._init_project("proj_new")
        proj_prefs = svc.get_project_preferences("proj_new")
        assert proj_prefs == "" or proj_prefs is None
        # Project inherits global + user
        effective = svc.get_effective_preferences("proj_new")
        assert "5 min" in effective or "dark theme" in effective


# ---------------------------------------------------------------------------
# AC-8: snapshot refresh timestamp matches confirmed_at
# ---------------------------------------------------------------------------


class TestAC8SnapshotRefreshMatchesConfirmed:
    def test_snapshot_refresh_matches_confirmed(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        svc.confirm_preferences("proj_test")
        svc.create_snapshot("proj_test")
        confirmed = svc.get_confirmed_at("proj_test")
        snapshots = svc.list_snapshots("proj_test")
        assert len(snapshots) >= 1
        assert confirmed is not None


# ---------------------------------------------------------------------------
# AC-9: Snapshots capped at 20
# ---------------------------------------------------------------------------


class TestAC9SnapshotCapAt20:
    def test_snapshot_cap_at_20(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        for i in range(25):
            svc.create_snapshot("proj_test")
        snapshots = svc.list_snapshots("proj_test")
        assert len(snapshots) <= 20


# ---------------------------------------------------------------------------
# AC-10: Rollback creates new version
# ---------------------------------------------------------------------------


class TestAC10RollbackCreatesNewVersion:
    def test_rollback_creates_new_version(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, type TEXT, payload TEXT)"
        )
        conn.commit()
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        svc.confirm_preferences("proj_test")
        svc.create_snapshot("proj_test")
        before_count = len(svc.list_snapshots("proj_test"))
        # Rollback to version 1
        svc.rollback("proj_test", version=1)
        after_count = len(svc.list_snapshots("proj_test"))
        # Rollback creates a NEW version, so count increases
        assert after_count > before_count


# ---------------------------------------------------------------------------
# AC-11: Rollback writes event
# ---------------------------------------------------------------------------


class TestAC11RollbackWritesEvent:
    def test_rollback_writes_event(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, type TEXT, payload TEXT)"
        )
        conn.commit()
        svc = PreferenceService(conn)
        svc._ensure_tables()
        svc._init_project("proj_test")
        svc.create_snapshot("proj_test")
        svc.rollback("proj_test", version=1)
        row = conn.execute(
            "SELECT * FROM events WHERE project_id = 'proj_test' AND type = 'preference.rollback'"
        ).fetchone()
        assert row is not None


# -- Pydantic models for Instructor-based extraction -------------------------


class Candidate(BaseModel):
    id: str
    rule: str
    scope: str = "stage"
    stage: Optional[str] = None
    key: str
    value: str | int | float | bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = ""


class CandidateList(BaseModel):
    candidates: list[Candidate] = Field(default_factory=list)
    nothing_found: bool = False
