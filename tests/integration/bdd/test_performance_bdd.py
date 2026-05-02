"""pytest-bdd dispatcher for features/performance.feature.

Step defs live in steps/performance_steps.py. Selection: `pytest -m performance`.
"""

from pytest_bdd import scenarios

pytest_plugins = ["tests.integration.bdd.steps.performance_steps"]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/performance.feature")
