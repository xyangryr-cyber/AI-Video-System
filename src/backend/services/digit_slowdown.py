"""[SPEC-D-004] P4 DigitSlowdown -- SSML wrapping for digit-dense sentences.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.6

Pure code, 0 LLM tokens. Detects digit-dense sentences via regex and wraps
them with SSML prosody/break tags so TTS slows down for financial figures.
"""

from __future__ import annotations

import re

# Detect digit-dense sentences: contains Chinese percentage markers or
# multiple decimal/percentage tokens.
_DIGIT_DENSE_RE = re.compile(r"[\d.]+%|百分之[\d.]+|[0-9]+\.[0-9]{2,}|\d+点\d+")


class DigitSlowdown:
    """Detect digit-dense sentences and wrap with SSML slowdown tags."""

    _WRAP_TEMPLATE = '<speak><prosody rate="slow">{text}<break time="100ms"/></prosody></speak>'

    @classmethod
    def is_digit_dense(cls, text: str) -> bool:
        return bool(_DIGIT_DENSE_RE.search(text))

    @classmethod
    def wrap_ssml(cls, text: str) -> str:
        if not cls.is_digit_dense(text):
            return text
        return cls._WRAP_TEMPLATE.format(text=text)
