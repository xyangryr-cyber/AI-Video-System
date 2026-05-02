"""[SPEC-D-002] P1 OutlineAgent -- produces 2-3 outline versions.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.1.1
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from src.backend.agents.schemas import OutlineLLMOutput
from src.backend.services.llm_service import LLMFormatError, chat_completion

log = logging.getLogger(__name__)

_PLACEHOLDER_PATTERNS = [
    r"Key point \d+ for \w+",
    r"\w+ data point \d+",
    r"第\d+部分.*Key point",
    r"Transition from \w+ to \w+",
]

_OUTLINE_MAX_TOKENS = 16384


class OutlineAgent:
    """Produce 2 outline versions with narrative beats.

    Stateless -- every call generates fresh outlines from its arguments.
    Calls LLM via chat_completion; on failure, lets the exception propagate
    so the Dispatcher can retry per PRD §3.3.3 / TECH_PLAN §8.
    """

    def produce(
        self,
        *,
        requirements: Dict[str, Any],
        topic: str,
        duration_seconds: int,
    ) -> Dict[str, Any]:
        try:
            llm_result: OutlineLLMOutput = chat_completion(
                role="outline_agent",
                messages=_build_messages(topic, duration_seconds, requirements),
                response_model=OutlineLLMOutput,
                max_tokens=_OUTLINE_MAX_TOKENS,
            )
        except LLMFormatError:
            log.error(
                "OutlineAgent LLM call failed after all retries",
                extra={"topic": topic[:200], "duration_seconds": duration_seconds},
            )
            raise
        except Exception:
            log.exception(
                "OutlineAgent unexpected error",
                extra={"topic": topic[:200], "duration_seconds": duration_seconds},
            )
            raise

        result = {"versions": [v.model_dump() for v in llm_result.versions]}
        _validate_no_placeholders(result)
        return result


def _build_messages(
    topic: str, duration_seconds: int, requirements: Dict[str, Any]
) -> list[dict]:
    """Build the system + user messages for the outline LLM call."""
    return [
        {
            "role": "system",
            "content": (
                "You are a financial video outline designer. "
                "Generate two narrative outlines (chronological and "
                "progressive) for a financial video. Each outline "
                "must have exactly 5 narrative beats: hook, context, "
                "argument, climax, conclusion.\n\n"
                "CRITICAL: Output ONLY valid JSON matching this schema:\n"
                '{"versions": [\n'
                '  {"version_id": "vA", "viewpoint": "...",\n'
                '   "narrative_beats": [\n'
                '     {"type": "hook", "title": "...", "viewpoint": "...",\n'
                '      "start_seconds": 0, "end_seconds": 120,\n'
                '      "key_points": ["actual narrative sentence in Chinese"],\n'
                '      "supporting_data": ["specific fact: S&P 500 fell 2.3% in 2025 Q3"],\n'
                '      "transition_to_next": "..."}\n'
                '   ]}\n'
                ']}\n'
                "Rules:\n"
                "- key_points must be REAL narrative sentences, "
                "NOT 'Key point N for X'\n"
                "- supporting_data must be SPECIFIC facts with numbers/dates, "
                "NOT 'data point N'\n"
                "- transition_to_next must be real transitions, "
                "NOT 'Transition from X to Y'\n"
                "- The two versions must be genuinely different "
                "in narrative approach"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Topic: {topic}\n"
                f"Duration: {duration_seconds} seconds\n"
                f"Requirements: {requirements}\n\n"
                "Generate two outline versions (vA: chronological, "
                "vB: progressive). Each version must have 5 beats "
                "(hook/context/argument/climax/conclusion). "
                "key_points should be actual narrative content, "
                "supporting_data should contain specific verifiable "
                "data point descriptions. Distribute the total "
                f"duration of {duration_seconds}s across the 5 beats."
            ),
        },
    ]


def _validate_no_placeholders(result: dict) -> None:
    """Reject placeholder text in agent output.

    Complements GateKeeper content_quality checks (PRD §6.3) as a
    first-line defense at the agent level.
    """
    text = json.dumps(result, ensure_ascii=False)
    found: list[str] = []
    for pattern in _PLACEHOLDER_PATTERNS:
        found.extend(re.findall(pattern, text))
    if found:
        raise ValueError(
            f"OutlineAgent output contains {len(found)} placeholder(s): "
            f"{found[:10]}"
        )
