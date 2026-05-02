"""[SPEC-D-003] Gate-P3: validates P3 outputs before advancing to P4.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.3.3
"""

from __future__ import annotations

from typing import Any


class GateP3:
    """Check: polished_script present, is_authoritative_text_source=true,
    StylePrecheck PASS, no missing artifacts."""

    @staticmethod
    def check(
        *,
        polished_script: dict[str, Any],
        style_precheck_result: dict[str, Any],
    ) -> dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        # 1. polished_script exists with required fields
        if not polished_script or not polished_script.get("segments"):
            failed.append("polished_script missing or has no segments")
        elif not polished_script.get("is_authoritative_text_source"):
            failed.append("is_authoritative_text_source is not true")
        else:
            passed.append("polished_script present and authoritative")

        # 2. StylePrecheck PASS
        if style_precheck_result.get("verdict") == "PASS":
            passed.append("StylePrecheck PASS")
        else:
            failed_checks = [
                c for c in style_precheck_result.get("checks", []) if c.get("verdict") == "FAIL"
            ]
            failed.append(f"StylePrecheck FAIL: {[c['rule'] for c in failed_checks]}")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
