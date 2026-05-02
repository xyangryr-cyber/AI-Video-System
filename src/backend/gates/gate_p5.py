"""[SPEC-D-005 + SPEC-D-019] Gate-P5: validates P5 outputs before advancing to P6.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.5.6, SPEC-9.5.3 (v3.17)
"""

from __future__ import annotations

from typing import Any


class GateP5:
    """Check: BGM JSON + file exist, MusicFitReviewer PASS, no pending tasks,
    preferences confirmed. When skipped, only checks pending tasks + prefs.
    v3.17 (D-019): 6 additional checks + no_bgm path."""

    @staticmethod
    def check(
        *,
        skipped: bool,
        bgm_exists: bool,
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

        if not bgm_exists:
            failed.append("BGM JSON/file missing or not playable")
        else:
            passed.append("BGM exists and playable")

        if not reviewer_passed:
            failed.append("MusicFitReviewer FAIL")
        else:
            passed.append("MusicFitReviewer PASS")

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

    # -- v3.17 extension (D-019) --

    @staticmethod
    def check_v317(
        *,
        no_bgm: bool = False,
        bgm_mix_preview_exists: bool = False,
        user_selected: bool = False,
        master_file_ready: bool = False,
        master_playable: bool = False,
        source_ref_valid: bool = False,
        master_audio_ref_switched: bool = False,
        reviewer_passed: bool = False,
    ) -> dict[str, Any]:
        if no_bgm:
            return {
                "passed": True,
                "failed_checks": [],
                "passed_checks": ["no_bgm path"],
            }

        failed: list[str] = []
        passed: list[str] = []

        if not bgm_mix_preview_exists:
            failed.append("BGM mix preview missing")
        else:
            passed.append("mix preview exists")

        if not user_selected:
            failed.append("user has not selected BGM")
        else:
            passed.append("user selected")

        if not master_file_ready:
            failed.append("bgm_mix_master file not ready")
        else:
            passed.append("master file ready")

        if not master_playable:
            failed.append("bgm_mix_master not playable")
        else:
            passed.append("master playable")

        if not source_ref_valid:
            failed.append("source_ref chain invalid")
        else:
            passed.append("source_ref valid")

        if not master_audio_ref_switched:
            failed.append("master_audio_ref not switched")
        else:
            passed.append("master_audio_ref switched")

        if not reviewer_passed:
            failed.append("MusicFitReviewer v3.17 FAIL")
        else:
            passed.append("MusicFitReviewer PASS")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
