"""pytest-bdd dispatcher for features/safety.feature.

Step defs live in steps/safety_steps.py. Selection: `pytest -m safety`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.safety_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/safety.feature")
