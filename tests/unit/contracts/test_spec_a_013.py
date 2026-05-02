"""Tests for [SPEC-A-013] MasterAudioArtifact schema + ProjectState.master_audio_ref + artifact registry 扩展.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-1.

Mirrors the 12 function names in tasks/SPEC-A/A-013-master-audio-schema.md
"Test Mapping" section (the task card's own statement that this file is the
verification target for AC-1..AC-6). Substantive coverage helper file at
tests/unit/contracts/test_audio_master_schema.py carries the same invariants
plus two additional Pydantic-side cases; both files share the canonical
payloads inlined here so neither file depends on the other.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError
from pydantic import ValidationError as PydanticError

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "audio_master.schema.json"
TS_PATH = ROOT / "src" / "shared" / "types" / "audio_master.ts"

CHECKSUM_NARRATION = "sha256:" + "a" * 64
CHECKSUM_BGM = "sha256:" + "b" * 64
CHECKSUM_FINAL = "sha256:" + "c" * 64


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _narration_payload() -> Dict[str, Any]:
    return {
        "kind": "narration_master",
        "file_path": "phase_4/narration_master.mp3",
        "based_on_phase": 4,
        "derived_from_segments": ["seg_01", "seg_02", "seg_03"],
        "total_duration_seconds": 123.45,
        "checksum": CHECKSUM_NARRATION,
        "version": 1,
    }


def _bgm_payload() -> Dict[str, Any]:
    return {
        "kind": "bgm_mix_master",
        "file_path": "phase_5/bgm_mix_master.mp3",
        "based_on_phase": 5,
        "derived_from_segments": ["seg_01", "seg_02"],
        "total_duration_seconds": 123.45,
        "checksum": CHECKSUM_BGM,
        "version": 1,
        "source_ref": {"kind": "narration_master", "checksum": CHECKSUM_NARRATION},
    }


def _final_payload() -> Dict[str, Any]:
    return {
        "kind": "final_audio_master",
        "file_path": "phase_6/final_audio_with_bgm_sfx.mp3",
        "based_on_phase": 6,
        "derived_from_segments": ["seg_01", "seg_02"],
        "total_duration_seconds": 123.45,
        "checksum": CHECKSUM_FINAL,
        "version": 1,
        "source_ref": {"kind": "bgm_mix_master", "checksum": CHECKSUM_BGM},
    }


def _minimal_project_state_kwargs() -> Dict[str, Any]:
    return {
        "project": {
            "project_id": "proj_x",
            "title": "t",
            "description": "d",
            "current_phase": 4,
            "status": "active",
            "category": "finance",
            "updated_at": "2026-04-19T00:00:00Z",
        },
        "phases": [],
        "active_tasks": [],
        "preferences": {"pending_candidates": 0, "last_confirmed_at": None},
        "system_status": {"all_critical_ok": True, "degraded_services": []},
    }


class TestAC1:
    """AC-1: audio_master.schema.json validates the three kinds and the documented invalid cases."""

    def test_narration_master_valid(self):
        schema = _load_schema()
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_narration_payload())
        Draft202012Validator(schema).validate(_bgm_payload())
        Draft202012Validator(schema).validate(_final_payload())

    def test_bgm_mix_master_requires_source_ref(self):
        schema = _load_schema()
        bgm_missing = _bgm_payload()
        del bgm_missing["source_ref"]
        with pytest.raises(JsonSchemaError):
            Draft202012Validator(schema).validate(bgm_missing)

        final_missing = _final_payload()
        del final_missing["source_ref"]
        with pytest.raises(JsonSchemaError):
            Draft202012Validator(schema).validate(final_missing)

    def test_narration_master_rejects_source_ref(self):
        schema = _load_schema()
        payload = _narration_payload()
        payload["source_ref"] = {
            "kind": "narration_master",
            "checksum": CHECKSUM_NARRATION,
        }
        with pytest.raises(JsonSchemaError):
            Draft202012Validator(schema).validate(payload)

    def test_invalid_kind_rejected(self):
        schema = _load_schema()
        payload = _narration_payload()
        payload["kind"] = "totally_bogus_kind"
        with pytest.raises(JsonSchemaError):
            Draft202012Validator(schema).validate(payload)


class TestAC2:
    """AC-2: Pydantic discriminated union round-trips and TS mirror has every Pydantic field name."""

    def test_pydantic_round_trip_three_kinds(self):
        from src.shared.schemas.audio_master import (
            BgmMixMasterArtifact,
            FinalAudioMasterArtifact,
            MasterAudioArtifactAdapter,
            NarrationMasterArtifact,
        )

        for payload, expected_cls in [
            (_narration_payload(), NarrationMasterArtifact),
            (_bgm_payload(), BgmMixMasterArtifact),
            (_final_payload(), FinalAudioMasterArtifact),
        ]:
            obj = MasterAudioArtifactAdapter.validate_python(payload)
            assert isinstance(obj, expected_cls)
            round_tripped = json.loads(
                MasterAudioArtifactAdapter.dump_json(obj).decode("utf-8")
            )
            assert round_tripped == payload

    def test_ts_pydantic_field_parity(self):
        from src.shared.schemas.audio_master import (
            BgmMixMasterArtifact,
            FinalAudioMasterArtifact,
            NarrationMasterArtifact,
        )

        ts_src = TS_PATH.read_text(encoding="utf-8")
        for cls in (
            NarrationMasterArtifact,
            BgmMixMasterArtifact,
            FinalAudioMasterArtifact,
        ):
            for field_name in cls.model_fields:
                assert re.search(rf"\b{re.escape(field_name)}\b", ts_src), (
                    f"TS mirror missing field '{field_name}' (from {cls.__name__})"
                )


class TestAC3:
    """AC-3: ProjectState.master_audio_ref is optional and the TS mirror declares it."""

    def test_project_state_master_audio_ref_optional(self):
        from src.shared.schemas.project_state import ProjectState

        assert "master_audio_ref" in ProjectState.model_fields, (
            "ProjectState must declare `master_audio_ref`"
        )
        state = ProjectState(**_minimal_project_state_kwargs())
        assert state.master_audio_ref is None

        ts_src = (ROOT / "src" / "shared" / "types" / "project_state.ts").read_text(
            encoding="utf-8"
        )
        assert re.search(r"\bmaster_audio_ref\b", ts_src), (
            "TS ProjectState must mirror master_audio_ref"
        )

    def test_project_state_master_audio_ref_valid_payload(self):
        from src.shared.schemas.project_state import ProjectState

        kwargs = _minimal_project_state_kwargs()
        kwargs["master_audio_ref"] = {
            "kind": "bgm_mix_master",
            "file_path": "phase_5/bgm_mix_master.mp3",
            "based_on_phase": 5,
            "checksum": CHECKSUM_BGM,
            "version": 1,
        }
        state = ProjectState(**kwargs)
        assert state.master_audio_ref is not None
        assert state.master_audio_ref.kind == "bgm_mix_master"
        assert state.master_audio_ref.based_on_phase == 5


class TestAC4:
    """AC-4: artifact registry contains the three master-audio entries with proper producer/consumer/validation."""

    def test_registry_contains_three_master_audio_entries(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        expected = {
            "phase_4/narration_master.mp3": "NarrationMasterAssembler",
            "phase_5/bgm_mix_master.mp3": "BgmMixRenderer",
            "phase_6/final_audio_with_bgm_sfx.mp3": "FinalAudioAssembler",
        }
        for key, producer in expected.items():
            assert key in ARTIFACT_REGISTRY, f"registry missing '{key}'"
            entry = ARTIFACT_REGISTRY[key]
            assert entry.producer == producer, (
                f"{key}: producer expected {producer}, got {entry.producer}"
            )
            assert isinstance(entry.consumers, tuple) and entry.consumers, (
                f"{key}: consumers must be a non-empty tuple"
            )
            assert "audio_master.schema.json" in entry.validation, (
                f"{key}: validation must reference audio_master.schema.json"
            )


class TestAC5:
    """AC-5: validate_checksum_chain enforces bgm.source_ref == narration.checksum and final.source_ref == bgm.checksum."""

    def test_checksum_chain_bgm_to_narration(self):
        from src.shared.schemas.audio_master import (
            MasterAudioArtifactAdapter,
            validate_checksum_chain,
        )

        narration = MasterAudioArtifactAdapter.validate_python(_narration_payload())
        bgm = MasterAudioArtifactAdapter.validate_python(_bgm_payload())

        validate_checksum_chain(bgm, narration)

        bad = _bgm_payload()
        bad["source_ref"]["checksum"] = "sha256:" + "9" * 64
        bad_obj = MasterAudioArtifactAdapter.validate_python(bad)
        with pytest.raises(ValueError):
            validate_checksum_chain(bad_obj, narration)

    def test_checksum_chain_final_to_bgm(self):
        from src.shared.schemas.audio_master import (
            MasterAudioArtifactAdapter,
            validate_checksum_chain,
        )

        bgm = MasterAudioArtifactAdapter.validate_python(_bgm_payload())
        final = MasterAudioArtifactAdapter.validate_python(_final_payload())

        validate_checksum_chain(final, bgm)

        bad = _final_payload()
        bad["source_ref"]["checksum"] = "sha256:" + "0" * 64
        bad_obj = MasterAudioArtifactAdapter.validate_python(bad)
        with pytest.raises(ValueError):
            validate_checksum_chain(bad_obj, bgm)


class TestAC6:
    """AC-6: cross-language alignment — schema properties == union of Pydantic fields, schema required == intersection, and TS mirror covers every property."""

    def test_cross_language_field_alignment(self):
        from src.shared.schemas.audio_master import (
            BgmMixMasterArtifact,
            FinalAudioMasterArtifact,
            MasterAudioArtifactAdapter,
            NarrationMasterArtifact,
            SourceRef,
        )

        schema = _load_schema()
        schema_props = set(schema["properties"].keys())
        schema_required = set(schema["required"])

        py_union_fields = (
            set(NarrationMasterArtifact.model_fields.keys())
            | set(BgmMixMasterArtifact.model_fields.keys())
            | set(FinalAudioMasterArtifact.model_fields.keys())
        )
        assert schema_props == py_union_fields, (
            f"Schema properties {schema_props} != Pydantic union {py_union_fields}"
        )

        common_required = (
            set(NarrationMasterArtifact.model_fields.keys())
            & set(BgmMixMasterArtifact.model_fields.keys())
            & set(FinalAudioMasterArtifact.model_fields.keys())
        )
        assert schema_required == common_required, (
            f"Schema required {schema_required} != Pydantic common {common_required}"
        )

        schema_source_ref = schema["properties"]["source_ref"]
        assert set(schema_source_ref["properties"].keys()) == set(
            SourceRef.model_fields.keys()
        )

        ts_src = TS_PATH.read_text(encoding="utf-8")
        for name in schema_props:
            assert re.search(rf"\b{re.escape(name)}\b", ts_src), (
                f"TS mirror missing '{name}'"
            )

        # Defensive sanity: PydanticError surface still rejects narration with
        # source_ref (kept here so this file's coverage is self-contained and
        # does not silently degrade if test_audio_master_schema.py is moved).
        bad = _narration_payload()
        bad["source_ref"] = {
            "kind": "narration_master",
            "checksum": CHECKSUM_NARRATION,
        }
        with pytest.raises(PydanticError):
            MasterAudioArtifactAdapter.validate_python(bad)
