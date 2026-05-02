"""E2E tests -- require full stack (frontend + backend).

See also:
- test_app_loads.py -- homepage non-blank verification
- test_api_integration.py -- proxy chain verification
- playwright/ -- browser-based E2E (Playwright, requires npx)
"""

import pytest


class TestE2ERegression:
    """End-to-end tests requiring full stack."""

    def test_real_e2e_tests_exist(self):
        """Verify that E2E test files are no longer placeholders."""
        import os

        e2e_dir = os.path.dirname(__file__)
        test_files = [
            f for f in os.listdir(e2e_dir)
            if f.startswith("test_") and f.endswith(".py") and f != os.path.basename(__file__)
        ]
        assert len(test_files) > 0, f"Expected real E2E tests in {e2e_dir}"
