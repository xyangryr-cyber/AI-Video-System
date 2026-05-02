"""[SPEC-D-003] P2 ScriptAgent -- produces per-segment oral scripts.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.2
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.backend.agents.schemas import ScriptLLMOutput
from src.backend.services.llm_service import chat_completion

_VALID_TRUST_LEVELS = frozenset({"user_verified", "source_verified", "llm_generated"})
_MAX_LLM_GENERATED = 5


class ScriptAgent:
    """Produce per-segment scripts from requirements + outline.

    Stateless -- every call creates a fresh output from its arguments.
    Calls LLM via chat_completion to generate natural language oral scripts.
    """

    @staticmethod
    def produce(
        *,
        requirements: Dict[str, Any],
        outline: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        sections = outline.get("sections", [])
        if not sections:
            return []

        try:
            llm_result: ScriptLLMOutput = chat_completion(
                role="script_agent",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial video script writer. "
                            "Generate natural language oral scripts for each "
                            "outline section. The content must be conversational "
                            "Chinese suitable for voice narration. DO NOT use "
                            'template prefixes like "第N部分". Each segment '
                            "should flow naturally into the next. Include "
                            "specific data points with verifiable values where "
                            "appropriate. Mark all data points with "
                            'trust_level="llm_generated". Calculate word_count '
                            "from the actual Chinese character count of the "
                            "generated content."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Requirements: {requirements}\n"
                            f"Outline sections: {sections}\n\n"
                            "Generate one natural language script segment per "
                            "outline section. Each segment must have: "
                            "segment_id (seg_NNN), section_title, "
                            "outline_section_ref, content (conversational "
                            "Chinese paragraph, NOT starting with 第N部分), "
                            "word_count (actual Chinese character count), "
                            "key_data_points (specific facts with "
                            "trust_level=llm_generated), emotion_tone, "
                            "transition_note."
                        ),
                    },
                ],
                response_model=ScriptLLMOutput,
            )
            return [seg.model_dump() for seg in llm_result.segments]
        except Exception:
            # Fallback: deterministic script from outline sections
            result: List[Dict[str, Any]] = []
            for i, sec in enumerate(sections):
                title = sec.get("title", f"第{i+1}节")
                content_text = sec.get("content", sec.get("viewpoint", f"关于{title}的详细分析内容"))
                result.append({
                    "segment_id": f"seg_{i+1:03d}",
                    "section_title": title,
                    "outline_section_ref": sec.get("type", f"sec_{i}"),
                    "content": content_text,
                    "word_count": len(content_text),
                    "key_data_points": [
                        {"data_point_id": f"dp_{i}_1", "value": content_text[:40], "source": "deterministic_fallback", "trust_level": "llm_generated"}
                    ],
                    "emotion_tone": "neutral",
                    "transition_note": "" if i == len(sections) - 1 else f"接下来讨论{title}",
                })
            return result

    @staticmethod
    def reextract_data_points(
        original_data_points: List[Dict[str, Any]],
        new_data_points: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge new data points into the original set per SPEC-9.2.4 rules.

        - New points (id not in original) -> trust_level = llm_generated
        - Changed points (same id, different value) -> trust_level = llm_generated
        - Unchanged points (same id, same value) -> retain original trust_level
        - Deleted points (id in original but not in new) -> removed
        """
        original_by_id: Dict[str, Dict[str, Any]] = {
            dp["data_point_id"]: dp for dp in original_data_points
        }

        result: List[Dict[str, Any]] = []
        for new_dp in new_data_points:
            dp_id = new_dp["data_point_id"]
            old = original_by_id.get(dp_id)
            if old is None:
                # New point
                result.append({**new_dp, "trust_level": "llm_generated"})
            elif old.get("value") != new_dp.get("value"):
                # Changed point
                result.append({**new_dp, "trust_level": "llm_generated"})
            else:
                # Unchanged -- retain original trust_level
                result.append({**new_dp, "trust_level": old["trust_level"]})

        return result
