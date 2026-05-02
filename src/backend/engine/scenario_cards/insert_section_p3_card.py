"""[SPEC-D-102] InsertSectionP3Card — P3 insert_section scenario card.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-3

Handles insert_section at P3 (polished script phase):
- Same logic as P2: generate new segment_id, run DiffAuditor, gate verdict
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List


class InsertSectionP3Card:
    """Scenario card for P3 insert_section actions."""

    MAX_UNRELATED_RATIO = 0.05

    def handle_insert(
        self,
        *,
        old_segments: List[Dict[str, Any]],
        after_segment_id: str,
        content_intent: str,
    ) -> Dict[str, Any]:
        """Handle insert_section at P3: create new segment, run DiffAuditor, return gate result."""

        seg_hash = hashlib.sha256(
            f"{after_segment_id}:{content_intent}".encode("utf-8")
        ).hexdigest()[:10]
        new_segment_id = f"seg_new_{seg_hash}"

        new_segment: Dict[str, Any] = {
            "segment_id": new_segment_id,
            "text": f"[POLISHED INSERT] {content_intent}",
            "section_title": "",
            "word_count": len(content_intent.split()),
        }

        insert_idx = None
        for i, seg in enumerate(old_segments):
            if seg["segment_id"] == after_segment_id:
                insert_idx = i + 1
                break

        if insert_idx is None:
            insert_idx = len(old_segments)

        new_segments = list(old_segments)
        new_segments.insert(insert_idx, new_segment)

        allowed_modify = [new_segment_id]
        diff_result = self._run_diff_audit(
            old_segments=old_segments,
            new_segments=new_segments,
            allowed_modify_segments=allowed_modify,
        )

        return {
            "new_segment": new_segment,
            "is_new_segment": True,
            "diff_verdict": diff_result["verdict"],
            "unrelated_change_ratio": diff_result["unrelated_change_ratio"],
            "gate_passed": diff_result["verdict"] == "PASS",
            "insertion_index": insert_idx,
        }

    def _run_diff_audit(
        self,
        *,
        old_segments: List[Dict[str, Any]],
        new_segments: List[Dict[str, Any]],
        allowed_modify_segments: List[str],
    ) -> Dict[str, Any]:
        allowed = set(allowed_modify_segments)
        total = len(old_segments)

        if total == 0:
            return {"verdict": "PASS", "unrelated_change_ratio": 0.0}

        old_map = {s["segment_id"]: s for s in old_segments}
        new_map = {s["segment_id"]: s for s in new_segments}

        unrelated_count = 0
        for seg_id, old_seg in old_map.items():
            if seg_id in allowed:
                continue
            new_seg = new_map.get(seg_id)
            if new_seg is None:
                unrelated_count += 1
            elif old_seg.get("text", "") != new_seg.get("text", ""):
                unrelated_count += 1

        ratio = unrelated_count / total
        verdict = "PASS" if ratio <= self.MAX_UNRELATED_RATIO + 1e-12 else "FAIL"

        return {
            "verdict": verdict,
            "unrelated_change_ratio": round(ratio, 4),
        }


__all__ = ["InsertSectionP3Card"]
