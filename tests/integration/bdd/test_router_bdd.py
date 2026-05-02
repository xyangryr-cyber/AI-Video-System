"""pytest-bdd dispatcher for features/router.feature.

This file produces one pytest test-function per Scenario. Step defs live in
steps/router_steps.py. Selection by tag: `pytest -m "router"`.
"""

from pytest_bdd import scenarios

# pytest_plugins tells pytest to collect fixtures from these modules,
# which is required so pytest-bdd step fixtures are discovered at session start.
pytest_plugins = ["tests.integration.bdd.steps.router_steps"]

# Relative path resolved from bdd_features_base_dir = "tests" in pyproject.toml.
scenarios("integration/bdd/features/router.feature")
