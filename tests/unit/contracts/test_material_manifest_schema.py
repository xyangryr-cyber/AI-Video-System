"""Tests for [SPEC-A-015] MaterialManifest + ShotMaterialBindings schemas (P7A).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-3.

Covers AC-1..AC-5 from tasks/SPEC-A/A-015-material-manifest-schemas.md.

Note: the task card's `Allowed Files` lists this file
(`tests/unit/contracts/test_material_manifest_schema.py`), while its
`Verification Commands` / `Test Mapping` reference
`tests/unit/contracts/test_spec_a_015.py`. Following SPEC-A-013/A-014
precedent (PROGRESS §[SPEC-A-014] Decisions), substantive AC bodies
live here (allowed path); the skip-stub at `test_spec_a_015.py` is
kept untouched (outside allowed_files).
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
MANIFEST_SCHEMA_PATH = ROOT / "schemas" / "material_manifest.schema.json"
BINDINGS_SCHEMA_PATH = ROOT / "schemas" / "shot_material_bindings.schema.json"
MANIFEST_TS_PATH = ROOT / "src" / "shared" / "types" / "material_manifest.ts"
BINDINGS_TS_PATH = ROOT / "src" / "shared" / "types" / "shot_material_bindings.ts"


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _material_payload(
    material_id: str = "mat_001",
    shot_id: str = "shot_01",
    material_type: str = "chart",
    verification_status: str = "pending",
) -> Dict[str, Any]:
    return {
        "material_id": material_id,
        "shot_id": shot_id,
        "material_type": material_type,
        "required": "hard",
        "source": {"kind": "api", "ref": "chart_svc://req_001"},
        "verification_status": verification_status,
        "fetched_at": "2026-04-20T10:00:00Z",
        "rationale": "needed for shot narrative emphasis",
    }


def _manifest_payload(
    project_id: str = "proj_abc",
    phase: str = "7A",
    materials: list[dict] | None = None,
) -> Dict[str, Any]:
    return {
        "project_id": project_id,
        "phase": phase,
        "materials": (
            materials
            if materials is not None
            else [_material_payload("mat_001", "shot_01")]
        ),
    }


def _binding_entry(
    shot_id: str = "shot_01",
    required_materials: tuple[str, ...] = ("mat_001",),
    optional_materials: tuple[str, ...] = (),
) -> Dict[str, Any]:
    return {
        "shot_id": shot_id,
        "required_materials": list(required_materials),
        "optional_materials": list(optional_materials),
    }


def _bindings_payload(
    bindings: list[dict] | None = None,
) -> Dict[str, Any]:
    return {
        "bindings": bindings if bindings is not None else [_binding_entry()],
    }


# ---------------------------------------------------------------------------
# AC-1: JSON Schemas accept valid payloads and reject illegal ones.
# ---------------------------------------------------------------------------


class TestAC1JsonSchemaPayloads:
    def test_manifest_valid(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        validator.validate(_manifest_payload())

    def test_manifest_invalid_material_type(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        bad = _manifest_payload(
            materials=[_material_payload(material_type="not_a_type")]
        )
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_manifest_invalid_material_id_pattern(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        bad = _manifest_payload(materials=[_material_payload(material_id="material_1")])
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_manifest_invalid_shot_id_pattern(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        bad = _manifest_payload(materials=[_material_payload(shot_id="shot_1")])
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_manifest_invalid_required_enum(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        mat = _material_payload()
        mat["required"] = "maybe"
        with pytest.raises(JsonSchemaError):
            validator.validate(_manifest_payload(materials=[mat]))

    def test_manifest_invalid_source_kind(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        mat = _material_payload()
        mat["source"]["kind"] = "websocket"
        with pytest.raises(JsonSchemaError):
            validator.validate(_manifest_payload(materials=[mat]))

    def test_manifest_invalid_verification_status(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        bad = _manifest_payload(
            materials=[_material_payload(verification_status="approved")]
        )
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_phase_must_be_7a(self):
        validator = Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH))
        for bad_phase in ("7", "P7A", "7a", "7B", "phase_7a", ""):
            with pytest.raises(JsonSchemaError):
                validator.validate(_manifest_payload(phase=bad_phase))
        # Explicit positive case.
        validator.validate(_manifest_payload(phase="7A"))

    def test_bindings_valid(self):
        validator = Draft202012Validator(_load_schema(BINDINGS_SCHEMA_PATH))
        validator.validate(
            _bindings_payload(
                bindings=[
                    _binding_entry(
                        shot_id="shot_01",
                        required_materials=("mat_001", "mat_002"),
                        optional_materials=("mat_003",),
                    ),
                    _binding_entry(
                        shot_id="shot_02",
                        required_materials=("mat_004",),
                        optional_materials=(),
                    ),
                ]
            )
        )

    def test_bindings_invalid_shot_id(self):
        validator = Draft202012Validator(_load_schema(BINDINGS_SCHEMA_PATH))
        with pytest.raises(JsonSchemaError):
            validator.validate(
                _bindings_payload(bindings=[_binding_entry(shot_id="shot_1")])
            )

    def test_bindings_invalid_material_id_pattern(self):
        validator = Draft202012Validator(_load_schema(BINDINGS_SCHEMA_PATH))
        with pytest.raises(JsonSchemaError):
            validator.validate(
                _bindings_payload(
                    bindings=[
                        _binding_entry(required_materials=("material_one",)),
                    ]
                )
            )


# ---------------------------------------------------------------------------
# AC-2: Pydantic <-> TS mirror - field names match.
# ---------------------------------------------------------------------------


def _ts_fields(ts_path: Path, interface_name: str) -> set[str]:
    text = ts_path.read_text(encoding="utf-8")
    header = re.search(
        rf"export interface {re.escape(interface_name)}\s*\{{",
        text,
    )
    assert header, f"interface {interface_name} not found in {ts_path.name}"
    start = header.end()
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
    cleaned_lines: list[str] = []
    for raw in body.splitlines():
        idx = raw.find("//")
        cleaned_lines.append(raw[:idx] if idx >= 0 else raw)
    body = "\n".join(cleaned_lines)
    fields: set[str] = set()
    for logical in body.split(";"):
        logical = logical.strip()
        if not logical:
            continue
        simplified = re.sub(r"\{[^{}]*\}", "", logical, flags=re.DOTALL)
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??:", simplified)
        if m:
            fields.add(m.group(1))
    return fields


class TestAC2PydanticTsAlignment:
    def test_pydantic_ts_alignment_manifest(self):
        from src.shared.schemas.material_manifest import (
            MaterialEntry,
            MaterialManifest,
            MaterialSource,
        )

        assert set(MaterialManifest.model_fields) == _ts_fields(
            MANIFEST_TS_PATH, "MaterialManifest"
        )
        assert set(MaterialEntry.model_fields) == _ts_fields(
            MANIFEST_TS_PATH, "MaterialEntry"
        )
        assert set(MaterialSource.model_fields) == _ts_fields(
            MANIFEST_TS_PATH, "MaterialSource"
        )

    def test_pydantic_ts_alignment_bindings(self):
        from src.shared.schemas.shot_material_bindings import (
            ShotBinding,
            ShotMaterialBindings,
        )

        assert set(ShotMaterialBindings.model_fields) == _ts_fields(
            BINDINGS_TS_PATH, "ShotMaterialBindings"
        )
        assert set(ShotBinding.model_fields) == _ts_fields(
            BINDINGS_TS_PATH, "ShotBinding"
        )


# ---------------------------------------------------------------------------
# AC-3: cross-artifact consistency - every referenced material_id must exist
# in the manifest.
# ---------------------------------------------------------------------------


class TestAC3CrossArtifactConsistency:
    def test_bindings_material_id_must_exist_in_manifest(self):
        from src.shared.schemas.material_manifest import MaterialManifest
        from src.shared.schemas.shot_material_bindings import (
            ShotMaterialBindings,
            validate_bindings_against_manifest,
        )

        manifest = MaterialManifest.model_validate(
            _manifest_payload(
                materials=[
                    _material_payload("mat_001", "shot_01"),
                    _material_payload("mat_002", "shot_01"),
                    _material_payload("mat_003", "shot_02"),
                ]
            )
        )

        bindings_ok = ShotMaterialBindings.model_validate(
            _bindings_payload(
                bindings=[
                    _binding_entry(
                        shot_id="shot_01",
                        required_materials=("mat_001",),
                        optional_materials=("mat_002",),
                    ),
                    _binding_entry(
                        shot_id="shot_02",
                        required_materials=("mat_003",),
                    ),
                ]
            )
        )
        validate_bindings_against_manifest(bindings_ok, manifest)

        bindings_bad = ShotMaterialBindings.model_validate(
            _bindings_payload(
                bindings=[
                    _binding_entry(
                        shot_id="shot_01",
                        required_materials=("mat_999",),
                    )
                ]
            )
        )
        with pytest.raises(ValueError):
            validate_bindings_against_manifest(bindings_bad, manifest)

        bindings_bad_opt = ShotMaterialBindings.model_validate(
            _bindings_payload(
                bindings=[
                    _binding_entry(
                        shot_id="shot_01",
                        required_materials=("mat_001",),
                        optional_materials=("mat_888",),
                    )
                ]
            )
        )
        with pytest.raises(ValueError):
            validate_bindings_against_manifest(bindings_bad_opt, manifest)


# ---------------------------------------------------------------------------
# AC-4: artifact registry contains the two new P7A entries.
# ---------------------------------------------------------------------------


class TestAC4RegistryEntries:
    def test_registry_contains_two_p7a_entries(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        manifest_key = "phase_7a/material_manifest.json"
        bindings_key = "phase_7a/shot_material_bindings.json"
        assert manifest_key in ARTIFACT_REGISTRY
        assert bindings_key in ARTIFACT_REGISTRY

        manifest = ARTIFACT_REGISTRY[manifest_key]
        assert "StoryboardAssetPlanner" in manifest.producer
        assert any("MaterialReadinessCheck" in c for c in manifest.consumers)
        assert "material_manifest.schema.json" in manifest.validation

        bindings = ARTIFACT_REGISTRY[bindings_key]
        assert "StoryboardAssetPlanner" in bindings.producer
        assert any("KeyframeRenderAgent" in c for c in bindings.consumers)
        assert "shot_material_bindings.schema.json" in bindings.validation


# ---------------------------------------------------------------------------
# AC-5: verification_status state machine
#   pending -> {verified, rejected, missing}
#   verified -> !pending (blocked; re-entry only via explicit supplement flow)
# ---------------------------------------------------------------------------


class TestAC5VerificationStatusTransitions:
    def test_verification_status_transitions(self):
        from src.shared.schemas.material_manifest import (
            VerificationStatus,
            validate_verification_status_transition,
        )

        assert set(VerificationStatus) == {
            VerificationStatus.PENDING,
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MISSING,
        }

        # Legal from pending.
        for nxt in (
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MISSING,
        ):
            validate_verification_status_transition(VerificationStatus.PENDING, nxt)

        # Idempotent no-op transitions are allowed.
        for s in VerificationStatus:
            validate_verification_status_transition(s, s)

        # verified -> pending is forbidden without supplement flow.
        with pytest.raises(ValueError):
            validate_verification_status_transition(
                VerificationStatus.VERIFIED, VerificationStatus.PENDING
            )

        # Supplement flow: explicit opt-in is accepted.
        validate_verification_status_transition(
            VerificationStatus.VERIFIED,
            VerificationStatus.PENDING,
            via_supplement=True,
        )

        # rejected -> pending and missing -> pending also require supplement.
        for s in (VerificationStatus.REJECTED, VerificationStatus.MISSING):
            with pytest.raises(ValueError):
                validate_verification_status_transition(s, VerificationStatus.PENDING)
            validate_verification_status_transition(
                s, VerificationStatus.PENDING, via_supplement=True
            )

        # verified -> rejected / missing without supplement is also forbidden
        # (state machine locks once verified).
        for nxt in (
            VerificationStatus.REJECTED,
            VerificationStatus.MISSING,
        ):
            with pytest.raises(ValueError):
                validate_verification_status_transition(
                    VerificationStatus.VERIFIED, nxt
                )

        # Negative: unknown inputs raise.
        with pytest.raises((ValueError, TypeError)):
            validate_verification_status_transition("pending", "approved")


# ---------------------------------------------------------------------------
# Extra: Pydantic also enforces the schema's required fields + enums.
# ---------------------------------------------------------------------------


class TestPydanticStrictness:
    def test_pydantic_rejects_unknown_fields(self):
        from src.shared.schemas.material_manifest import MaterialManifest

        payload = _manifest_payload()
        payload["materials"][0]["extra_field"] = "nope"
        with pytest.raises(PydanticError):
            MaterialManifest.model_validate(payload)

    def test_pydantic_rejects_non_7a_phase(self):
        from src.shared.schemas.material_manifest import MaterialManifest

        with pytest.raises(PydanticError):
            MaterialManifest.model_validate(_manifest_payload(phase="7B"))
