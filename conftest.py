"""Project-root pytest config.

Markers are declared in pyproject.toml [tool.pytest.ini_options].
Kept as a file for future project-wide fixtures.
"""

import os


def pytest_addoption(parser):
    parser.addoption(
        "--eval-mode",
        action="store_true",
        default=False,
        help="Enable eval mode (sets AVS_EVAL_MODE=1).",
    )


def pytest_configure(config):
    if config.getoption("--eval-mode"):
        os.environ["AVS_EVAL_MODE"] = "1"
