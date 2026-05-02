"""pytest-bdd dispatcher for features/phase8.feature.

Step defs live in steps/phase8_steps.py. Selection: `pytest -m phase8`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase8_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase8.feature")
