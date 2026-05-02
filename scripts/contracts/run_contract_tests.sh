#!/usr/bin/env bash
# Run the SPEC-A contract test suite.
#
# Usage:
#   bash scripts/contracts/run_contract_tests.sh          # run all 11 redo-target files
#   bash scripts/contracts/run_contract_tests.sh all      # run every test in tests/unit/contracts/
#   bash scripts/contracts/run_contract_tests.sh 001 010  # run a subset by task numbers
#
# Exits non-zero on any test failure or on any lingering skip stubs.
# See tasks/SPEC-A/REDO-real-tests-plan.md for context.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Pin Python 3.11 from the repo venv; system default is 3.9 on this machine.
if [[ ! -x ".venv/bin/python3" ]]; then
  echo "ERROR: .venv/bin/python3 not found. Create venv with 'python3.11 -m venv .venv' and 'pip install -e .[dev]'." >&2
  exit 2
fi
PYTHON=".venv/bin/python3"
PY_VERSION="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PY_VERSION" != "3.11" && "$PY_VERSION" != "3.12" ]]; then
  echo "ERROR: venv python is $PY_VERSION, expected 3.11+." >&2
  exit 2
fi

REDO_FILES=(
  tests/unit/contracts/test_spec_a_001.py
  tests/unit/contracts/test_spec_a_002.py
  tests/unit/contracts/test_spec_a_004.py
  tests/unit/contracts/test_spec_a_007.py
  tests/unit/contracts/test_spec_a_010.py
  tests/unit/contracts/test_spec_a_011.py
  tests/unit/contracts/test_spec_a_014.py
  tests/unit/contracts/test_spec_a_015.py
  tests/unit/contracts/test_spec_a_016.py
  tests/unit/contracts/test_spec_a_017.py
  tests/unit/contracts/test_spec_a_018.py
)

if [[ $# -eq 0 ]]; then
  TARGETS=("${REDO_FILES[@]}")
elif [[ "$1" == "all" ]]; then
  TARGETS=(tests/unit/contracts/)
else
  TARGETS=()
  for arg in "$@"; do
    TARGETS+=("tests/unit/contracts/test_spec_a_${arg}.py")
  done
fi

echo "=== Contract tests: $(date -u +%FT%TZ) ==="
echo "Python:   $($PYTHON --version)"
echo "Targets:  ${TARGETS[*]}"
echo

# 1. Skip-stub gate (fast fail).
$PYTHON scripts/contracts/verify_no_skip_stubs.py

# 2. pytest -v.
$PYTHON -m pytest "${TARGETS[@]}" -v --no-header -ra

echo
echo "=== Contract tests PASSED ==="
