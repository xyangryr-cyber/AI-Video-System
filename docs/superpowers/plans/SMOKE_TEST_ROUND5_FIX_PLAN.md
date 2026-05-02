# Round 5 Smoke Test Fix Plan

> **Source**: `第五轮smoke_test_report.md` (2026-04-27)
> **Conclusion**: NOT PASSED — 2 P0 blockers + 1 P1 instability
> **HARNESS**: v1.1.0 compliant
> **Status**: PLAN

---

## Issue Summary

| Priority | Issue | Impact | Root Cause |
|---|---|---|---|
| **P0** | Frontend white screen | Entire frontend unusable | `src/frontend/api/` dir name conflicts with Vite `/api` proxy prefix |
| **P0** | Backend API 500 | All data APIs return 500 | `get_db()` dependency never overridden — throws RuntimeError |
| **P1** | pnpm symlink unstable | MSW may intermittently fail to load | pnpm peer dependency version mismatch (two MSW installs) |

---

## Task Card 1: Fix Vite Proxy Path Conflict (P0)

```yaml
task_id: SMOKE-FIX-001
title: Fix Vite proxy intercepting frontend source files under src/frontend/api/
spec_ref: SPEC-B (infra — dev server config)
priority: P0
depends_on: []
allowed_files:
  - src/frontend/vite.config.ts
  - src/frontend/api/client.ts
  - src/frontend/api/master_audio.ts
  - src/frontend/api/material_actions.ts
  - src/frontend/hooks/useProjects.ts
  - src/frontend/hooks/useProjectState.ts
  - src/frontend/hooks/useCreateProject.ts
  - src/frontend/hooks/useEventStream.ts
  - src/frontend/hooks/useSettings.ts
  - src/frontend/hooks/usePreferenceWriteback.ts
  - src/frontend/components/CandidateSelector.tsx
  - src/frontend/render/brandKit.ts
forbidden_files:
  - HARNESS.md
  - CLAUDE.md
  - docker-compose.dev.yml
  - docker-compose.yml
  - .env
verification_commands:
  - curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/client.ts  # expect 200
  - curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/master_audio.ts  # expect 200
  - curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/material_actions.ts  # expect 200
  - docker exec ai-video-system-frontend-1 sh -c 'cd /tmp && node -e "const { chromium } = require(\"playwright\"); (async () => { const browser = await chromium.launch({ headless: true }); const page = await browser.newPage(); await page.goto(\"http://localhost:3000\", { waitUntil: \"networkidle\" }); await page.waitForTimeout(3000); const text = await page.textContent(\"body\"); console.log(\"HAS_项目列表:\", text.includes(\"项目列表\")); console.log(\"HAS_黄金价格:\", text.includes(\"黄金价格\")); await browser.close(); })();"'  # expect both true
  - pnpm --filter frontend exec vitest run tests/unit/frontend/  # existing frontend unit tests still pass
  - pnpm --filter frontend exec tsc --noEmit  # type check passes
completion_definition:
  - Frontend page renders content (not white screen) in Docker dev environment
  - All 3 api/*.ts source files served as JS modules (HTTP 200), not proxied to backend
  - All 10 dependent imports resolve correctly
  - Existing frontend tests pass
```

### Approach Selection

Three approaches identified in smoke test report:

| Option | Description | Files Touched | Risk |
|---|---|---|---|
| **A** | Rename `src/frontend/api/` → `src/frontend/apiClient/` | 13 (3 source + 10 imports) | Medium — every import path changes |
| **B** | Add Vite proxy `bypass` function excluding `*.ts` files | 1 (vite.config.ts) | Low — proxy config only |
| **C** | Use `import.meta.env.VITE_API_TARGET` for absolute URLs | 10+ (all API call sites) | High — changes every API call pattern |

**Decision: Option B (proxy bypass)** — minimal change, lowest risk, no import path refactoring needed. The bypass function in Vite's proxy config can inspect the request path and skip proxying when the request is for a `.ts`/`.tsx` source file.

### TDD Plan (RED-GREEN-REFACTOR)

**Step 1 — RED**: Write a test that verifies source files under `src/frontend/api/` are NOT proxied.

- Test file: `tests/integration/test_proxy_routing.py` (already exists — add test case)
- Test case: `test_api_ts_files_not_proxied()` — HTTP GET `/api/client.ts` returns 200 with JS content, not 500 backend error

