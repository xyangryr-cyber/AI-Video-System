"""pytest-bdd dispatcher for the eval-bucket @classification scenarios.

The eval bucket's router.feature contains classifier-correctness scenarios
(e.g. "revise", "regenerate") -- integration-bucket router.feature covers
the timeout/fallback case only.
"""

from pytest_bdd import scenarios

# Register step defs from this dispatcher (pytest-bdd 8 needs explicit plugin reg).
pytest_plugins = ["tests.eval.bdd.steps.classification_steps"]

# Path relative to bdd_features_base_dir ("tests") -- see T5's precedent.
scenarios("eval/bdd/features/router.feature")
