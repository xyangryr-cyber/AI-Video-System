"""[SPEC-D-002] OutlineAgent schema coercion tests.

Verifies that OutlineLLMOutput._coerce_versions() correctly maps
LLM field aliases (beat/narrative/beats) to the schema's canonical
field names (type/key_points/narrative_beats).
"""

from __future__ import annotations

from src.backend.agents.schemas import OutlineLLMOutput


class TestSchemaCoercion:
    """Verify schema coercion maps LLM field aliases."""

    def test_coerce_beats_maps_beats_to_narrative_beats(self):
        data = {
            "versions": [{
                "version_id": "vA",
                "viewpoint": "chronological",
                "beats": [{
                    "beat": "hook",
                    "title": "Test Beat Title",
                    "narrative": "Actual narrative content here",
                    "start_seconds": 0,
                    "end_seconds": 120,
                }],
            }],
        }
        result = OutlineLLMOutput.model_validate(data)
        beat = result.versions[0].narrative_beats[0]
        assert beat.type == "hook"
        assert beat.key_points == ["Actual narrative content here"]

    def test_coerce_dict_versions_to_list(self):
        data = {
            "versions": {
                "vA": {
                    "viewpoint": "chronological",
                    "narrative_beats": [{
                        "type": "hook",
                        "title": "Test",
                        "start_seconds": 0,
                        "end_seconds": 120,
                    }],
                },
                "vB": {
                    "viewpoint": "progressive",
                    "narrative_beats": [{
                        "type": "context",
                        "title": "Test 2",
                        "start_seconds": 120,
                        "end_seconds": 240,
                    }],
                },
            },
        }
        result = OutlineLLMOutput.model_validate(data)
        assert len(result.versions) == 2
        version_ids = {v.version_id for v in result.versions}
        assert version_ids == {"vA", "vB"}
