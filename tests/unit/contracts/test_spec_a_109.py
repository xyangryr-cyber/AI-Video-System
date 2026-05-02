"""SPEC-A-109 (v3.18 D7): PolishedScriptArtifact with optional style_applied."""

from __future__ import annotations

from src.shared.schemas.artifacts import PolishedScriptArtifact


def test_polished_script_artifact_accepts_style_applied():
    a = PolishedScriptArtifact(style_applied="亲切科普型")
    assert a.style_applied == "亲切科普型"


def test_polished_script_artifact_omits_style_applied():
    a = PolishedScriptArtifact()
    assert a.style_applied is None
