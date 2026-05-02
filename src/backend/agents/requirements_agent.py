"""[SPEC-D-002] P0 RequirementsAgent -- produces requirements.json.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.0.1
"""

from __future__ import annotations

from typing import Any

from src.backend.agents.schemas import RequirementsLLMOutput
from src.backend.services.llm_service import chat_completion
from src.shared.schemas.artifacts import (
    Category,
    PlatformEntry,
    Requirements,
    SubtitlePreferences,
    TargetDuration,
    TargetWordCount,
    VoicePreferences,
)


class RequirementsAgent:
    """Produce requirements.json with all SPEC-9.0.1 fields.

    Stateless -- every call creates a fresh output from its arguments.
    Calls LLM via chat_completion to clarify topic and determine
    voice/subtitle preferences.
    """

    _SPEECH_RATE_BASELINE = 3  # chars per second for Chinese

    def produce(
        self,
        *,
        project_id: str,
        title: str,
        topic: str,
        duration_class: str,
        platform: str,
        category_level1: str,
        category_level2: str,
        narrative_template: str,
        target_duration_seconds: int = 600,
        target_word_count_min: int = 800,
        target_word_count_max: int = 1200,
        voice_preferences: dict[str, Any] | None = None,
        target_platform: str = "web",
        subtitle_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # AC-2: validate word count / duration consistency (+-10%)
        expected_center = target_duration_seconds * self._SPEECH_RATE_BASELINE
        wc_center = (target_word_count_min + target_word_count_max) / 2
        if expected_center > 0:
            error = abs(wc_center - expected_center) / expected_center
            if error > 0.10:
                raise ValueError(
                    f"word_count center ({wc_center:.0f}) deviates from "
                    f"duration-based estimate ({expected_center:.0f}) "
                    f"by {error:.1%} (> 10%)"
                )

        # Call LLM to clarify topic and determine preferences
        llm_result: RequirementsLLMOutput = chat_completion(
            role="requirements_agent",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial video requirements analyst. "
                        "Based on user input topic, output structured "
                        "requirements definition. Do not expand factual "
                        "content, only do structural organization."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {title}\n"
                        f"Topic: {topic}\n"
                        f"Duration class: {duration_class}\n"
                        f"Platform: {platform}\n\n"
                        "Output a clarified topic (structured description, "
                        "not a verbatim copy), voice preferences "
                        "(gender/tone/speed), and subtitle preferences "
                        "(position/font_size)."
                    ),
                },
            ],
            response_model=RequirementsLLMOutput,
        )

        raw = {
            "project_id": project_id,
            "title": title,
            "topic": topic,
            "clarified_topic": llm_result.clarified_topic,
            "duration_class": duration_class,
            "target_duration_seconds": target_duration_seconds,
            "target_word_count": {
                "min": target_word_count_min,
                "max": target_word_count_max,
            },
            "platform": platform,
            "category": {
                "level1": category_level1,
                "level2": category_level2,
            },
            "narrative_template": narrative_template,
            "voice_preferences": llm_result.voice_preferences.model_dump(),
            "target_platform": target_platform,
            "subtitle_preferences": llm_result.subtitle_preferences.model_dump(),
        }
        return self._to_canonical(raw).model_dump()

    @staticmethod
    def _to_canonical(raw: dict[str, Any]) -> Requirements:
        """Transform the agent's flat dict output into a canonical Requirements model.

        Maps flat agent fields to the structured Pydantic types expected
        by the shared artifact schema.
        """
        # 1. TargetDuration: same value for min/max from flat seconds
        dur_sec = raw.get("target_duration_seconds", 600)
        target_duration = TargetDuration(min_sec=dur_sec, max_sec=dur_sec)

        # 2. TargetWordCount: map min/max from nested dict
        wc = raw.get("target_word_count", {})
        target_word_count = TargetWordCount(
            min=wc.get("min", 800),
            max=wc.get("max", 1200),
        )

        # 3. Platform: flat string -> list[PlatformEntry]
        platform_str = raw.get("platform", "web")
        platform_list = [PlatformEntry(platform=platform_str, role="primary")]

        # 4. Category: nested dict -> Category
        cat = raw.get("category", {})
        category = Category(
            level1=cat.get("level1", "finance"),
            level2=cat.get("level2", "general"),
        )

        # 5. VoicePreferences: agent dict -> canonical (voice_id from gender, style from tone)
        vp = raw.get("voice_preferences", {})
        voice_preferences = VoicePreferences(
            voice_id=vp.get("gender", "neutral"),
            style=vp.get("tone", "professional"),
        )

        # 6. SubtitlePreferences: sensible defaults (agent output doesn't map 1:1)
        subtitle_preferences = SubtitlePreferences(
            style="sentence",
            highlight_enabled=True,
        )

        # 7. Assemble the canonical Requirements model
        return Requirements(
            project_id=raw.get("project_id", ""),
            title=raw.get("title", ""),
            topic=raw.get("topic", ""),
            clarified_topic=raw.get("clarified_topic", ""),
            duration_class=raw.get("duration_class", "medium"),
            target_duration_seconds=dur_sec,
            target_duration=target_duration,
            target_word_count=target_word_count,
            platform=platform_list,
            category=category,
            narrative_template=raw.get("narrative_template", "chronological"),
            voice_preferences=voice_preferences,
            subtitle_preferences=subtitle_preferences,
            target_platform=raw.get("target_platform", "web"),
            clarification_needed=raw.get("clarification_needed", []),
        )
