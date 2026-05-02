"""pytest-bdd dispatcher for features/phase6.feature.

Step defs live in steps/phase6_steps.py. Selection: `pytest -m phase6`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase6_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase6.feature")
