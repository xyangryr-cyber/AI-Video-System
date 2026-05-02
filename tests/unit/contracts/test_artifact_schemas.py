"""Tests for [SPEC-A-001] Artifact JSON Schemas.

Covers AC-1..AC-6 from tasks/SPEC-A/A-001-artifact-schemas.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = ROOT / "schemas"
TYPES_TS = ROOT / "src" / "shared" / "types" / "artifacts.ts"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC-1: requirements.json JSON Schema
# ---------------------------------------------------------------------------


def _valid_requirements_payload() -> dict:
    return {
        "project_id": "proj_abc123",
        "title": "Q1 Earnings Preview",
        "topic": "Tech sector earnings outlook for Q1 2026",
        "duration_class": "medium",
        "target_duration": {"min_sec": 180, "max_sec": 600},
        "target_word_count": {"min": 800, "max": 3000},
        "platform": [{"platform": "youtube", "role": "primary"}],
        "category": {"level1": "finance", "level2": "stock_market"},
        "narrative_template": "progressive",
        "voice_preferences": {"voice_id": "v_1", "style": "calm"},
        "subtitle_preferences": {"style": "word_by_word", "highlight_enabled": True},
    }


class TestAC1RequirementsJsonSchema:
    def test_requirements_json_schema_valid(self):
        schema = _load_schema("requirements.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_valid_requirements_payload())

    def test_requirements_json_schema_rejects_short_topic(self):
        schema = _load_schema("requirements.schema.json")
        payload = _valid_requirements_payload()
        payload["topic"] = "abcd"  # 4 chars, below minLength 5
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(payload)


# ---------------------------------------------------------------------------
# AC-2: timeline.json JSON Schema
# ---------------------------------------------------------------------------


def _valid_timeline_payload() -> dict:
    return {
        "segments": [
            {
                "segment_id": "seg_01",
                "text": "Opening line",
                "start_sec": 0.0,
                "end_sec": 12.5,
                "audio_path": "phase_4/narration_seg_01.mp3",
                "voice_params": {"rate_multiplier": 1.0, "emotion": "neutral"},
                "word_count": 50,
            }
        ],
        "total_duration_sec": 300.0,
        "sample_rate": 44100,
    }


class TestAC2TimelineJsonSchema:
    def test_timeline_json_schema_valid(self):
        schema = _load_schema("timeline.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_valid_timeline_payload())

    def test_timeline_json_schema_rejects_missing_segments(self):
        schema = _load_schema("timeline.schema.json")
        payload = _valid_timeline_payload()
        del payload["segments"]
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(payload)


# ---------------------------------------------------------------------------
# AC-3: style_lock.json JSON Schema
# ---------------------------------------------------------------------------


def _valid_style_lock_payload() -> dict:
    return {
        "project_id": "proj_abc123",
        "locked_at": "2026-04-17T10:00:00Z",
        "locked_by": "user_confirmed",
        "color_palette": {
            "primary": "#1a73e8",
            "secondary": "#34a853",
            "accent": "#ea4335",
            "background": "#ffffff",
        },
        "font_family": "Noto Sans SC",
        "chart_style": {
            "axis_color": "#666",
            "grid_color": "#eee",
            "label_font_size": 14,
        },
    }


class TestAC3StyleLockJsonSchema:
    def test_style_lock_json_schema_valid(self):
        schema = _load_schema("style_lock.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_valid_style_lock_payload())

    def test_style_lock_json_schema_rejects_invalid_locked_by(self):
        schema = _load_schema("style_lock.schema.json")
        payload = _valid_style_lock_payload()
        payload["locked_by"] = "system_override"
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(payload)


# ---------------------------------------------------------------------------
# AC-4: Pydantic round-trip
# ---------------------------------------------------------------------------


class TestAC4PydanticRoundTrip:
    def test_pydantic_round_trip_requirements(self):
        from src.shared.schemas.artifacts import Requirements

        payload = _valid_requirements_payload()
        model = Requirements.model_validate(payload)
        roundtrip = json.loads(model.model_dump_json())
        assert roundtrip == payload

    def test_pydantic_round_trip_timeline(self):
        from src.shared.schemas.artifacts import Timeline

        payload = _valid_timeline_payload()
        model = Timeline.model_validate(payload)
        roundtrip = json.loads(model.model_dump_json())
        assert roundtrip == payload

    def test_pydantic_round_trip_style_lock(self):
        from src.shared.schemas.artifacts import StyleLock

        payload = _valid_style_lock_payload()
        model = StyleLock.model_validate(payload)
        roundtrip = json.loads(model.model_dump_json())
        assert roundtrip == payload


# ---------------------------------------------------------------------------
# AC-5: TS interfaces match Pydantic
# ---------------------------------------------------------------------------


class TestAC5TypeScriptInterfacesMatchPydantic:
    def test_ts_interfaces_match_pydantic(self):
        from src.shared.schemas.artifacts import Requirements, StyleLock, Timeline

        ts_source = TYPES_TS.read_text(encoding="utf-8")

        def ts_interface_fields(name: str) -> set[str]:
            m = re.search(
                rf"export interface {name}\s*\{{([^}}]*)\}}",
                ts_source,
                re.DOTALL,
            )
            assert m is not None, f"interface {name} not found in artifacts.ts"
            body = m.group(1)
            fields = set()
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                fm = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*\??\s*:", line)
                if fm:
                    fields.add(fm.group(1))
            return fields

        for model_cls, iface in [
            (Requirements, "Requirements"),
            (Timeline, "Timeline"),
            (StyleLock, "StyleLock"),
        ]:
            py_fields = set(model_cls.model_fields.keys())
            ts_fields = ts_interface_fields(iface)
            assert py_fields == ts_fields, (
                f"field mismatch for {iface}: "
                f"python-only={py_fields - ts_fields}, ts-only={ts_fields - py_fields}"
            )


# ---------------------------------------------------------------------------
# AC-6: Artifact registry covers all 8
# ---------------------------------------------------------------------------


class TestAC6ArtifactRegistryCoversAll8:
    def test_artifact_registry_covers_all_8(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        # AC-6 baseline: the 8 core artifacts must always be present. Later
        # SPEC-A cards (A-013..A-016) add master-audio / material-manifest
        # entries; those extensions are allowed and tested by their own
        # contract tests, so here we only enforce the baseline-8 invariant.
        core_8 = {
            "requirements.json",
            "outline",
            "polished_script",
            "timeline.json",
            "style_lock.json",
            "keyframe_renders",
            "rough_cut",
            "final_cut",
        }
        registry_keys = set(ARTIFACT_REGISTRY.keys())
        missing = core_8 - registry_keys
        assert not missing, f"artifact registry dropped core entries: {missing}"
        for name, entry in ARTIFACT_REGISTRY.items():
            assert entry.producer, f"{name} missing producer"
            assert entry.consumers, f"{name} missing consumers"
            assert entry.validation, f"{name} missing validation"
