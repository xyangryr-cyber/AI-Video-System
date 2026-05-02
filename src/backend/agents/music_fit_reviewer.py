"""[SPEC-D-005] P5 MusicFitReviewer -- L1 (0 token) + L2 (LLM) BGM review.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.5.5

Placed outside reviewers/ to avoid circular import.
"""

from __future__ import annotations

from typing import Any

_VALID_COPYRIGHT_TAGS = frozenset({"CC0", "CC-BY", "proprietary"})


class MusicFitReviewer:
    """Review BGM fit: L1 (duration, volume, copyright) + L2 (emotion matching)."""

    BODY_VOLUME_MAX_DB = -18

    @staticmethod
    def review_l1(
        *,
        bgm_duration: float,
        video_duration: float,
        volume_db: float,
        copyright_tag: str,
    ) -> dict[str, Any]:
        blocking: list[str] = []

        if bgm_duration < video_duration:
            blocking.append(f"BGM duration ({bgm_duration}s) < video duration ({video_duration}s)")
        if volume_db > MusicFitReviewer.BODY_VOLUME_MAX_DB:
            blocking.append(
                f"BGM volume ({volume_db}dB) exceeds body max ({MusicFitReviewer.BODY_VOLUME_MAX_DB}dB)"
            )
        if copyright_tag not in _VALID_COPYRIGHT_TAGS:
            blocking.append(f"Invalid copyright tag: {copyright_tag!r}")

        verdict = "FAIL" if blocking else "PASS"
        return {"verdict": verdict, "blocking_issues": blocking}

    @classmethod
    def review(
        cls,
        *,
        bgm_duration: float,
        video_duration: float,
        volume_db: float,
        copyright_tag: str,
        emotion_curve: dict[str, Any],
    ) -> dict[str, Any]:
        l1 = cls.review_l1(
            bgm_duration=bgm_duration,
            video_duration=video_duration,
            volume_db=volume_db,
            copyright_tag=copyright_tag,
        )

        l2_called = False
        l2_result = None
        if l1["verdict"] == "PASS":
            # L2: LLM-backed emotion matching (stub in V1)
            l2_called = True
            l2_result = {"verdict": "PASS", "note": "L2 emotion matching stub"}

        return {
            "verdict": l1["verdict"] if not l2_called else "PASS",
            "l1_result": l1,
            "l2_result": l2_result,
            "l2_called": l2_called,
        }
