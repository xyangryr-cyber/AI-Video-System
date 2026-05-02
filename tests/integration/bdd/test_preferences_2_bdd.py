"""pytest-bdd dispatcher for features/preferences-2.feature.

Step defs live in steps/preferences_2_steps.py. Selection: `pytest -m "preferences-2"`.
"""

from __future__ import annotations

import pytest
from pytest_bdd import scenarios

pytest_plugins = [
    "tests.integration.bdd.steps.preferences_2_steps",
]
pytestmark = pytest.mark.__getattr__("preferences-2")

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/preferences-2.feature")
