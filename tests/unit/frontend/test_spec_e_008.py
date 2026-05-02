"""Tests for [SPEC-E-008] Agent Activity Panel (Event Stream)."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
TEST_FILE = "components/AgentActivityPanel.test.tsx"


def _vitest(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, TEST_FILE],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1Renders50EventsFormatted:
    """AC-1: Panel displays up to 50 events with format `[HH:MM:SS] [agent_name] [action] [result/progress]`"""

    def test_renders_50_events_formatted(self):
        r = _vitest("AC-1 renders events")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2FetchesHistoryOnMount:
    """AC-2: On page load, fetches history via `GET /api/projects/{id}/events?limit=50`"""

    def test_fetches_history_on_mount(self):
        r = _vitest("AC-2 fetches initial history")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3AppendsWsEvents:
    """AC-3: Real-time events arrive via WebSocket and append to panel"""

    def test_appends_ws_events(self):
        r = _vitest("AC-3 appends live event")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4DomUpdateWithin200ms:
    """AC-4: DOM update completes within 200ms of `WebSocket.onmessage` (Performance.mark instrumentation)"""

    def test_dom_update_within_200ms(self):
        r = _vitest("AC-4 DOM update")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5ScrollTopLoadsHistory:
    """AC-5: Scrolling to top triggers loading of older events (pagination)"""

    def test_scroll_top_loads_history(self):
        r = _vitest("AC-5 scroll-to-top")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6ReconnectFillsGapNoDuplicates:
    """AC-6: After WebSocket disconnect/reconnect, missed events are fetched via REST and merged without duplicates"""

    def test_reconnect_fills_gap_no_duplicates(self):
        r = _vitest("AC-6 dedup")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
