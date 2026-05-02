"""[SPEC-GAPFIX-042] E2E test: verify homepage loads (non-blank).

Requires the full stack to be running (docker compose up).
Skips gracefully when the stack is not available.
"""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
TIMEOUT = 10.0


def _stack_available() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        return r.status_code < 600
    except Exception:
        return False


@pytest.mark.skipif(
    not _stack_available(),
    reason="Full stack not available. Run 'docker compose -f docker-compose.dev.yml up -d' first.",
)
class TestAppLoads:
    """Verify the frontend serves a non-blank HTML page."""

    def test_homepage_returns_200(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        assert r.status_code == 200

    def test_homepage_is_html(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        content_type = r.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_homepage_has_body_content(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        body = r.text.strip()
        assert len(body) > 500, f"Expected non-trivial HTML, got {len(body)} chars"
        assert "</body>" in body or "</html>" in body, "Page should be valid HTML"

    def test_homepage_has_root_div(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        # React apps mount into a root div
        assert "root" in r.text.lower() or "app" in r.text.lower(), (
            "Homepage should contain a mount point"
        )

    def test_static_assets_are_served(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT, follow_redirects=True)
        text = r.text
        # Vite injects a script tag for the entry module
        has_script = '<script' in text
        assert has_script, "Homepage should include JavaScript"
