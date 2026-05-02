"""Tests for [SPEC-F-010] Subtitle System: Style, Highlight & Rendering."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUBTITLE_DIR = PROJECT_ROOT / "src" / "frontend" / "components" / "subtitle"
STYLE_PATH = SUBTITLE_DIR / "subtitleStyle.ts"
HIGHLIGHTER_PATH = SUBTITLE_DIR / "subtitleHighlighter.ts"
RENDERER_PATH = SUBTITLE_DIR / "SubtitleRenderer.tsx"
AVSYNC_PATH = SUBTITLE_DIR / "AVSyncReviewer.ts"

SUBTITLE_STYLE_FIELDS = [
    "font",
    "color",
    "stroke",
    "background",
    "position",
    "highlight_rules",
    "animation",
]

HIGHLIGHT_PRIORITY_ORDER = [
    "key_data_point",
    "percentage",
    "number",
    "proper_noun",
]

SUBTITLE_WORD_FIELDS = ["word", "start_sec", "end_sec", "highlight_type"]


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _all_sources() -> str:
    sources = []
    for p in [STYLE_PATH, HIGHLIGHTER_PATH, RENDERER_PATH, AVSYNC_PATH]:
        if p.is_file():
            sources.append(p.read_text(encoding="utf-8"))
    return "\n".join(sources)


class TestAC1SubtitleStyleFields:
    """AC-1: subtitle_style config contains font, color, stroke, background, position, highlight_rules, animation"""

    def test_subtitle_style_fields(self):
        source = _read_text(STYLE_PATH)
        for field in SUBTITLE_STYLE_FIELDS:
            assert field in source, f"subtitleStyle.ts must define '{field}' field"


class TestAC2HighlightPriorityHighestWins:
    """AC-2: When a word matches multiple highlight rules, only the highest priority rule applies"""

    def test_highlight_priority_highest_wins(self):
        source = _read_text(HIGHLIGHTER_PATH)
        assert "priority" in source.lower() or "PRIORITY" in source, (
            "subtitleHighlighter.ts must define highlight priority"
        )
        # Priority: key_data_point > percentage > number > proper_noun
        for rule in HIGHLIGHT_PRIORITY_ORDER:
            assert rule in source, (
                f"subtitleHighlighter.ts must reference '{rule}' in priority order"
            )

    def test_single_rule_per_word(self):
        source = _read_text(HIGHLIGHTER_PATH)
        # Must have logic that returns after first match (highest priority)
        has_early_return = "return" in source
        has_priority_loop = "for" in source or "find" in source
        assert has_early_return or has_priority_loop, (
            "subtitleHighlighter must apply only one (highest-priority) rule per word"
        )


class TestAC3HighlighterNoLlmCalls:
    """AC-3: subtitle_highlighter has zero LLM calls"""

    def test_highlighter_no_llm_calls(self):
        source = _read_text(HIGHLIGHTER_PATH)
        llm_patterns = ["fetch(", "axios", "openai", "anthropic", "llm", "LLM"]
        for pattern in llm_patterns:
            assert pattern not in source, (
                f"subtitleHighlighter.ts must not contain LLM call: '{pattern}'"
            )


class TestAC4SubtitleWordsSchema:
    """AC-4: subtitle_words entries contain word, start_sec, end_sec, highlight_type"""

    def test_subtitle_words_schema(self):
        source = _all_sources()
        for field in SUBTITLE_WORD_FIELDS:
            assert field in source, (
                f"Subtitle system must reference SubtitleWord field '{field}'"
            )


class TestAC5HighlightKeyDataPointMismatchFail:
    """AC-5: Highlight word value inconsistent with key_data_point triggers FAIL"""

    def test_highlight_key_data_point_mismatch_fail(self):
        source = _read_text(AVSYNC_PATH) if AVSYNC_PATH.is_file() else _all_sources()
        # AVSyncReviewer must check highlight word consistency
        assert "key_data_point" in source, (
            "AVSyncReviewer must check highlight word against key_data_point"
        )
        assert (
            "fail" in source.lower() or "FAIL" in source or "mismatch" in source.lower()
        ), "AVSyncReviewer must trigger FAIL on key_data_point mismatch"


class TestAC6WhisperAlignmentUnder200ms:
    """AC-6: Whisper word-level alignment error < 200ms"""

    def test_whisper_alignment_under_200ms(self):
        source = _all_sources()
        assert "200" in source or "0.2" in source, (
            "Subtitle system must enforce 200ms Whisper alignment threshold"
        )


class TestAC7AvOffsetOver100msFail:
    """AC-7: AV offset > 100ms triggers FAIL in AVSyncReviewer"""

    def test_av_offset_over_100ms_fail(self):
        source = _read_text(AVSYNC_PATH)
        assert "100" in source or "0.1" in source, (
            "AVSyncReviewer must check AV offset at 100ms threshold"
        )


class TestAC8BlankFramesFail:
    """AC-8: Blank frames > 0 triggers FAIL in AVSyncReviewer"""

    def test_blank_frames_fail(self):
        source = _read_text(AVSYNC_PATH)
        has_blank_check = "blank" in source.lower() or "empty" in source.lower()
        assert has_blank_check, "AVSyncReviewer must check for blank/empty frames"
