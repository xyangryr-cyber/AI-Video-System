"""pytest-bdd dispatcher for features/observability.feature.

Step defs live in steps/observability_steps.py. Selection: `pytest -m observability`.
"""

from pytest_bdd import scenarios

pytest_plugins = [
    "tests.integration.bdd.steps.common_steps",
    "tests.integration.bdd.steps.observability_steps",
]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/observability.feature")
