"""pytest-bdd dispatcher for features/gatekeeper.feature.

Step defs live in steps/gatekeeper_steps.py. Selection: `pytest -m gatekeeper`.
"""

from pytest_bdd import scenarios

pytest_plugins = [
    "tests.integration.bdd.steps.common_steps",
    "tests.integration.bdd.steps.gatekeeper_steps",
]

# Path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/gatekeeper.feature")