**Step 2 — GREEN**: Add bypass function to `vite.config.ts` proxy config:

```ts
proxy: {
  "/api": {
    target: process.env.VITE_API_TARGET || "http://localhost:8000",
    changeOrigin: true,
    bypass(req) {
      // Don't proxy requests for source files under src/frontend/api/
      if (req.url && /\.(ts|tsx|js|jsx)(\?.*)?$/.test(req.url)) {
        return req.url;
      }
    },
  },
}
```

**Step 3 — REFACTOR**: Verify no regressions in API proxy behavior (real API calls still reach backend).

**Step 4 — COMMIT**: `[SMOKE-FIX-001] add Vite proxy bypass for frontend api/ source files`

### HARNESS §4.3 TDD Exception Check

This is a **config change** (vite.config.ts proxy settings) — qualifies for TDD exception per HARNESS §4.3. However, since it changes runtime behavior and can be tested (integration test for proxy routing), TDD is applied for safety. The existing `tests/integration/test_proxy_routing.py` provides the test infrastructure.

---

## Task Card 2: Wire Database Dependency Injection (P0)

```yaml
task_id: SMOKE-FIX-002
title: Implement SQLite connection management and wire get_db dependency
spec_ref: SPEC-B (infra — database connection)
priority: P0
depends_on: []
allowed_files:
  - src/backend/api/main.py
  - src/backend/db/connection.py  (create if missing)
forbidden_files:
  - HARNESS.md
  - CLAUDE.md
  - data/db/*.sqlite3
  - .env
verification_commands:
  - curl -s http://localhost:8000/health  # expect {"status":"ok"}
  - curl -s http://localhost:8000/api/projects  # expect JSON array (not 500 error)
  - curl -s http://localhost:8000/api/projects | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list), f'Expected list, got {type(d)}'; print(f'OK: {len(d)} projects')"  # expect OK: N projects
  - python3 -m pytest tests/smoke/test_key_endpoints.py -v  # smoke tests pass
  - python3 -m pytest tests/unit/backend/ -v -k "project"  # backend unit tests pass
completion_definition:
  - GET /api/projects returns JSON array (not 500)
  - All endpoints using Depends(get_db) function correctly
  - DB connection managed via FastAPI lifespan events
  - Connection closed on app shutdown
  - Existing backend tests pass
```

### Fix Details

**Current state** (`src/backend/api/routes/projects.py:42-46`):
```python
def get_db() -> sqlite3.Connection:
    raise RuntimeError("DB dependency not wired...")
```

**Required changes:**

1. **Create `src/backend/db/connection.py`** — SQLite connection manager:
   - `get_db_path()` — resolve DB path from env `DB_PATH` (default `data/db/dev.sqlite3`)
   - `create_connection(db_path)` — create sqlite3.Connection with `check_same_thread=False`, `row_factory=sqlite3.Row`
   - Handle connection lifecycle (open/close)

2. **Update `src/backend/api/main.py`** — wire dependency:
   - Add `lifespan` context manager to FastAPI app
   - On startup: create DB connection, store in `app.state.db_connection`
   - Override `get_db` dependency to return `app.state.db_connection`
   - On shutdown: close connection

### TDD Plan (RED-GREEN-REFACTOR)

**Step 1 — RED**: Write tests that verify DB connection is wired.

- Test file: `tests/unit/backend/test_db_connection.py` (create)
- Test case 1: `test_get_db_returns_connection()` — verify get_db returns a real sqlite3.Connection
- Test case 2: `test_get_db_queries_projects()` — verify can query projects table
- Test case 3: `test_lifespan_wires_dependency()` — verify app.state has db_connection after startup

**Step 2 — GREEN**: Implement `src/backend/db/connection.py` + update `main.py` lifespan.

**Step 3 — REFACTOR**: Check all routes using `Depends(get_db)` work correctly. Check other route files (`tasks.py`, `preferences.py`, `settings_bridge.py`) for the same pattern.

**Step 4 — COMMIT**: `[SMOKE-FIX-002] implement SQLite connection management and wire get_db`

### Impact Analysis (举一反三)

Per smoke test report §4.2, check all route files using `Depends(get_db)`:

| Route File | Uses get_db? | Affected |
|---|---|---|
| `src/backend/api/routes/projects.py` | Yes | **Fix covers this** |
| `src/backend/api/routes/tasks.py` | Need to check | Verify after fix |
| `src/backend/api/routes/preferences.py` | Need to check | Verify after fix |
| `src/backend/api/routes/settings_bridge.py` | Need to check | Verify after fix |

