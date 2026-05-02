"""[SPEC-F-014] render_result validation — every result must carry error_code.

error_code ∈ {null, 'render_failed', 'material_missing', 'material_unverified'}
Missing error_code → MalformedRenderResultError.
"""

from __future__ import annotations

from typing import Any

_VALID_ERROR_CODES = {None, "render_failed", "material_missing", "material_unverified"}


class MalformedRenderResultError(ValueError):
    """Raised when a render_result is missing the required error_code field."""


def validate_render_result(result: dict[str, Any]) -> None:
    """Validate that result has a valid error_code field.

    Raises MalformedRenderResultError if error_code is missing or invalid.
    """
    if "error_code" not in result:
        raise MalformedRenderResultError(
            f"render_result missing required 'error_code' field: {result}"
        )

    error_code = result["error_code"]
    if error_code not in _VALID_ERROR_CODES:
        raise MalformedRenderResultError(
            f"render_result has invalid error_code={error_code!r}; "
            f"must be one of {_VALID_ERROR_CODES}"
        )
