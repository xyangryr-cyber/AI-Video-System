# SPEC A/B/C Acceptance Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all P0 and P1 blocking issues from SPEC-ABC-ACCEPTANCE-FIX-HANDOFF.md so SPEC A/B/C canonical tests pass, CI/dev env works, and static quality gates are clean.

**Architecture:** Fix in P0→P1 order. P0 fixes are blocking: (1) rename conflicting test file, (2) create FastAPI entrypoint + fix CI/compose deps, (3) replace hardcoded "default" with constant, (4) centralize DB writes into repositories, (5) replace NOT IMPLEMENTED skips with real assertions. P1 fixes handle frontend test, task card lint, and static quality.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, ruff, mypy, TypeScript, pnpm, Docker Compose

---

## P0-1: Fix pytest collection conflict (test_task_types.py name collision)

### Task 1.1: Rename contract test_task_types.py to avoid collision

**Files:**
- Rename: `tests/unit/contracts/test_task_types.py` → `tests/unit/contracts/test_task_types_contract.py`
- Modify: `tests/unit/contracts/test_spec_a_104.py` (if it re-exports from the old name)

- [ ] **Step 1: Check what imports test_task_types from contracts**

Run: `rg -n "test_task_types" tests/unit/contracts/`
Expected: Find any references that need updating.

- [ ] **Step 2: Rename the file**

```bash
git mv tests/unit/contracts/test_task_types.py tests/unit/contracts/test_task_types_contract.py
```

- [ ] **Step 3: Update any imports referencing old name**

If `test_spec_a_104.py` imports from `test_task_types`, update to `test_task_types_contract`.

- [ ] **Step 4: Verify collection works**

Run:
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_task_types_contract.py -q
.venv/bin/python -m pytest tests/unit/backend-core/test_task_types.py -q
.venv/bin/python -m pytest tests/unit/contracts tests/unit/infra tests/unit/backend-core tests/contract -q --collect-only
```
Expected: All three collect without import mismatch errors.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "[P0-1] rename contracts/test_task_types.py to resolve pytest collection conflict

Files Changed:
- tests/unit/contracts/test_task_types.py -> test_task_types_contract.py

Verification:
- pytest tests/unit/contracts/ tests/unit/infra/ tests/unit/backend-core/ tests/contract/ --collect-only → success"
```

---

## P0-2: Fix SPEC-B runtime / CI / dev env

### Task 2.1: Create FastAPI entrypoint src/backend/api/main.py

**Files:**
- Create: `src/backend/api/main.py`
- Test: `tests/unit/infra/test_api_main.py` (new)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/infra/test_api_main.py
"""Test FastAPI app entrypoint exists and exports /health."""
from __future__ import annotations


