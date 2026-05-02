"""[SPEC-D-003] P3 StylePrecheck -- 8-rule L1 pure-code style validator.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.3.2 (Gate-P3 L1 checks)

All 8 rules are pure Python -- 0 LLM tokens, 0 network calls.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Banned words list per SPEC (17 words)
_BANNED_WORDS: frozenset[str] = frozenset(
    {
        "绝对",
        "保证",
        "必买",
        "必赚",
        "稳赚",
        "翻倍",
        "暴涨",
        "暴跌",
        "抄底",
        "千载难逢",
        "错过后悔",
        "内幕",
        "独家",
        "必涨",
        "涨停",
        "跌停",
        "零风险",
    }
)

# Chinese modal particles
_MODAL_PARTICLES: frozenset[str] = frozenset(
    "吧呢吗啊哦呀哈哇啦咧呗呐嘛呵哎唉嗨嘻呵".split()
)

# Person markers
_FIRST_PERSON: frozenset[str] = frozenset({"我", "我们", "咱", "咱们"})
_THIRD_PERSON: frozenset[str] = frozenset({"他", "她", "它", "他们", "她们", "它们"})


class StylePrecheck:
    """8-rule L1 style precheck for polished script (pure code, no LLM)."""

    @staticmethod
    def review(
        segments: List[Dict[str, Any]],
        *,
        outline: Dict[str, Any],
        original_script: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        # 1. Person consistency
        checks.append(StylePrecheck._check_person_consistency(segments))

        # 2. Modal particle frequency [0.5, 3.0] per 100 chars
        checks.append(StylePrecheck._check_modal_particles(segments))

        # 3. Sentence length <= 80 chars
        checks.append(StylePrecheck._check_sentence_length(segments))

        # 4. Paragraph length <= 300 chars (WARNING only)
        checks.append(StylePrecheck._check_paragraph_length(segments))

        # 5. Banned words
        checks.append(StylePrecheck._check_banned_words(segments))

        # 6. Word count deviation <= 5% from original
        checks.append(
            StylePrecheck._check_word_count_deviation(segments, original_script)
        )

        # 7. Viewpoint coverage (all outline sections covered)
        checks.append(StylePrecheck._check_viewpoint_coverage(segments, outline))

        # 8. Data point ID set preservation
        checks.append(
            StylePrecheck._check_data_point_preservation(segments, original_script)
        )

        verdict = "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS"
        return {"verdict": verdict, "checks": checks}

    # ---- per-rule helpers ----

    @staticmethod
    def _check_person_consistency(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        has_first = False
        has_third = False
        for seg in segments:
            text = seg.get("content", "")
            if any(m in text for m in _FIRST_PERSON):
                has_first = True
            if any(m in text for m in _THIRD_PERSON):
                has_third = True
        if has_first and has_third:
            return {
                "rule": "person_consistency",
                "verdict": "FAIL",
                "detail": "mixed first-person and third-person references",
            }
        return {"rule": "person_consistency", "verdict": "PASS"}

    @staticmethod
    def _check_modal_particles(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_chars = 0
        modal_count = 0
        for seg in segments:
            text = seg.get("content", "")
            total_chars += len(text)
            modal_count += sum(1 for ch in text if ch in _MODAL_PARTICLES)
        if total_chars == 0:
            return {"rule": "modal_particle_frequency", "verdict": "PASS"}
        freq_per_100 = (modal_count / total_chars) * 100
        if freq_per_100 < 0.5 or freq_per_100 > 3.0:
            return {
                "rule": "modal_particle_frequency",
                "verdict": "FAIL",
                "detail": f"modal particle frequency {freq_per_100:.2f}/100chars (range [0.5, 3.0])",
            }
        return {"rule": "modal_particle_frequency", "verdict": "PASS"}

    @staticmethod
    def _check_sentence_length(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        for seg in segments:
            text = seg.get("content", "")
            # Split on Chinese sentence terminators
            sentences = _split_sentences(text)
            for s in sentences:
                if len(s) > 80:
                    return {
                        "rule": "sentence_length",
                        "verdict": "FAIL",
                        "detail": f"sentence exceeds 80 chars: {s[:40]}...",
                    }
        return {"rule": "sentence_length", "verdict": "PASS"}

    @staticmethod
    def _check_paragraph_length(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        for seg in segments:
            text = seg.get("content", "")
            if len(text) > 300:
                return {
                    "rule": "paragraph_length",
                    "verdict": "PASS",
                    "detail": f"paragraph {len(text)} chars exceeds 300 (WARNING only)",
                }
        return {"rule": "paragraph_length", "verdict": "PASS"}

    @staticmethod
    def _check_banned_words(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        found: List[str] = []
        for seg in segments:
            text = seg.get("content", "")
            for word in _BANNED_WORDS:
                if word in text:
                    found.append(word)
        if found:
            return {
                "rule": "banned_words",
                "verdict": "FAIL",
                "detail": f"banned words found: {found}",
            }
        return {"rule": "banned_words", "verdict": "PASS"}

    @staticmethod
    def _check_word_count_deviation(
        segments: List[Dict[str, Any]],
        original_script: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        orig_wc = sum(s.get("word_count", 0) for s in original_script)
        new_wc = sum(s.get("word_count", 0) for s in segments)
        if orig_wc == 0:
            return {"rule": "word_count_deviation", "verdict": "PASS"}
        deviation = abs(new_wc - orig_wc) / orig_wc
        if deviation > 0.05:
            return {
                "rule": "word_count_deviation",
                "verdict": "FAIL",
                "detail": f"word count deviation {deviation:.2%} exceeds 5%",
            }
        return {"rule": "word_count_deviation", "verdict": "PASS"}

    @staticmethod
    def _check_viewpoint_coverage(
        segments: List[Dict[str, Any]],
        outline: Dict[str, Any],
    ) -> Dict[str, Any]:
        outline_sections = {s.get("section_id") for s in outline.get("sections", [])}
        covered = {s.get("outline_section_ref") for s in segments}
        if outline_sections and not outline_sections.issubset(covered):
            missing = outline_sections - covered
            return {
                "rule": "viewpoint_coverage",
                "verdict": "FAIL",
                "detail": f"sections not covered: {missing}",
            }
        return {"rule": "viewpoint_coverage", "verdict": "PASS"}

    @staticmethod
    def _check_data_point_preservation(
        segments: List[Dict[str, Any]],
        original_script: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        orig_ids: set[str] = set()
        for s in original_script:
            for dp in s.get("key_data_points", []):
                orig_ids.add(dp.get("data_point_id", ""))

        new_ids: set[str] = set()
        for s in segments:
            for dp in s.get("key_data_points", []):
                new_ids.add(dp.get("data_point_id", ""))

        if not orig_ids:
            return {"rule": "data_point_preservation", "verdict": "PASS"}

        if orig_ids != new_ids:
            missing = orig_ids - new_ids
            extra = new_ids - orig_ids
            return {
                "rule": "data_point_preservation",
                "verdict": "FAIL",
                "detail": f"data point ID drift: missing={missing}, extra={extra}",
            }
        return {"rule": "data_point_preservation", "verdict": "PASS"}


def _split_sentences(text: str) -> List[str]:
    """Split Chinese text into sentences on common terminators."""
    result: List[str] = []
    current: List[str] = []
    terminators = {"。", "！", "？", "；", "，", "、"}
    for ch in text:
        current.append(ch)
        if ch in terminators:
            result.append("".join(current))
            current = []
    if current:
        result.append("".join(current))
    return result if result else [text]
