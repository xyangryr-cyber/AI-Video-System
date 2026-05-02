"""[SPEC-D-001] Phase Artifact Authority Map registry.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Phase Artifact Authority Map"
"""

from __future__ import annotations

from typing import Any, Dict, Final

# Each entry: producer_phase, producer_agent, consumer_phases, consumer_agents,
# schema_ref, acceptance_reviewer.
_FIELDS = (
    "producer_phase",
    "producer_agent",
    "consumer_phases",
    "consumer_agents",
    "schema_ref",
    "acceptance_reviewer",
)

ARTIFACT_AUTHORITY: Final[Dict[str, Dict[str, Any]]] = {
    "requirements.json": {
        "producer_phase": "P0",
        "producer_agent": "RequirementsAgent",
        "consumer_phases": [
            "P1",
            "P2",
            "P3",
            "P4",
            "P5",
            "P6",
            "P7",
            "P8",
            "P9",
            "P10",
            "P11",
        ],
        "consumer_agents": [
            "OutlineAgent",
            "ScriptAgent",
            "PolishAgent",
            "TTSAgent",
            "BGMAgent",
            "SFXAgent",
            "StoryboardAgent",
            "KeyframeRenderAgent",
            "BRollAgent",
            "RoughCutAgent",
            "FinalCutAgent",
        ],
        "schema_ref": "SPEC-A SPEC-0A.1",
        "acceptance_reviewer": "CompletenessReviewer",
    },
    "outline": {
        "producer_phase": "P1",
        "producer_agent": "OutlineAgent",
        "consumer_phases": ["P2"],
        "consumer_agents": ["ScriptAgent"],
        "schema_ref": "SPEC-D SPEC-9.1.1",
        "acceptance_reviewer": "StructureReviewer",
    },
    "polished_script": {
        "producer_phase": "P3",
        "producer_agent": "PolishAgent",
        "consumer_phases": ["P4", "P7", "P10"],
        "consumer_agents": ["TTSAgent", "StoryboardAgent", "SubtitleAgent"],
        "schema_ref": "SPEC-D SPEC-9.3.1",
        "acceptance_reviewer": "StyleReviewer",
    },
    "timeline.json": {
        "producer_phase": "P4",
        "producer_agent": "TTSAgent",
        "consumer_phases": ["P7", "P10", "F"],
        "consumer_agents": ["StoryboardAgent", "RoughCutAgent", "SubtitleAgent"],
        "schema_ref": "SPEC-A SPEC-0A.1",
        "acceptance_reviewer": "AudioQualityReviewer",
    },
    "style_lock.json": {
        "producer_phase": "P7",
        "producer_agent": "StoryboardAgent",
        "consumer_phases": ["P8", "F"],
        "consumer_agents": ["KeyframeRenderAgent", "ThemeConfig"],
        "schema_ref": "SPEC-A SPEC-0A.1",
        "acceptance_reviewer": "StoryboardReviewer",
    },
    "keyframe_renders": {
        "producer_phase": "P8",
        "producer_agent": "KeyframeRenderAgent",
        "consumer_phases": ["P10"],
        "consumer_agents": ["RoughCutAgent"],
        "schema_ref": "SPEC-D SPEC-9.8.1",
        "acceptance_reviewer": "VisualReviewer",
    },
    "rough_cut": {
        "producer_phase": "P10",
        "producer_agent": "RoughCutAgent",
        "consumer_phases": ["P11"],
        "consumer_agents": ["FinalCutAgent"],
        "schema_ref": "SPEC-D SPEC-9.10.1",
        "acceptance_reviewer": "AVSyncReviewer",
    },
    "final_cut": {
        "producer_phase": "P11",
        "producer_agent": "FinalCutAgent",
        "consumer_phases": [],
        "consumer_agents": ["User"],
        "schema_ref": "SPEC-D SPEC-9.11.1",
        "acceptance_reviewer": "FinalReviewer",
    },
    "emotion_curve.json": {
        "producer_phase": "P5",
        "producer_agent": "BGMAgent",
        "consumer_phases": ["P10"],
        "consumer_agents": ["RoughCutAgent"],
        "schema_ref": "SPEC-D SPEC-9.5.1",
        "acceptance_reviewer": "MusicFitReviewer",
    },
}


def lookup_artifact(name: str) -> Dict[str, Any]:
    """Return the authority record for *name*, or raise KeyError."""
    return dict(ARTIFACT_AUTHORITY[name])


__all__ = ["ARTIFACT_AUTHORITY", "lookup_artifact"]
