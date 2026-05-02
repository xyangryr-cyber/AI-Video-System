"""pytest-bdd dispatcher for features/phase10.feature.

Step defs live in steps/phase10_steps.py. Selection: `pytest -m phase10`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase10_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase10.feature")