class TestAppEntrypoint:
    def test_app_importable(self):
        from src.backend.api.main import app
        assert app is not None
        assert app.title is not None

    def test_health_endpoint_registered(self):
        from src.backend.api.main import app
        routes = [r.path for r in app.routes]
        assert "/health" in routes

    def test_health_returns_ok(self):
        from fastapi.testclient import TestClient
        from src.backend.api.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/infra/test_api_main.py -v`
Expected: FAIL with ModuleNotFoundError for `src.backend.api.main`

- [ ] **Step 3: Create main.py**

```python
"""FastAPI application entrypoint.

[SPEC-B-001] Three-service topology: web / api / worker.
"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="AI Video System", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/infra/test_api_main.py -v`
Expected: 3 passed

- [ ] **Step 5: Register existing routers without breaking tests**

Add router registration to main.py:

```python
from src.backend.api.routes import system, tasks, preferences, observability, cost

app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["preferences"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["observability"])
app.include_router(cost.router, prefix="/api/v1/cost", tags=["cost"])
```

- [ ] **Step 6: Verify existing tests still pass**

Run: `.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q`
Expected: Same pass count as before (252 passed).

- [ ] **Step 7: Commit**

```bash
git add src/backend/api/main.py tests/unit/infra/test_api_main.py
git commit -m "[P0-2a] create FastAPI entrypoint with /health endpoint"
```

### Task 2.2: Fix dependency file strategy for CI/Docker/compose

**Files:**
- Create: `requirements.txt`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/nightly_e2e.yml`

- [ ] **Step 1: Generate requirements.txt from pyproject.toml**

Run: `.venv/bin/pip freeze > /tmp/frozen.txt` and inspect, or create a minimal requirements.txt from pyproject.toml deps.

Since the project uses `pyproject.toml`, create `requirements.txt` that mirrors its dependencies:

```text
# Generated from pyproject.toml — kept in sync manually for CI/Docker.
# Primary install: pip install -e ".[dev]" via pyproject.toml
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
instructor>=1.0.0
litellm>=1.50.0
sqlite3
```

Check `pyproject.toml` for actual deps and create matching requirements.txt.

- [ ] **Step 2: Verify CI workflow references are consistent**

Run: `rg -n "requirements.txt|requirements-dev.txt|pyproject" .github/workflows docker-compose*.yml src/backend/Dockerfile`
Expected: All reference the same strategy.

- [ ] **Step 3: Update docker-compose.yml to handle missing .env gracefully**

Modify `docker-compose.yml` to use `env_file` with optional semantics. One approach: provide defaults via `environment` fallback in compose:

```yaml
  api:
    ...
    env_file:
      - path: .env
        required: false
    environment:
      - DATABASE_URL=sqlite:///data/db/ai_video.db
```

- [ ] **Step 4: Verify docker compose config works**

Run: `docker compose config --quiet 2>&1`
Expected: No error (or only warnings, not failures).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .github/workflows/ci.yml .github/workflows/nightly_e2e.yml docker-compose.yml docker-compose.dev.yml
git commit -m "[P0-2b] fix CI/compose deps: add requirements.txt, make .env optional"
```

### Task 2.3: Fix nightly e2e "three consecutive failures" logic

**Files:**
- Modify: `.github/workflows/nightly_e2e.yml`

- [ ] **Step 1: Update nightly_e2e.yml to track consecutive failures**

Add a step before running e2e that reads/sets `.nightly_failure_count`:

```yaml
      - id: check_consecutive
        run: |
          if [ -f .nightly_failure_count ]; then
            COUNT=$(cat .nightly_failure_count)
          else
            COUNT=0
          fi
          echo "consecutive_failures=$COUNT" >> $GITHUB_OUTPUT
      - id: run_e2e
        ...
      - if: steps.run_e2e.outcome == 'failure'
        run: |
          echo $(( ${{ steps.check_consecutive.outputs.consecutive_failures }} + 1 )) > .nightly_failure_count
          echo "## nightly e2e failed ($(cat .nightly_failure_count)/3 consecutive)" > .nightly_failure.txt
      - if: steps.run_e2e.outcome == 'success'
        run: echo "0" > .nightly_failure_count
      - if: steps.run_e2e.outcome == 'failure' && steps.check_consecutive.outputs.consecutive_failures >= 2
        uses: peter-evans/create-issue-from-file@v5
        with:
          title: "[nightly-e2e] 3 consecutive failures"
          content-filepath: .nightly_failure.txt
          labels: nightly-e2e
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/nightly_e2e.yml
git commit -m "[P0-2c] fix nightly e2e: three consecutive failures before opening issue"
```

---

## P0-3: Fix SPEC-A-009 DEFAULT_USER_ID constant regression

### Task 3.1: Replace hardcoded "default" with DEFAULT_USER_ID

**Files:**
- Modify: `src/backend/services/preference_service.py:121`

- [ ] **Step 1: Verify the test catches the issue**

Run: `.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_009.py -q`
Expected: 1 failed (the current regression).

- [ ] **Step 2: Fix the code**

Change line 121 in `preference_service.py` from:
```python
def get_effective_preferences(self, project_id: str, user_id: str = "default") -> str:
```
to:
```python
def get_effective_preferences(self, project_id: str, user_id: str = DEFAULT_USER_ID) -> str:
```

Add import at top:
```python
from src.shared.constants.auth import DEFAULT_USER_ID
```

- [ ] **Step 3: Verify test passes**

Run:
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_009.py -q
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q
```
Expected: All pass, 0 failures.

- [ ] **Step 4: Verify no other hardcoded "default" user_id strings remain**

Run:
```bash
out=$(rg '"default"' src/ --type py | grep -v 'DEFAULT_USER_ID' | grep -i user || true); test -z "$out"
```
Expected: No output (no violations).

- [ ] **Step 5: Commit**

```bash
git add src/backend/services/preference_service.py
git commit -m "[P0-3] fix SPEC-A-009: use DEFAULT_USER_ID constant instead of hardcoded 'default'"
```

---

## P0-4: Fix SPEC-B-002 / SPEC-C-001 write boundary violations

### Task 4.1: Create TaskLedgerRepository for task_ledger writes

**Files:**
- Create: `src/backend/db/repositories/task_ledger_repository.py`
- Modify: `src/backend/agents/subtask_agents.py:64`

- [ ] **Step 1: Check existing repository pattern**

Read `src/backend/db/repositories/base.py` and `src/backend/db/repositories/preferences_repo.py` for patterns.

- [ ] **Step 2: Write failing test for task_ledger write path**

Create test that verifies all task_ledger writes go through repository:

```python
# tests/unit/infra/test_task_ledger_write_path.py
"""Verify task_ledger writes only through repository."""
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"

WRITE_SQL = re.compile(
    r"\b(INSERT\s+INTO\s+task_ledger|UPDATE\s+\w*task_ledger\w*\s+SET|DELETE\s+FROM\s+task_ledger)\b",
    flags=re.IGNORECASE,
)


def test_task_ledger_writes_only_in_repository_or_engine():
    violations = []
    for py_file in BACKEND_DIR.rglob("*.py"):
        if "task_ledger_repository" in str(py_file) or "workflow_engine" in str(py_file):
            continue
        if "db/repositories" in str(py_file):
            continue
        content = py_file.read_text(encoding="utf-8")
        if WRITE_SQL.search(content):
            violations.append(str(py_file.relative_to(REPO_ROOT)))
    assert violations == [], f"task_ledger writes outside repository/engine: {violations}"
```

- [ ] **Step 3: Create TaskLedgerRepository**

```python
# src/backend/db/repositories/task_ledger_repository.py
"""Repository for task_ledger table writes."""
from __future__ import annotations

import sqlite3


class TaskLedgerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def update_result_ref(self, task_id: str, result_ref: str) -> None:
        self._conn.execute(
            "UPDATE task_ledger SET result_ref = ? WHERE id = ?",
            (result_ref, task_id),
        )
        self._conn.commit()
```

- [ ] **Step 4: Fix subtask_agents.py to use repository**

Replace the raw SQL in `src/backend/agents/subtask_agents.py:64` with a call through `TaskLedgerRepository`.

- [ ] **Step 5: Create FinancialDataCacheRepository**

```python
# src/backend/db/repositories/financial_data_cache_repo.py
"""Repository for financial_data_cache table."""
from __future__ import annotations

import sqlite3


class FinancialDataCacheRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def delete_by_symbol_provider(self, symbol: str, provider: str) -> None:
        self._conn.execute(
            "DELETE FROM financial_data_cache WHERE symbol = ? AND provider = ?",
            (symbol, provider),
        )
        self._conn.commit()
```

- [ ] **Step 6: Fix financial_data_service.py to use repository**

Replace raw SQL at line 57 with call through `FinancialDataCacheRepository`.

- [ ] **Step 7: Fix PreferenceService raw SQL (lines 148, 173, 187, 195, 245, 257, 292, 300)**

These already have a `preferences_repo.py` in the repository layer. Refactor PreferenceService to delegate writes to `PreferencesRepo` rather than issuing raw SQL directly.

- [ ] **Step 8: Verify SPEC-B-002 test passes**

Run: `.venv/bin/python -m pytest tests/unit/infra/test_spec_b_002.py -q`
Expected: All passed (or at least the raw SQL scan parts pass).

- [ ] **Step 9: Verify SPEC-C-001 WorkflowEngine test passes**

Run: `.venv/bin/python -m pytest tests/unit/backend-core/test_workflow_engine.py::TestAC1AllStateChangesThroughEngine -q`
Expected: All passed.

- [ ] **Step 10: Commit**

```bash
git add src/backend/db/repositories/task_ledger_repository.py src/backend/db/repositories/financial_data_cache_repo.py src/backend/agents/subtask_agents.py src/backend/services/financial_data_service.py src/backend/services/preference_service.py tests/unit/infra/
git commit -m "[P0-4] centralize DB writes into repositories; fix task_ledger/preferences/financial_data_cache raw SQL"
```

---

## P0-5: Replace SPEC-C canonical NOT IMPLEMENTED skips

### Task 5.1: Migrate real tests into canonical SPEC-C files

**Files:**
- Modify: `tests/unit/backend-core/test_spec_c_001.py` through `test_spec_c_022.py`, `test_spec_c_100.py`, `test_spec_c_101.py`

For each SPEC-C task marked DONE in PROGRESS.md, the canonical test file must have real assertions instead of `pytest.skip("NOT IMPLEMENTED")`. Real implementations exist in files like:
- `tests/unit/services/test_narration_master_assembler.py` → re-export to `test_spec_c_016.py`
- Similar for C-001..C-006, C-009, C-010, C-011, C-015, C-017, C-019, C-020, C-021, C-022, C-100, C-101

- [ ] **Step 1: For each NOT-IMPLEMENTED canonical file, find the real test file**

Run to map stubs to real tests:
```bash
for f in tests/unit/backend-core/test_spec_c_*.py; do
    has_skip=$(rg -c 'pytest\.skip\("NOT IMPLEMENTED' "$f" 2>/dev/null || echo 0)
    if [ "$has_skip" -gt 0 ]; then
        echo "STUB: $f"
    fi
done
```

Then for each stub, find where real tests landed by checking PROGRESS.md DONE entries.

- [ ] **Step 2: Replace C-001 stubs (WorkflowEngine)**

Find real tests: `tests/unit/backend-core/test_workflow_engine.py` already has real tests. Re-export pattern:
```python
# In test_spec_c_001.py, replace skip stubs with:
from tests.unit.backend_core.test_workflow_engine import (
    TestAC1AllStateChangesThroughEngine,
    # ... other test classes
)
```

- [ ] **Step 3: Repeat for C-002 through C-022, C-100, C-101**

Follow same pattern: find real test implementations in other test files and re-export or migrate to canonical files.

- [ ] **Step 4: Verify all NOT IMPLEMENTED skips removed**

Run: `rg -n 'pytest\.skip\("NOT IMPLEMENTED' tests/unit/backend-core/test_spec_c_*.py`
Expected: No output.

- [ ] **Step 5: Run full SPEC-C canonical tests**

Run: `.venv/bin/python -m pytest tests/unit/backend-core/test_spec_c_*.py -q`
Expected: All pass, 0 skipped (or skipped for genuinely unimplemented tasks only).

- [ ] **Step 6: Update verify_no_skip_stubs.py coverage**

Ensure `scripts/contracts/verify_no_skip_stubs.py` covers all A/B/C canonical test files.

- [ ] **Step 7: Commit**

```bash
git add tests/unit/backend-core/test_spec_c_*.py scripts/contracts/verify_no_skip_stubs.py
git commit -m "[P0-5] replace SPEC-C canonical NOT IMPLEMENTED skips with real test re-exports"
```

---

## P1-1: Fix SPEC-B-017 mock/fixture test failure

### Task 6.1: Fix handler test to match array response from /api/v1/projects

**Files:**
- Modify: `tests/unit/frontend/mocks/handlers.test.ts`

- [ ] **Step 1: Understand the contract**

The fixture `list_response.json` returns an array of projects. The test `expect(body.project_id).toBe("proj_001")` expects a single object. Fix the test to handle the array response:

```typescript
  it("intercepts /api/v1/projects with fixture data", async () => {
    const res = await fetch("http://localhost/api/v1/projects");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body[0].project_id).toBe("proj_001");
    expect(body[0].title).toBe("黄金价格走势分析");
  });
```

- [ ] **Step 2: Handle WebSocket mock**

Add a WS handler to prevent unhandled request warnings:
```typescript
import { ws } from "msw";

// In handlers array:
ws.link("ws://localhost:8000/ws/*"),
```

Or configure the server to warn (not error) on unhandled WS:
```typescript
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
```

- [ ] **Step 3: Run frontend tests**

Run:
```bash
pnpm --filter frontend test -- tests/unit/frontend/mocks/handlers.test.ts
pnpm --filter frontend test
```
Expected: All pass.

- [ ] **Step 4: Commit**

```bash
git add src/frontend/mocks/handlers.ts tests/unit/frontend/mocks/handlers.test.ts
git commit -m "[P1-1] fix handler test: /api/v1/projects returns array, not single object"
```

---

## P1-2: Fix task card verification command coverage

### Task 7.1: Add verification commands to A-107..A-115 task cards

**Files:**
- Modify: `tasks/SPEC-A/A-107-*.md` through `tasks/SPEC-A/A-115-*.md`

- [ ] **Step 1: Read each task card**

Read A-107 through A-115 to understand what each task does.

- [ ] **Step 2: Add Verification Commands section**

For each task card, add a `## Verification Commands` section with at least one `pytest` command that verifies the implementation.

- [ ] **Step 3: Add Test Mapping section**

Add a `## Test Mapping` table mapping each AC to a test function.

- [ ] **Step 4: Verify task card lint passes**

Run: `.venv/bin/python scripts/lint_task_cards.py --only SPEC-A`
Expected: 0 findings for A-107..A-115.

- [ ] **Step 5: Commit**

```bash
git add tasks/SPEC-A/
git commit -m "[P1-2a] add verification commands to A-107..A-115 task cards"
```

### Task 7.2: Create canonical tests for B-017/B-018

**Files:**
- Create: `tests/unit/infra/test_spec_b_017.py`
- Create: `tests/unit/infra/test_spec_b_018.py`

- [ ] **Step 1: Read B-017 and B-018 task cards**

Understand what they require for verification.

- [ ] **Step 2: Create canonical test files**

Write `test_spec_b_017.py` and `test_spec_b_018.py` with real assertions matching the task card acceptance criteria.

- [ ] **Step 3: Verify task card lint passes**

Run:
```bash
.venv/bin/python scripts/lint_task_cards.py --only SPEC-B
.venv/bin/python scripts/lint_task_cards.py --only SPEC-C
```
Expected: No findings.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/infra/test_spec_b_017.py tests/unit/infra/test_spec_b_018.py
git commit -m "[P1-2b] add canonical test files for B-017 and B-018"
```

---

## P1-3: Fix static quality gates

### Task 8.1: Fix ruff errors

**Files:**
- Modify: Various files with ruff violations

- [ ] **Step 1: Get full list of ruff errors**

Run: `.venv/bin/python -m ruff check src tests/unit/contracts tests/unit/infra tests/unit/backend-core scripts 2>&1 | tee /tmp/ruff_errors.txt`

- [ ] **Step 2: Fix each category of errors**

Common fixes:
- `F401`: Remove unused imports
- `F841`: Remove unused variables
- `E731`: Convert lambdas to defs
- `F541`: Remove f-string prefix without placeholders

- [ ] **Step 3: Verify ruff is clean**

Run: `.venv/bin/python -m ruff check src tests/unit/contracts tests/unit/infra tests/unit/backend-core scripts`
Expected: No output (0 errors).

- [ ] **Step 4: Commit**

```bash
git add <fixed files>
git commit -m "[P1-3a] fix ruff errors on A/B/C-related paths"
```

### Task 8.2: Fix mypy strict errors

**Files:**
- Modify: Various source files with mypy errors

- [ ] **Step 1: Get full list of mypy errors**

Run: `.venv/bin/python -m mypy --explicit-package-bases src/shared src/backend scripts --strict 2>&1 | tee /tmp/mypy_errors.txt`

- [ ] **Step 2: Fix each category of errors**

Common fixes:
- Missing type annotations on function params/returns
- Missing TypedDict definitions
- Literal type narrowing
- None checks

- [ ] **Step 3: Verify mypy is clean**

Run: `.venv/bin/python -m mypy --explicit-package-bases src/shared src/backend scripts --strict`
Expected: No output (0 errors).

- [ ] **Step 4: Commit**

```bash
git add <fixed files>
git commit -m "[P1-3b] fix mypy strict errors on A/B/C-related source files"
```

### Task 8.3: Fix frontend tsc errors

**Files:**
- Modify: Various frontend TypeScript files

- [ ] **Step 1: Get full list of tsc errors**

Run: `pnpm --filter frontend tsc 2>&1 | tee /tmp/tsc_errors.txt`

- [ ] **Step 2: Fix each error**

Common fixes:
- Missing type imports
- Incorrect prop types
- Missing dependencies in package.json
- Path alias resolution issues

- [ ] **Step 3: Verify tsc passes**

Run: `pnpm --filter frontend tsc`
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add <fixed files>
git commit -m "[P1-3c] fix frontend tsc errors"
```

---

## Final Verification (after all tasks complete)

Run the full acceptance suite:

```bash
# 1. SPEC-A
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q

# 2. SPEC-B
.venv/bin/python -m pytest tests/unit/infra/test_spec_b_*.py tests/unit/infra/test_validate_fixtures.py tests/unit/infra/test_seed_dev_db.py -q

# 3. SPEC-C
.venv/bin/python -m pytest tests/unit/backend-core/test_spec_c_*.py -q

# 4. Full unit/contract
.venv/bin/python -m pytest tests/unit/ tests/contract/ -q

# 5. No-skip + lint
.venv/bin/python scripts/contracts/verify_no_skip_stubs.py
.venv/bin/python scripts/lint_task_cards.py --only SPEC-A
.venv/bin/python scripts/lint_task_cards.py --only SPEC-B
.venv/bin/python scripts/lint_task_cards.py --only SPEC-C

# 6. Frontend
pnpm --filter frontend test
pnpm --filter frontend tsc

# 7. Static quality
.venv/bin/python -m ruff check src tests/unit/contracts tests/unit/infra tests/unit/backend-core scripts
.venv/bin/python -m mypy --explicit-package-bases src/shared src/backend scripts --strict

# 8. Docker
docker compose config --quiet
```
