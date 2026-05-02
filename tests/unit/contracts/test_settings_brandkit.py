"""Tests for [SPEC-A-003] Settings, Preferences & BrandKit Contracts.

Real test implementations (allowed_files for SPEC-A-003). The stub file
test_spec_a_003.py is a placeholder; this file holds the actual assertions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]


class TestAC1BrandKitPydanticModel:
    """AC-1: BrandKit Pydantic model validates logo, watermark, intro/outro_template,
    color_palette, font_family with position enum and opacity 0-1."""

    def test_brand_kit_valid(self):
        from src.shared.schemas.brand_kit import BrandKit

        bk = BrandKit(
            logo={"path": "/assets/logo.png", "position": "top_left", "opacity": 0.8},
            watermark={
                "text": "Confidential",
                "opacity": 0.3,
                "position": "bottom_right",
            },
            intro_template={"template_id": "intro_v1", "duration": 3.0},
            outro_template={"template_id": "outro_v1", "duration": 3.0},
            color_palette={
                "primary": "#1a73e8",
                "secondary": "#34a853",
                "accent": "#ea4335",
                "background": "#ffffff",
            },
            font_family="Noto Sans SC",
        )
        assert bk.font_family == "Noto Sans SC"
        assert bk.logo.position == "top_left"
        assert bk.logo.opacity == pytest.approx(0.8)
        assert bk.logo.path == "/assets/logo.png"
        assert bk.watermark.text == "Confidential"
        assert bk.watermark.opacity == pytest.approx(0.3)
        assert bk.intro_template.template_id == "intro_v1"
        assert bk.outro_template.duration == pytest.approx(3.0)
        assert bk.color_palette.primary == "#1a73e8"

    def test_brand_kit_null_optionals_valid(self):
        from src.shared.schemas.brand_kit import BrandKit

        bk = BrandKit(
            logo={"path": None, "position": "bottom_left", "opacity": 0.5},
            watermark={"text": None, "opacity": 0.3, "position": "bottom_right"},
            intro_template={"template_id": None, "duration": 3.0},
            outro_template={"template_id": None, "duration": 3.0},
            color_palette={
                "primary": "#000000",
                "secondary": "#111111",
                "accent": "#222222",
                "background": "#ffffff",
            },
            font_family="Arial",
        )
        assert bk.logo.path is None
        assert bk.watermark.text is None
        assert bk.intro_template.template_id is None

    def test_brand_kit_rejects_invalid_position(self):
        from src.shared.schemas.brand_kit import BrandKit

        with pytest.raises(ValidationError):
            BrandKit(
                logo={"path": None, "position": "center", "opacity": 0.5},
                watermark={"text": None, "opacity": 0.3, "position": "bottom_right"},
                intro_template={"template_id": None, "duration": 3.0},
                outro_template={"template_id": None, "duration": 3.0},
                color_palette={
                    "primary": "#1a73e8",
                    "secondary": "#34a853",
                    "accent": "#ea4335",
                    "background": "#ffffff",
                },
                font_family="Noto Sans SC",
            )

    def test_brand_kit_rejects_opacity_out_of_range(self):
        from src.shared.schemas.brand_kit import BrandKit

        with pytest.raises(ValidationError):
            BrandKit(
                logo={"path": None, "position": "top_left", "opacity": 1.5},
                watermark={"text": None, "opacity": 0.3, "position": "bottom_right"},
                intro_template={"template_id": None, "duration": 3.0},
                outro_template={"template_id": None, "duration": 3.0},
                color_palette={
                    "primary": "#1a73e8",
                    "secondary": "#34a853",
                    "accent": "#ea4335",
                    "background": "#ffffff",
                },
                font_family="Noto Sans SC",
            )


class TestAC2BrandKitTsMatchesPydantic:
    """AC-2: BrandKit TS interface mirrors the Pydantic model."""

    def test_brand_kit_ts_matches_pydantic(self):
        from src.shared.schemas.brand_kit import BrandKit, BrandKitLogo

        ts_path = ROOT / "src" / "shared" / "types" / "brand_kit.ts"
        assert ts_path.exists(), "src/shared/types/brand_kit.ts must exist"
        ts = ts_path.read_text(encoding="utf-8")

        assert re.search(r"\binterface\s+BrandKit\b", ts), "BrandKit interface missing"
        assert re.search(r"\binterface\s+BrandKitLogo\b", ts), (
            "BrandKitLogo interface missing"
        )

        for field in BrandKit.model_fields:
            assert re.search(rf"\b{field}\b", ts), (
                f"brand_kit.ts missing BrandKit field: {field}"
            )

        for field in BrandKitLogo.model_fields:
            assert re.search(rf"\b{field}\b", ts), (
                f"brand_kit.ts missing BrandKitLogo field: {field}"
            )

        for val in ("top_left", "top_right", "bottom_left", "bottom_right"):
            assert val in ts, f"brand_kit.ts missing position value: {val}"


class TestAC3SettingsResponseSchema:
    """AC-3: Settings response schema includes model_config and brand_kit sections."""

    def test_settings_response_schema(self):
        from src.shared.schemas.settings import SettingsResponse

        fields = set(SettingsResponse.model_fields)
        assert "brand_kit" in fields, "SettingsResponse missing brand_kit"
        has_model_config = any("model_config" in f for f in fields)
        assert has_model_config, (
            f"SettingsResponse missing model_config section; fields: {fields}"
        )

    def test_settings_response_round_trip(self):
        from src.shared.schemas.brand_kit import BrandKit
        from src.shared.schemas.settings import SettingsResponse

        bk = BrandKit(
            logo={"path": None, "position": "top_left", "opacity": 0.5},
            watermark={"text": None, "opacity": 0.3, "position": "bottom_right"},
            intro_template={"template_id": None, "duration": 3.0},
            outro_template={"template_id": None, "duration": 3.0},
            color_palette={
                "primary": "#1a73e8",
                "secondary": "#34a853",
                "accent": "#ea4335",
                "background": "#ffffff",
            },
            font_family="Noto Sans SC",
        )
        resp = SettingsResponse(model_config_data={}, brand_kit=bk)
        assert resp.brand_kit.font_family == "Noto Sans SC"


class TestAC4PreferencesResponseSchema:
    """AC-4: Preferences response schema includes global_rules_md and user_preferences_md."""

    def test_preferences_response_schema(self):
        from src.shared.schemas.settings import PreferencesResponse

        fields = set(PreferencesResponse.model_fields)
        assert "global_rules_md" in fields, (
            "PreferencesResponse missing global_rules_md"
        )
        assert "user_preferences_md" in fields, (
            "PreferencesResponse missing user_preferences_md"
        )

    def test_preferences_response_round_trip(self):
        from src.shared.schemas.settings import PreferencesResponse

        resp = PreferencesResponse(
            global_rules_md="# Rules", user_preferences_md="# Prefs"
        )
        assert resp.global_rules_md == "# Rules"
        assert resp.user_preferences_md == "# Prefs"


class TestAC5PreferencesUpdateOptionalFields:
    """AC-5: Both fields are optional in the update request."""

    def test_preferences_update_optional_fields(self):
        from src.shared.schemas.settings import PreferencesUpdateRequest

        empty = PreferencesUpdateRequest()
        assert empty.global_rules_md is None
        assert empty.user_preferences_md is None

        partial = PreferencesUpdateRequest(global_rules_md="# Rules")
        assert partial.global_rules_md == "# Rules"
        assert partial.user_preferences_md is None

        full = PreferencesUpdateRequest(
            global_rules_md="# Rules", user_preferences_md="# Prefs"
        )
        assert full.global_rules_md == "# Rules"
        assert full.user_preferences_md == "# Prefs"


class TestAC6SnapshotListResponse:
    """AC-6: Snapshot list response includes array of {id, created_at, preview}."""

    def test_snapshot_list_response(self):
        from src.shared.schemas.settings import SnapshotItem, SnapshotListResponse

        item_fields = set(SnapshotItem.model_fields)
        assert "id" in item_fields, "SnapshotItem missing id"
        assert "created_at" in item_fields, "SnapshotItem missing created_at"
        assert "preview" in item_fields, "SnapshotItem missing preview"

        resp = SnapshotListResponse(
            snapshots=[
                SnapshotItem(
                    id="snap_001",
                    created_at="2026-04-24T10:00:00Z",
                    preview="# Rules preview",
                ),
            ]
        )
        assert len(resp.snapshots) == 1
        assert resp.snapshots[0].id == "snap_001"
        assert resp.snapshots[0].preview == "# Rules preview"

    def test_snapshot_list_response_empty(self):
        from src.shared.schemas.settings import SnapshotListResponse

        resp = SnapshotListResponse(snapshots=[])
        assert resp.snapshots == []


class TestAC7PreferenceWriteFlowDocumented:
    """AC-7: Write flow constants encode snapshot-first-then-update + returns snapshot_id."""

    def test_preference_write_flow_invariants(self):
        from src.shared.schemas.settings import PREFERENCE_WRITE_FLOW

        assert PREFERENCE_WRITE_FLOW["snapshot_before_update"] is True, (
            "Write flow must document snapshot_before_update = True"
        )
        assert "snapshot_id" in PREFERENCE_WRITE_FLOW["returns"], (
            "Write flow must document that snapshot_id is returned"
        )
        steps = PREFERENCE_WRITE_FLOW["steps"]
        assert len(steps) >= 3, "Write flow must document at least 3 steps"
        combined = " ".join(steps).lower()
        assert "snapshot" in combined, "Write flow steps must mention 'snapshot'"
        assert "update" in combined or "preferences" in combined, (
            "Write flow steps must mention update/preferences"
        )


class TestAC8PreferenceRollbackFlowDocumented:
    """AC-8: Rollback flow constants encode snapshot-current + overwrite + audit event."""

    def test_preference_rollback_flow_invariants(self):
        from src.shared.schemas.settings import PREFERENCE_ROLLBACK_FLOW

        assert PREFERENCE_ROLLBACK_FLOW["snapshot_current"] is True, (
            "Rollback flow must document snapshot_current = True"
        )
        assert PREFERENCE_ROLLBACK_FLOW["overwrite_from_target"] is True, (
            "Rollback flow must document overwrite_from_target = True"
        )
        assert PREFERENCE_ROLLBACK_FLOW["audit_event"] == "preference.rollback", (
            "Rollback flow audit_event must be 'preference.rollback'"
        )
        assert "new_snapshot_id" in PREFERENCE_ROLLBACK_FLOW["returns"], (
            "Rollback flow must document that new_snapshot_id is returned"
        )
        steps = PREFERENCE_ROLLBACK_FLOW["steps"]
        combined = " ".join(steps).lower()
        assert "snapshot" in combined, "Rollback flow steps must mention 'snapshot'"
        assert any(w in combined for w in ("overwrite", "target", "覆盖")), (
            "Rollback flow steps must mention overwrite/target"
        )
        assert (
            "preference.rollback" in combined
            or "audit" in combined
            or "event" in combined
        ), "Rollback flow steps must mention the audit event"
