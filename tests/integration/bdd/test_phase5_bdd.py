"""pytest-bdd dispatcher for features/phase5.feature.

Step defs live in steps/phase5_steps.py. Selection: `pytest -m phase5`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase5_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase5.feature")
