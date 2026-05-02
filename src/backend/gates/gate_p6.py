"""[SPEC-D-005 + SPEC-D-020] Gate-P6: validates P6 outputs before advancing to P7.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.6.6, v3.17 update
"""

from __future__ import annotations

from typing import Any


class GateP6:
    """Check: SFX JSON + files exist, SFXReviewer PASS, no pending tasks,
    preferences confirmed. When skipped, only checks pending tasks + prefs.
    v3.17 (D-020): final_audio_master checks + segment mix completeness."""

    @staticmethod
    def check(
        *,
        skipped: bool,
        sfx_exists: bool,
        reviewer_passed: bool,
        pending_tasks: list[Any],
        preferences_confirmed: bool,
    ) -> dict[str, Any]:
        if skipped:
            failed_pending = bool(pending_tasks)
            failed_prefs = not preferences_confirmed
            return {
                "passed": not failed_pending and not failed_prefs,
                "failed_checks": ([f"{len(pending_tasks)} pending tasks"] if failed_pending else [])
                + (["preferences not confirmed"] if failed_prefs else []),
                "passed_checks": (["no pending tasks"] if not failed_pending else [])
                + (["preferences confirmed"] if not failed_prefs else []),
            }

        failed: list[str] = []
        passed: list[str] = []

        if not sfx_exists:
            failed.append("SFX JSON/files missing or not playable")
        else:
            passed.append("SFX exists and playable")

        if not reviewer_passed:
            failed.append("SFXReviewer FAIL")
        else:
            passed.append("SFXReviewer PASS")

        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks")
        else:
            passed.append("no pending tasks")

        if not preferences_confirmed:
            failed.append("preferences not confirmed")
        else:
            passed.append("preferences confirmed")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }

    # -- v3.17 extension (D-020) --

    @staticmethod
    def check_v317(
        *,
        final_audio_master_exists: bool = False,
        master_playable: bool = False,
        checksum_consistent: bool = False,
        source_ref_valid: bool = False,
        reviewer_passed: bool = False,
        segment_mix_complete: bool = False,
    ) -> dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not final_audio_master_exists:
            failed.append("final_audio_master missing")
        else:
            passed.append("final_audio_master exists")
        if not master_playable:
            failed.append("master not playable")
        else:
            passed.append("master playable")
        if not checksum_consistent:
            failed.append("checksum inconsistent")
        else:
            passed.append("checksum consistent")
        if not source_ref_valid:
            failed.append("source_ref invalid")
        else:
            passed.append("source_ref valid")
        if not reviewer_passed:
            failed.append("SFXReviewer FAIL")
        else:
            passed.append("SFXReviewer PASS")
        if not segment_mix_complete:
            pass  # non-blocking advisory
        else:
            passed.append("segment mix complete")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
