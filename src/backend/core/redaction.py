"""Secret redaction for LLM prompt/response fields (SPEC-B-008).

7 regex rules cover common key formats. Applied BEFORE DB write so
no secret ever lands in ``agent_call_log.prompt`` or ``.response``.
"""

from __future__ import annotations

import hashlib
import re

SECRET_REGEXES: list[tuple[str, str]] = [
    ("sk_key", r"sk-[a-zA-Z0-9_\-]{5,}"),
    ("openai_key", r"sk-[a-zA-Z0-9_\-]{15,}"),
    ("github_pat", r"gh[pousr]_[a-zA-Z0-9]{15,}"),
    ("aws_key", r"AKIA[A-Z0-9]{16}"),
    ("jwt", r"eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{5,}"),
    (
        "private_key",
        r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----[\s\S]{5,}?(?:-----END (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----|$)",
    ),
    ("google_api", r"ya29\.[a-zA-Z0-9_\-]{10,}"),
]

REDACTION_PLACEHOLDER = "[REDACTED]"

TRUNCATION_THRESHOLD = 8192  # 8 KB
TRUNCATION_HEAD_BYTES = 2048
TRUNCATION_TAIL_BYTES = 2048


def redact_text(text: str) -> str:
    """Apply all SECRET_REGEXES, replacing matches with [REDACTED]."""
    for _name, pattern in SECRET_REGEXES:
        text = re.sub(pattern, REDACTION_PLACEHOLDER, text)
    return text


def truncate_large_payload(text: str) -> str:
    """If text exceeds TRUNCATION_THRESHOLD bytes, keep first 2KB + last 2KB + MD5."""
    if len(text.encode("utf-8")) <= TRUNCATION_THRESHOLD:
        return text
    md5_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    head = text[:TRUNCATION_HEAD_BYTES]
    tail = text[-TRUNCATION_TAIL_BYTES:]
    return (
        f"{head}\n... [TRUNCATED: {len(text.encode('utf-8'))} bytes] ...\n{tail}\n"
        f"[MD5: {md5_hash}]"
    )