---

## Task Card 3: Stabilize pnpm MSW Peer Dependency (P1)

```yaml
task_id: SMOKE-FIX-003
title: Fix pnpm symlink inconsistency for MSW peer dependencies
spec_ref: SPEC-B (infra — build dependencies)
priority: P1
depends_on: []
allowed_files:
  - src/frontend/package.json
  - pnpm-lock.yaml
forbidden_files:
  - HARNESS.md
  - CLAUDE.md
verification_commands:
  - docker exec ai-video-system-frontend-1 sh -c 'ls -la node_modules/msw'  # symlink resolves to existing dir
  - docker exec ai-video-system-frontend-1 sh -c 'pnpm list msw --depth=0'  # single version, no errors
  - docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up -d  # restart clean
  - docker exec ai-video-system-frontend-1 sh -c 'ls -la node_modules/msw'  # symlink still valid after restart
completion_definition:
  - MSW symlink resolves consistently across docker restarts
  - Single MSW version installed (no duplicate peer dependency variants)
  - pnpm list shows no errors for MSW
```

### Fix Details

**Current state**: Two MSW installations in lockfile:
- `msw@2.6.6_@types+node@25.6.0_typescript@5.8.3` (expected by lockfile)
- `msw@2.6.6_typescript@5.8.3` (extra installation)

**Fix approach:**
1. Check if `@types/node` is a declared peer dependency of MSW or a transitive dependency
2. If MSW doesn't actually need `@types/node` as a peer, remove the explicit `@types/node` peer dep resolution
3. If it does, ensure `@types/node` version matches what MSW expects
4. Ensure Docker startup uses consistent pnpm install flags

**TDD Exception**: This is a dependency/config fix — qualifies for TDD exception per HARNESS §4.3. Verification is via docker container inspection commands.

---

## Implementation Order

```
SMOKE-FIX-002 (DB wiring)     ← No dependency, can start immediately
SMOKE-FIX-001 (Proxy bypass)  ← No dependency, can start immediately
SMOKE-FIX-003 (pnpm symlink)  ← No dependency, can start immediately
```

All three are independent and can be executed in parallel.

**Recommended order**: 002 → 001 → 003 (backend first, then frontend, then stability)

---

## HARNESS Compliance Checklist

| HARNESS Rule | SMOKE-FIX-001 | SMOKE-FIX-002 | SMOKE-FIX-003 |
|---|---|---|---|
| §1 Directory Authority | frontend + tests only | backend + tests only | frontend config only |
| §2 Dependency Direction | Layer 7 change only | Layer 4 change only | N/A (config) |
| §3 Naming Conventions | snake_case.py for test | snake_case.py | N/A |
| §4 TDD | Yes (integration test) | Yes (unit tests) | Exception (config) |
| §6 File Size Limits | <300 lines TS | <400 lines Python | N/A |
| §8 Logging | N/A | Use structured logger | N/A |
| §9 PROGRESS.md | One row per commit | One row per commit | One row per commit |
| §12 Task Card | Read before code | Read before code | Read before code |

---

## Verification Gate (All Fixes Applied)

After all three fixes are applied, run the full smoke test verification from the original report:

```bash
# 1. Frontend module availability
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/client.ts
# Expected: 200

# 2. Backend API
curl -s http://localhost:8000/api/projects
# Expected: JSON array (not {"error":...})

# 3. Page rendering verification (in container)
docker exec ai-video-system-frontend-1 sh -c '
cd /tmp && node -e "
const { chromium } = require(\"playwright\");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(\"http://localhost:3000\", { waitUntil: \"networkidle\" });
  await page.waitForTimeout(3000);
  const text = await page.textContent(\"body\");
  console.log(\"HAS_项目列表:\", text.includes(\"项目列表\"));
  console.log(\"HAS_黄金价格:\", text.includes(\"黄金价格\"));
  await browser.close();
})();
"
# Expected: HAS_项目列表: true, HAS_黄金价格: true

# 4. MSW stability
docker exec ai-video-system-frontend-1 sh -c 'ls -la node_modules/msw'
# Expected: valid symlink to existing directory

# 5. Existing test suite
python3 -m pytest tests/unit/ tests/integration/ -x --timeout=30
pnpm --filter frontend exec vitest run tests/unit/frontend/
```
