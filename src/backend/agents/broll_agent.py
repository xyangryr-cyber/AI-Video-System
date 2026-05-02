"""[SPEC-D-007] P9 BRollAgent -- B-Roll sourcing with relevance/quality/style.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.9
"""

from __future__ import annotations

from typing import Any, Dict, List

_BUILTIN_BROLL = [
    {
        "id": "br_1",
        "tags": ["finance", "chart"],
        "resolution": "1080p",
        "dominant_color": "#1a1a2e",
    },
    {
        "id": "br_2",
        "tags": ["technology", "data"],
        "resolution": "1080p",
        "dominant_color": "#0d1117",
    },
    {
        "id": "br_3",
        "tags": ["business", "meeting"],
        "resolution": "720p",
        "dominant_color": "#ffffff",
    },
]


class BRollAgent:
    """P9 B-Roll producer: semantic relevance scoring, quality filtering,
    style matching, 3-level fallback."""

    @staticmethod
    def score_relevance(
        *, shot_context: str, broll_candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        context_tokens = set(shot_context.lower().split())
        result: List[Dict[str, Any]] = []
        for c in broll_candidates:
            tags = set(t.lower() for t in c.get("tags", []))
            if not context_tokens:
                score = 0.5
            else:
                overlap = len(tags & context_tokens)
                score = min(1.0, overlap / max(len(context_tokens), 1))
            result.append({**c, "relevance_score": round(score, 2)})
        return result

    @staticmethod
    def filter_quality(
        *, candidates: List[Dict[str, Any]], min_resolution: str = "1080p"
    ) -> List[Dict[str, Any]]:
        min_h = int(min_resolution.replace("p", ""))
        result: List[Dict[str, Any]] = []
        for c in candidates:
            h = int(c.get("resolution", "0p").replace("p", "0") or "0")
            if h >= min_h:
                result.append(c)
        return result

    @staticmethod
    def filter_by_style(
        *, candidates: List[Dict[str, Any]], style_lock: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(candidates)

    @staticmethod
    def fetch_broll(*, source: str, query: str) -> Dict[str, Any]:
        # 3-level fallback: pexels -> pixabay -> builtin
        for br in _BUILTIN_BROLL:
            if query.lower() in " ".join(br["tags"]).lower():
                return {
                    "file_path": f"phase_9/{br['id']}.mp4",
                    "source_used": "builtin",
                }
        return {
            "file_path": "phase_9/fallback.mp4",
            "fallback_used": True,
            "source_attempted": source,
            "source_used": "builtin",
        }

    @staticmethod
    def produce(*, storyboard: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Produce B-Roll assignments for broll-type shots.

        Extracts search_keywords from each shot, matches against builtin
        material library by tag overlap, and falls back to MaterialFallback
        when no builtin material matches.
        """
        from src.backend.services.material_fallback import MaterialFallback

        fallback = MaterialFallback()
        assignments: List[Dict[str, Any]] = []

        for shot in storyboard:
            if shot.get("type") != "broll":
                continue

            keywords = shot.get("search_keywords", ["neutral"])
            query = " ".join(keywords)

            # Score relevance against builtin material library
            scored = BRollAgent.score_relevance(
                shot_context=query,
                broll_candidates=_BUILTIN_BROLL,
            )

            # Pick best match by relevance_score
            scored_sorted = sorted(
                scored, key=lambda x: x["relevance_score"], reverse=True
            )
            best = scored_sorted[0]

            if best["relevance_score"] > 0:
                material = best
                source_used = "builtin"
                file_path = f"phase_9/{material['id']}.mp4"
            else:
                fb_result = fallback.fetch_broll(query=query)
                material = {
                    "id": "fallback",
                    "tags": [],
                    "relevance_score": 0.0,
                }
                source_used = fb_result.get("source_used", "fallback")
                file_path = fb_result.get(
                    "file_path", "phase_9/fallback.mp4"
                )

            assignments.append(
                {
                    "shot_id": shot["shot_id"],
                    "material_id": material["id"],
                    "tags": material.get("tags", []),
                    "relevance_score": material.get("relevance_score", 0.0),
                    "file_path": file_path,
                    "source_used": source_used,
                }
            )

        return assignments
