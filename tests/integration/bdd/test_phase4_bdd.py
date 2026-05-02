"""pytest-bdd dispatcher for features/phase4.feature.

Step defs live in steps/phase4_steps.py. Selection: `pytest -m phase4`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.phase4_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/phase4.feature")
