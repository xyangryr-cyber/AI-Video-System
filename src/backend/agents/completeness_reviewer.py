"""[SPEC-D-002] P0 CompletenessReviewer -- validates requirements.json.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.0.2

Stateless, pure-function reviewer. Does NOT import from the reviewers
package (avoids known circular import in reviewers/__init__.py).
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet

_VALID_DURATION_CLASSES: FrozenSet[str] = frozenset({"short", "medium", "long"})

_VALID_LEVEL1: FrozenSet[str] = frozenset(
    {"finance", "tech", "education", "news", "lifestyle", "business"}
)

_VALID_LEVEL2: Dict[str, FrozenSet[str]] = {
    "finance": frozenset(
        {
            "stock_market",
            "cryptocurrency",
            "real_estate",
            "personal_finance",
            "macroeconomics",
            "commodities",
        }
    ),
    "tech": frozenset(
        {
            "ai_ml",
            "consumer_electronics",
            "software",
            "semiconductors",
            "ev_energy",
            "biotech",
        }
    ),
    "education": frozenset(
        {"k12", "higher_ed", "vocational", "online_learning", "stem"}
    ),
    "news": frozenset({"breaking", "analysis", "commentary", "investigation", "recap"}),
    "lifestyle": frozenset({"health", "food", "travel", "fashion", "home"}),
    "business": frozenset({"startup", "management", "marketing", "supply_chain", "hr"}),
}

_VALID_TEMPLATES: FrozenSet[str] = frozenset(
    {"chronological", "progressive", "comparative", "problem_solution", "storytelling"}
)


class CompletenessReviewer:
    """Validate requirements.json fields per SPEC-9.0.2 FAIL conditions.

    Stateless -- no instance state. ``review()`` is a pure function.
    """

    def review(self, req: Dict[str, Any]) -> Dict[str, Any]:
        notes: list[str] = []
        blocking: list[str] = []

        # 1. topic empty or < 5 chars
        topic = req.get("topic", "")
        if len(topic) < 5:
            blocking.append(f"topic too short ({len(topic)} chars, min 5)")

        # 2. duration_class not in {short, medium, long}
        dc = req.get("duration_class", "")
        if dc not in _VALID_DURATION_CLASSES:
            blocking.append(f"invalid duration_class: {dc!r}")

        # 3. target_word_count range validation
        wc = req.get("target_word_count", {})
        wc_min = wc.get("min", 0)
        wc_max = wc.get("max", 0)
        if wc_min <= 0:
            blocking.append(f"target_word_count.min <= 0 ({wc_min})")
        if wc_max <= wc_min:
            blocking.append(f"target_word_count.max ({wc_max}) <= min ({wc_min})")
        if wc_max > 100000:
            blocking.append(f"target_word_count.max > 100000 ({wc_max})")

        # 4. no valid platform
        platform = req.get("platform", "")
        if not platform:
            blocking.append("no valid platform")

        # 5. resolution/bitrate/format
        resolution = req.get("resolution", "")
        bitrate = req.get("bitrate", "")
        fmt = req.get("format", "")
        if not resolution:
            blocking.append("resolution is empty")
        if not bitrate:
            blocking.append("bitrate is empty")
        if not fmt:
            blocking.append("format is empty")

        # 6. category.level1 valid enum + level2 mapping
        category = req.get("category", {})
        level1 = category.get("level1", "")
        level2 = category.get("level2", "")
        if level1 not in _VALID_LEVEL1:
            blocking.append(f"invalid category.level1: {level1!r}")
        elif level2 not in _VALID_LEVEL2.get(level1, frozenset()):
            blocking.append(
                f"category.level2 {level2!r} not valid for level1 {level1!r}"
            )

        # 7. narrative_template valid
        tmpl = req.get("narrative_template", "")
        if tmpl not in _VALID_TEMPLATES:
            blocking.append(f"invalid narrative_template: {tmpl!r}")

        verdict = "FAIL" if blocking else "PASS"
        if verdict == "PASS":
            notes.append("All 7 checks passed")

        return {
            "verdict": verdict,
            "notes": notes,
            "blocking_issues": blocking,
        }
