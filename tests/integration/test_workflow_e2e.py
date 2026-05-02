"""Integration tests for end-to-end workflow."""

import pytest


class TestProjectLifecycle:
    """Full project lifecycle: create -> advance phases -> complete."""

    def test_create_project_and_advance_to_p3(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-C + SPEC-D")

    def test_phase_rollback_on_gate_failure(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-C-015")


class TestAPIIntegration:
    """API endpoint integration with real DB."""

    def test_project_crud_roundtrip(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-A-006 + SPEC-B-001")

    def test_websocket_event_delivery(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-A-010 + SPEC-B-001")
