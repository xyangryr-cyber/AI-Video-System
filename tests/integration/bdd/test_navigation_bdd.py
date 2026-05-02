"""pytest-bdd dispatcher for features/navigation.feature.

Step defs live in steps/navigation_steps.py. Selection: `pytest -m navigation`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.navigation_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/navigation.feature")
