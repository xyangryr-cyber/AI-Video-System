"""[SPEC-C-009] Producer Agent prompt template.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.1.

The template exposes EXACTLY 7 mandatory placeholders. Rendering with any
field missing (or empty) raises :class:`MissingTemplateFieldError` -- a
soft fallback would let an incomplete prompt reach the LLM, which is the
exact failure mode SPEC-5.1 is written to prevent.
"""

from __future__ import annotations

from typing import Final


class MissingTemplateFieldError(ValueError):
    """A mandatory SPEC-5.1 field is absent or empty at render time."""


PRODUCER_MANDATORY_FIELDS: Final[tuple[str, ...]] = (
    "role_name",
    "task_description",
    "input_artifacts",
    "output_schema",
    "user_preferences",
    "quality_criteria",
    "prohibitions",
)


PRODUCER_TEMPLATE: Final[str] = (
    "# Producer Agent\n"
    "\n"
    "## Role\n"
    "{role_name}\n"
    "\n"
    "## Task\n"
    "{task_description}\n"
    "\n"
    "## Input Artifacts\n"
    "{input_artifacts}\n"
    "\n"
    "## Output Schema\n"
    "{output_schema}\n"
    "\n"
    "## User Preferences\n"
    "{user_preferences}\n"
    "\n"
    "## Quality Criteria\n"
    "{quality_criteria}\n"
    "\n"
    "## Prohibitions\n"
    "{prohibitions}\n"
)


def render_producer_prompt(
    *,
    role_name: str = "",
    task_description: str = "",
    input_artifacts: str = "",
    output_schema: str = "",
    user_preferences: str = "",
    quality_criteria: str = "",
    prohibitions: str = "",
) -> str:
    """Render the SPEC-5.1 Producer prompt from the 7 mandatory fields.

    An empty or whitespace-only value is treated as missing: SPEC-5.1's
    invariant is that every slot reaches the LLM with real content, not a
    structural placeholder.
    """
    values = {
        "role_name": role_name,
        "task_description": task_description,
        "input_artifacts": input_artifacts,
        "output_schema": output_schema,
        "user_preferences": user_preferences,
        "quality_criteria": quality_criteria,
        "prohibitions": prohibitions,
    }
    missing = [
        field
        for field in PRODUCER_MANDATORY_FIELDS
        if not isinstance(values[field], str) or not values[field].strip()
    ]
    if missing:
        raise MissingTemplateFieldError(f"missing mandatory Producer prompt field(s): {missing}")
    return PRODUCER_TEMPLATE.format(**values)


__all__ = [
    "MissingTemplateFieldError",
    "PRODUCER_MANDATORY_FIELDS",
    "PRODUCER_TEMPLATE",
    "render_producer_prompt",
]
