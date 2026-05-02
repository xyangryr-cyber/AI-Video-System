"""Tests for [SPEC-A-014] SfxLayoutPlan + SfxMixSegments schemas (P6 dual-layer).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-2.

Covers AC-1..AC-5 from tasks/SPEC-A/A-014-sfx-layout-and-mix-schemas.md.

Note: the task card's `Allowed Files` lists `tests/unit/contracts/test_sfx_schemas.py`
(this file), while `Verification Commands` / `Test Mapping` reference
`tests/unit/contracts/test_spec_a_014.py`. Substantive bodies live here
(allowed path). The stub file is kept untouched. See PROGRESS.md
SPEC-A-014 entry for rationale.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest
from jsonschema import Draft202012Validator
from jsonschema import ValidationError as JsonSchemaError
from pydantic import ValidationError as PydanticError

ROOT = Path(__file__).resolve().parents[3]
LAYOUT_SCHEMA_PATH = ROOT / "schemas" / "sfx_layout_plan.schema.json"
MIX_SCHEMA_PATH = ROOT / "schemas" / "sfx_mix_segments.schema.json"
LAYOUT_TS_PATH = ROOT / "src" / "shared" / "types" / "sfx_layout_plan.ts"
MIX_TS_PATH = ROOT / "src" / "shared" / "types" / "sfx_mix_segments.ts"

CHECKSUM_SEG = "sha256:" + "a" * 64


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _trigger_payload(trigger_id: str = "trg_001") -> Dict[str, Any]:
    return {
        "trigger_id": trigger_id,
        "script_anchor": {"span_id": "span_001", "text": "opening surge"},
        "keyword_span": [0, 4],
        "planned_time_sec": 12.5,
        "sfx_type": "impact",
        "rationale": "emphasize the opening surge",
        "narrative_role": "emphasis",
        "volume_db": -6.0,
        "duration_seconds": 1.25,
    }


def _layout_payload() -> Dict[str, Any]:
    return {
        "plan_version": 1,
        "triggers": [_trigger_payload("trg_001"), _trigger_payload("trg_002")],
    }


def _segment_payload(
    segment_id: str = "seg_01",
    applied: tuple[str, ...] = ("trg_001",),
) -> Dict[str, Any]:
    return {
        "segment_id": segment_id,
        "file_path": f"phase_6/sfx_applied_segments/{segment_id}.mp3",
        "applied_triggers": list(applied),
        "checksum": CHECKSUM_SEG,
        "version": 1,
    }


def _mix_payload(
    base_master: str = "phase_5/bgm_mix_master.mp3",
    segments: list[dict] | None = None,
) -> Dict[str, Any]:
    return {
        "base_master": base_master,
        "segments": segments if segments is not None else [_segment_payload()],
    }


# ---------------------------------------------------------------------------
# AC-1: JSON Schemas accept valid payloads and reject illegal ones.
# ---------------------------------------------------------------------------


class TestAC1JsonSchemaPayloads:
    def test_layout_plan_valid(self):
        validator = Draft202012Validator(_load_schema(LAYOUT_SCHEMA_PATH))
        validator.validate(_layout_payload())

    def test_layout_plan_invalid_trigger_id(self):
        validator = Draft202012Validator(_load_schema(LAYOUT_SCHEMA_PATH))
        payload = _layout_payload()
        payload["triggers"][0]["trigger_id"] = "bad_id_001"
        with pytest.raises(JsonSchemaError):
            validator.validate(payload)

    def test_layout_plan_invalid_keyword_span_length(self):
        validator = Draft202012Validator(_load_schema(LAYOUT_SCHEMA_PATH))
        payload = _layout_payload()
        payload["triggers"][0]["keyword_span"] = [0, 4, 9]
        with pytest.raises(JsonSchemaError):
            validator.validate(payload)

    def test_layout_plan_invalid_planned_time_sec_negative(self):
        validator = Draft202012Validator(_load_schema(LAYOUT_SCHEMA_PATH))
        payload = _layout_payload()
        payload["triggers"][0]["planned_time_sec"] = -0.1
        with pytest.raises(JsonSchemaError):
            validator.validate(payload)

    def test_mix_segments_valid(self):
        validator = Draft202012Validator(_load_schema(MIX_SCHEMA_PATH))
        validator.validate(_mix_payload())

    def test_mix_segments_invalid_checksum(self):
        validator = Draft202012Validator(_load_schema(MIX_SCHEMA_PATH))
        payload = _mix_payload()
        payload["segments"][0]["checksum"] = "md5:" + "a" * 64
        with pytest.raises(JsonSchemaError):
            validator.validate(payload)

    def test_mix_segments_invalid_segment_id(self):
        validator = Draft202012Validator(_load_schema(MIX_SCHEMA_PATH))
        bad = _segment_payload(segment_id="segment_1")
        bad["file_path"] = "phase_6/sfx_applied_segments/seg_01.mp3"
        payload = _mix_payload(segments=[bad])
        with pytest.raises(JsonSchemaError):
            validator.validate(payload)


# ---------------------------------------------------------------------------
# AC-2: Pydantic <-> TS mirror - field names (required + optional) match.
# ---------------------------------------------------------------------------


def _ts_fields(ts_path: Path, interface_name: str) -> set[str]:
    text = ts_path.read_text(encoding="utf-8")
    header = re.search(
        rf"export interface {re.escape(interface_name)}\s*\{{",
        text,
    )
    assert header, f"interface {interface_name} not found in {ts_path.name}"
    start = header.end()
    # Brace-balanced scan, skipping line comments so `{` / `}` inside
    # `// comment` (e.g. regex snippets like `\d{2,}`) don't confuse us.
    depth = 1
    i = start
    in_line_comment = False
    while i < len(text) and depth > 0:
        ch = text[i]
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            in_line_comment = True
            i += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    body = text[start : i - 1]
    # Strip line comments from remaining body so nested-regex braces in
    # comments don't leak field names.
    cleaned_lines: list[str] = []
    for raw in body.splitlines():
        idx = raw.find("//")
        cleaned_lines.append(raw[:idx] if idx >= 0 else raw)
    body = "\n".join(cleaned_lines)
    fields: set[str] = set()
    # Top-level field detection: match at the start of a logical line and
    # ignore anything that looks like a nested object literal.
    depth2 = 0
    for logical in body.split(";"):
        logical = logical.strip()
        if not logical:
            continue
        # Flatten nested braces out of the match target.
        simplified = re.sub(r"\{[^{}]*\}", "", logical, flags=re.DOTALL)
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??:", simplified)
        if m:
            fields.add(m.group(1))
        _ = depth2  # quiet lint
    return fields


class TestAC2PydanticTsAlignment:
    def test_pydantic_ts_alignment_layout(self):
        from src.shared.schemas.sfx_layout_plan import (
            SfxLayoutPlan,
            SfxLayoutTrigger,
            SfxScriptAnchor,
        )

        assert set(SfxLayoutPlan.model_fields) == _ts_fields(
            LAYOUT_TS_PATH, "SfxLayoutPlan"
        )
        assert set(SfxLayoutTrigger.model_fields) == _ts_fields(
            LAYOUT_TS_PATH, "SfxLayoutTrigger"
        )
        assert set(SfxScriptAnchor.model_fields) == _ts_fields(
            LAYOUT_TS_PATH, "SfxScriptAnchor"
        )

    def test_pydantic_ts_alignment_mix(self):
        from src.shared.schemas.sfx_mix_segments import (
            SfxMixSegment,
            SfxMixSegments,
        )

        assert set(SfxMixSegments.model_fields) == _ts_fields(
            MIX_TS_PATH, "SfxMixSegments"
        )
        assert set(SfxMixSegment.model_fields) == _ts_fields(
            MIX_TS_PATH, "SfxMixSegment"
        )


# ---------------------------------------------------------------------------
# AC-3: Pydantic enforces the base_master pattern.
# ---------------------------------------------------------------------------


class TestAC3BaseMasterPattern:
    def test_base_master_pattern_enforced(self):
        from src.shared.schemas.sfx_mix_segments import SfxMixSegments

        SfxMixSegments.model_validate(_mix_payload("phase_5/bgm_mix_master.mp3"))
        SfxMixSegments.model_validate(_mix_payload("phase_4/narration_master.mp3"))

        for bad in (
            "phase_6/final_audio_with_bgm_sfx.mp3",
            "phase_5/bgm_mix_master.wav",
            "phase_4/narration_master",
            "phase_5/other_master.mp3",
        ):
            with pytest.raises(PydanticError):
                SfxMixSegments.model_validate(_mix_payload(bad))


# ---------------------------------------------------------------------------
# AC-4: artifact registry contains the two new SFX entries.
# ---------------------------------------------------------------------------


class TestAC4RegistryEntries:
    def test_registry_contains_two_sfx_entries(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        layout_key = "phase_6/sfx_layout_plan.json"
        mix_key = "phase_6/sfx_mix_segments.json"
        assert layout_key in ARTIFACT_REGISTRY
        assert mix_key in ARTIFACT_REGISTRY

        layout = ARTIFACT_REGISTRY[layout_key]
        assert "SfxLayoutPlanner" in layout.producer
        assert any("SfxLayoutReviewer" in c for c in layout.consumers)
        assert "sfx_layout_plan.schema.json" in layout.validation

        mix = ARTIFACT_REGISTRY[mix_key]
        assert "SfxSegmentMixService" in mix.producer
        assert any("FinalAudioAssembler" in c for c in mix.consumers)
        assert "sfx_mix_segments.schema.json" in mix.validation


# ---------------------------------------------------------------------------
# AC-5: cross-artifact consistency between plan and mix.
# ---------------------------------------------------------------------------


class TestAC5CrossArtifactConsistency:
    def test_applied_triggers_must_exist_in_plan(self):
        from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan
        from src.shared.schemas.sfx_mix_segments import (
            SfxMixSegments,
            validate_applied_triggers_against_plan,
        )

        plan = SfxLayoutPlan.model_validate(_layout_payload())

        mix_ok = SfxMixSegments.model_validate(
            _mix_payload(
                segments=[
                    _segment_payload("seg_01", applied=("trg_001",)),
                    _segment_payload("seg_02", applied=("trg_001", "trg_002")),
                ]
            )
        )
        validate_applied_triggers_against_plan(mix_ok, plan)

        mix_bad = SfxMixSegments.model_validate(
            _mix_payload(
                segments=[
                    _segment_payload("seg_01", applied=("trg_001",)),
                    _segment_payload("seg_02", applied=("trg_999",)),
                ]
            )
        )
        with pytest.raises(ValueError):
            validate_applied_triggers_against_plan(mix_bad, plan)
