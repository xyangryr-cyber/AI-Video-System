"""pytest-bdd dispatcher for features/preferences.feature.

Step defs live in steps/preferences_steps.py. Selection: `pytest -m preferences`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.preferences_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/preferences.feature")
