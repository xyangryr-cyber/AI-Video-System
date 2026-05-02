"""pytest-bdd dispatcher for features/phase11.feature.

Step defs live in steps/phase11_steps.py. Selection: `pytest -m phase11`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase11_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase11.feature")
