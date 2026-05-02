"""pytest-bdd dispatcher for features/error_ux.feature.

Step defs live in steps/error_ux_steps.py. Selection: `pytest -m error_ux`.
"""

from __future__ import annotations

import pytest
from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.error_ux_steps"]
pytestmark = pytest.mark.error_ux

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/error_ux.feature")
