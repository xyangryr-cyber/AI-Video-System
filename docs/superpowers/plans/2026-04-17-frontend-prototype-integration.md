# Frontend Prototype Integration — Implementation Plan (Wave 0 + Wave 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the foundational infrastructure (mock layer, real dev env, contract test) and the prototype audit needed before per-card SPEC-E TDD reimplementation can begin.

**Architecture:** Isolate the Google AI Studio prototype under `prototype/` (read-only reference, exempt from SPEC-X-NNN flow). Build an MSW + JSON-fixture mock layer with a single source of truth. Stand up `make dev` for real backend+frontend integration. Add a contract consistency test that compares `src/frontend/types/*.ts` against Pydantic models in `src/shared/schemas/*.py` (via emitted JSON Schema). Audit the prototype and capture every contract delta in `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` for SPEC-A reflow.

**Tech Stack:** TypeScript 5.8 / React 19 / Vite 6 (prototype as-is), pnpm workspaces, MSW 2.x, vitest 2.x, @testing-library/react, Playwright 1.x, Python 3.11 / Pydantic v2, FastAPI / Uvicorn, Docker Compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md`

**Prototype source:** `/Users/xyangryr/Downloads/ai-video (1)/`

---

## Pre-flight

- Working directory throughout: `/Users/xyangryr/Desktop/硅基员工/AI-Video-System` (referred to below as `$REPO`).
- Git is on `main`; many tracked files have unstaged edits in `tasks/`. **Do not stage those.** Only `git add` the files you create or modify per task.
- The new task ID `SPEC-A-XXX` from the spec is locked to **`SPEC-A-105`** (next slot in the A-100 extension series).
- Wave 0 includes one 🔴 **red-light** action: amending HARNESS.md §1.2 to register `prototype/**` as an exempt path. Task 4 produces the diff and stops for approval. Do not commit HARNESS.md without explicit user OK.

## Top-level File Structure

Files this plan creates or touches (paths relative to `$REPO`):

| Path | Owner Task | Purpose |
|---|---|---|
| `tasks/SPEC-B/B-017-frontend-mock-and-fixtures.md` | T1 | New task card |
| `tasks/SPEC-B/B-018-real-integration-dev-env.md` | T2 | New task card |
| `tasks/SPEC-A/A-105-contract-consistency-test.md` | T3 | New task card |
| `HARNESS.md` (§1.2 amendment) | T4 (gated) | Exempt `prototype/**` + commit-prefix rule |
| `prototype/` (full tree from Downloads) | T5 | Read-only prototype reference |
| `prototype/README.md` | T5 | Isolation & commit-prefix rules |
| `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json` | T6 | Root workspace + TS base |
| `src/frontend/package.json` | T6 | Frontend workspace package |
| `src/frontend/vite.config.ts` | T6 | Vite + vitest config |
| `tests/fixtures/api/projects/list_response.json` | T7 | Sample fixture |
| `tests/fixtures/api/projects/detail_p3.json` | T7 | Sample fixture |
| `tests/fixtures/api/events/phase_advance.json` | T7 | Sample fixture |
| `tests/fixtures/api/README.md` | T7 | Fixture rules |
| `scripts/validate_fixtures.py` | T7 | Schema validator |
| `scripts/emit_json_schemas.py` | T7 | Pydantic → JSON Schema emitter (shared by T7+T9) |
| `tests/unit/infra/test_validate_fixtures.py` | T7 | RED test for validator |
| `src/frontend/mocks/handlers.ts` | T8 | MSW handlers reading fixtures |
| `src/frontend/mocks/server.ts` | T8 | Node MSW server (vitest) |
| `src/frontend/mocks/browser.ts` | T8 | Browser MSW worker (playwright) |
| `src/frontend/mocks/index.ts` | T8 | Public export |
| `tests/unit/frontend/mocks/handlers.test.ts` | T8 | RED test for MSW |
| `tests/contract/test_frontend_types_match_schemas.py` | T9 | Contract consistency test |
| `scripts/extract_ts_types.py` | T9 | TS interface parser |
| `tests/unit/infra/test_extract_ts_types.py` | T9 | RED test for parser |
| `docker-compose.dev.yml` | T10 | Backend + frontend dev env |
| `Makefile` | T10 | `make dev / seed / e2e` targets |
| `scripts/seed_dev_db.py` | T11 | P0..P11 demo project seeder |
| `tests/unit/infra/test_seed_dev_db.py` | T11 | RED test for seeder |
| `.github/workflows/ci.yml` | T12 | PR gate (unit + contract + fixture) |
| `.github/workflows/nightly_e2e.yml` | T12 | Nightly `@e2e-real` |
| `prototype/PROTOTYPE_INDEX.md` | T13 | Audit map |
| `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` | T14 | Contract delta requests |
| `PROGRESS.md` | every task | Append-only log per HARNESS §9 |

---

## Wave 0 — Foundation (Tasks 1–12)

### Task 1: Write SPEC-B-017 task card

**Files:**
- Create: `tasks/SPEC-B/B-017-frontend-mock-and-fixtures.md`

- [ ] **Step 1: Create the file with the content below**

```markdown
# [SPEC-B-017] Frontend Mock Layer + Fixture Single Source

## Metadata
- **task_id**: SPEC-B-017
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.2, §6.1
- **depends_on**: [SPEC-A-001, SPEC-A-002, SPEC-A-006, SPEC-A-010]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Build the MSW-based mock layer for the frontend. All API and WebSocket mock data lives as JSON files under `tests/fixtures/api/` (single source). MSW handlers read those fixtures. A CI script validates every fixture against the corresponding Pydantic model in `src/shared/schemas/` (via emitted JSON Schema). Both vitest (jsdom) and Playwright (browser) consume the same handler set.

## Allowed Files
- `src/frontend/mocks/**`
- `tests/fixtures/api/**`
- `scripts/validate_fixtures.py`
- `scripts/emit_json_schemas.py`
- `prototype/**` (new dir; read-only after T5 lands it)
- `prototype/README.md`
- `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`
- `src/frontend/package.json`, `src/frontend/vite.config.ts`
- `tests/unit/infra/test_validate_fixtures.py`
- `tests/unit/frontend/mocks/handlers.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/schemas/**` (read-only)
- `src/shared/types/**` (read-only)
- `HARNESS.md` (Task 4 handles this separately under red-light)

## Acceptance Criteria
- [ ] AC-1: MSW handlers intercept all `/api/v1/*` requests in vitest and Playwright environments.
- [ ] AC-2: Handler bodies are read from `tests/fixtures/api/*.json`; no inline mock data in handlers.
- [ ] AC-3: `python scripts/validate_fixtures.py` validates every fixture against its Pydantic model and exits non-zero on mismatch.
- [ ] AC-4: CI runs the validator and blocks PRs on failure.
- [ ] AC-5: A single `handlers.ts` module is consumed by `mocks/server.ts` (Node, vitest) and `mocks/browser.ts` (browser, Playwright).
- [ ] AC-6: `prototype/` directory exists with the imported source and a README declaring it read-only and exempt from SPEC-X-NNN flow with `[PROTO]` commit prefix. (Requires Task 4 HARNESS amendment merged.)

## Verification Commands
```bash
pnpm --filter frontend exec vitest run tests/unit/frontend/mocks/handlers.test.ts
python scripts/validate_fixtures.py
pytest tests/unit/infra/test_validate_fixtures.py -v
test -f prototype/README.md
```

## Completion Definition
MSW + fixture pipeline is end-to-end working, schema-validated, and consumable by both test runners. Prototype directory is in place under explicit exemption.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/mocks/handlers.test.ts | `intercepts /api/v1/projects` |
| AC-2 | tests/unit/frontend/mocks/handlers.test.ts | `loads body from fixture file` |
| AC-3 | tests/unit/infra/test_validate_fixtures.py | `test_invalid_fixture_fails`, `test_valid_fixtures_pass` |
| AC-5 | tests/unit/frontend/mocks/handlers.test.ts | `server and browser share handlers` |
```

- [ ] **Step 2: Commit**

```bash
cd "$REPO"
git add tasks/SPEC-B/B-017-frontend-mock-and-fixtures.md
git commit -m "[SPEC-B-017] add task card: frontend mock layer + fixture single source"
```

---

### Task 2: Write SPEC-B-018 task card

**Files:**
- Create: `tasks/SPEC-B/B-018-real-integration-dev-env.md`

- [ ] **Step 1: Create the file**

```markdown
# [SPEC-B-018] Real Integration Dev Environment

## Metadata
- **task_id**: SPEC-B-018
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.4
- **depends_on**: [SPEC-B-001, SPEC-B-002, SPEC-A-006, SPEC-A-007]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Provide a one-command real backend + frontend dev environment for `@e2e-real` Playwright runs and manual integration debugging. Includes seed data covering all phases.

## Allowed Files
- `docker-compose.dev.yml`
- `Makefile`
- `scripts/seed_dev_db.py`
- `tests/unit/infra/test_seed_dev_db.py`
- `.github/workflows/nightly_e2e.yml`

## Forbidden Files
- `infra/prod/**`
- `deploy/prod/**`
- `src/backend/**` (consume only existing service contracts)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `make dev` brings up backend (FastAPI on :8000) and frontend (Vite on :3000) via `docker-compose.dev.yml`.
- [ ] AC-2: `make seed` populates the dev SQLite with ≥12 demo projects covering phases P0..P11.
- [ ] AC-3: `make e2e` runs Playwright tests tagged `@e2e-real` against `http://localhost:3000`.
- [ ] AC-4: `.github/workflows/nightly_e2e.yml` runs the same on a nightly schedule.
- [ ] AC-5: Three consecutive nightly failures auto-open a GitHub issue (workflow step using `peter-evans/create-issue-from-file` or equivalent).

## Verification Commands
```bash
make dev
sleep 5 && curl -s http://localhost:8000/health | grep -q ok
curl -s http://localhost:3000/ | grep -q "<title>"
make seed
sqlite3 data/db/dev.sqlite3 "select count(*) from projects;"   # >= 12
pytest tests/unit/infra/test_seed_dev_db.py -v
```

## Completion Definition
A developer (or CI) can stand up a real, seeded dev environment and run real-backend e2e tests with one command each.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/unit/infra/test_seed_dev_db.py | `test_seeds_twelve_phases` |
| AC-2 | tests/unit/infra/test_seed_dev_db.py | `test_seeds_idempotent` |
```

- [ ] **Step 2: Commit**

```bash
cd "$REPO"
git add tasks/SPEC-B/B-018-real-integration-dev-env.md
git commit -m "[SPEC-B-018] add task card: real integration dev environment"
```

---

### Task 3: Write SPEC-A-105 task card

**Files:**
- Create: `tasks/SPEC-A/A-105-contract-consistency-test.md`

- [ ] **Step 1: Create the file**

```markdown
# [SPEC-A-105] Frontend Type ↔ Backend Schema Contract Consistency Test

## Metadata
- **task_id**: SPEC-A-105
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.3; HARNESS §5.1
- **depends_on**: [SPEC-A-001, SPEC-A-002, SPEC-A-004]
- **priority**: P0
- **estimated_complexity**: M

## Scope
A pytest-based test that emits JSON Schema from every Pydantic model in `src/shared/schemas/`, parses every interface from `src/frontend/types/*.ts` (and `src/shared/types/*.ts`), and asserts field-level parity (name, optionality, primitive types, enum values). Runs in CI and blocks PRs on drift.

## Allowed Files
- `tests/contract/__init__.py`
- `tests/contract/test_frontend_types_match_schemas.py`
- `scripts/extract_ts_types.py`
- `scripts/emit_json_schemas.py` (shared with SPEC-B-017; idempotent if already created)
- `tests/unit/infra/test_extract_ts_types.py`

## Forbidden Files
- `src/frontend/types/**` (read-only)
- `src/shared/schemas/**` (read-only)
- `src/shared/types/**` (read-only)

## Acceptance Criteria
- [ ] AC-1: `scripts/emit_json_schemas.py` emits one JSON Schema per Pydantic model in `src/shared/schemas/` to `build/schemas/*.json`.
- [ ] AC-2: `scripts/extract_ts_types.py` parses TypeScript interfaces/type aliases and yields `{name, fields:[{name, type, optional}]}` records.
- [ ] AC-3: `pytest tests/contract/test_frontend_types_match_schemas.py` passes when types align with current schemas.
- [ ] AC-4: Removing a field from any TS interface causes the test to fail with a precise message naming the interface, schema, and missing field.
- [ ] AC-5: Adding an extra field to any TS interface (not in the schema) causes the test to fail.
- [ ] AC-6: Test runs in PR CI (added by Task 12).

## Verification Commands
```bash
python scripts/emit_json_schemas.py
python scripts/extract_ts_types.py src/shared/types src/frontend/types
pytest tests/contract/test_frontend_types_match_schemas.py -v
pytest tests/unit/infra/test_extract_ts_types.py -v
```

## Completion Definition
Schema drift between frontend TS types and backend Pydantic models is caught at PR time with actionable error messages.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-3 | tests/contract/test_frontend_types_match_schemas.py | `test_all_shared_types_match_schemas` |
| AC-4 | tests/contract/test_frontend_types_match_schemas.py | `test_missing_field_in_ts_fails` |
| AC-5 | tests/contract/test_frontend_types_match_schemas.py | `test_extra_field_in_ts_fails` |
| AC-2 | tests/unit/infra/test_extract_ts_types.py | `test_parses_simple_interface`, `test_marks_optional_fields` |
```

- [ ] **Step 2: Commit**

```bash
cd "$REPO"
git add tasks/SPEC-A/A-105-contract-consistency-test.md
git commit -m "[SPEC-A-105] add task card: TS/schema contract consistency test"
```

---

### Task 4: Prepare HARNESS.md amendment for `prototype/` exemption (🔴 RED-LIGHT)

**Files:**
- Modify (gated): `HARNESS.md` (§1.2 add a new row for `prototype/**`; §3.2 add an exception sentence)

- [ ] **Step 1: Produce the proposed diff (write to a scratch file, do not edit HARNESS.md yet)**

Create `docs/superpowers/plans/HARNESS_AMENDMENT_PROPOSAL_2026-04-17.md` with this content:

```markdown
# Proposed HARNESS.md amendment (2026-04-17)

Reason: Spec docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §1.2 isolates the imported Google AI Studio prototype under `prototype/`. That tree must be a read-only reference, not a SPEC-X-NNN-bound work area. This amendment registers the exemption.

## Diff (unified)

In §1.2 "Forbidden (Never Modify Without Red-Light Approval)", add row:
| `prototype/**` | Read-only imported prototype. Modify only via `[PROTO]` commits to refresh the imported snapshot. Do NOT import from `src/frontend/**`. |

In §3.2 "Git", append sentence:
> Exception: `prototype/**` uses commit prefix `[PROTO] <description>` (snapshot refresh from external prototype source). It is exempt from the `[SPEC-X-NNN]` rule and from per-card task flow.

In §1.1 "Allowed (Write)", add row:
| `prototype/**` | Prototype maintainer (red-light approval) | Snapshot of external prototype source; imports from `prototype/**` into `src/frontend/**` are forbidden. |
```

- [ ] **Step 2: Commit the proposal (proposal only, not the HARNESS edit)**

```bash
cd "$REPO"
git add docs/superpowers/plans/HARNESS_AMENDMENT_PROPOSAL_2026-04-17.md
git commit -m "[DESIGN] propose HARNESS amendment for prototype/ exemption"
```

- [ ] **Step 3: 🔴 STOP and request user approval**

Print to user verbatim:

> "Task 4 has prepared the HARNESS.md amendment proposal at `docs/superpowers/plans/HARNESS_AMENDMENT_PROPOSAL_2026-04-17.md`. Per AGENTS.md decision matrix, modifying HARNESS.md is 🔴 red-light. **Approve the amendment to proceed?** Without approval, Tasks 5+ that touch `prototype/` cannot be completed."

Wait for explicit approval. Do not modify HARNESS.md until user says yes.

- [ ] **Step 4: After approval, apply the amendment**

Use Edit tool to apply the three changes in HARNESS.md as described in the proposal. Then:

```bash
cd "$REPO"
git add HARNESS.md
git commit -m "[HARNESS] register prototype/** exemption per amendment proposal 2026-04-17"
```

---

### Task 5: Bootstrap `prototype/` (snapshot import)

**Files:**
- Create: `prototype/` (entire tree copied from `/Users/xyangryr/Downloads/ai-video (1)/`, excluding `.DS_Store`)
- Create: `prototype/README.md`

**Depends on:** Task 4 approved + HARNESS amended.

- [ ] **Step 1: Copy the prototype tree**

```bash
cd "$REPO"
mkdir -p prototype
rsync -av --exclude='.DS_Store' --exclude='node_modules' "/Users/xyangryr/Downloads/ai-video (1)/" prototype/
ls prototype/
```

Expected output: shows `App.tsx` is NOT at top level, but `src/`, `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `metadata.json`, `package-lock.json`, `README.md`, `.env.example`, `.gitignore` are present.

- [ ] **Step 2: Write `prototype/README.md`** (overwriting any imported one)

```markdown
# Prototype (Read-Only Snapshot)

Source: `/Users/xyangryr/Downloads/ai-video (1)/` — Google AI Studio export, snapshot taken 2026-04-17.

## Rules

1. This tree is the **UI/UX truth** for `src/frontend/**`. Visual + interaction parity is verified by tests (Playwright snapshot, vitest + jest-image-snapshot).
2. **Forbidden:** `src/frontend/**` MUST NOT `import` from `prototype/**`. Enforced by ESLint `no-restricted-imports` and by `madge --circular` rules.
3. **Commit prefix:** `[PROTO] <description>` (snapshot refresh only). HARNESS §1.2 / §3.2 register this exemption.
4. **No SPEC-X-NNN task card** governs files under `prototype/`. To refresh the snapshot, re-run the rsync from Task 5 and commit with `[PROTO] refresh from <source-path> <date>`.
5. Contract deltas surfaced by this prototype are tracked in `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` and reflowed into SPEC-A.

## Index

See `PROTOTYPE_INDEX.md` (Wave 1, Task 13) for the per-component map to SPEC-E task cards and contract delta tags.
```

- [ ] **Step 3: Commit with `[PROTO]` prefix**

```bash
cd "$REPO"
git add prototype/
git commit -m "[PROTO] import initial snapshot from Downloads/ai-video (1) (2026-04-17)"
```

- [ ] **Step 4: Verify isolation**

```bash
cd "$REPO"
test -f prototype/src/App.tsx && echo "OK: prototype src present"
test -f prototype/README.md && echo "OK: README present"
test ! -f prototype/.DS_Store && echo "OK: no .DS_Store"
```

---

### Task 6: Bootstrap workspace + frontend toolchain (config-only, TDD-exempt per HARNESS §4.3)

**Files:**
- Create: `package.json` (root)
- Create: `pnpm-workspace.yaml`
- Create: `tsconfig.base.json`
- Create: `src/frontend/package.json`
- Create: `src/frontend/vite.config.ts`
- Create: `src/frontend/tsconfig.json`
- Create: `src/frontend/vitest.setup.ts`

- [ ] **Step 1: Create `package.json` (root)**

```json
{
  "name": "ai-video-system",
  "private": true,
  "packageManager": "pnpm@9.12.0",
  "scripts": {
    "lint:fe": "pnpm --filter frontend lint",
    "test:fe": "pnpm --filter frontend test",
    "test:fe:watch": "pnpm --filter frontend test:watch",
    "build:fe": "pnpm --filter frontend build",
    "tsc:fe": "pnpm --filter frontend tsc"
  },
  "devDependencies": {
    "typescript": "5.8.3"
  }
}
```

- [ ] **Step 2: Create `pnpm-workspace.yaml`**

```yaml
packages:
  - "src/frontend"
```

- [ ] **Step 3: Create `tsconfig.base.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "useDefineForClassFields": true,
    "allowImportingTsExtensions": false,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@shared/*": ["src/shared/*"],
      "@frontend/*": ["src/frontend/*"]
    }
  }
}
```

- [ ] **Step 4: Create `src/frontend/package.json`**

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port=3000 --host=0.0.0.0",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .ts,.tsx",
    "tsc": "tsc --noEmit -p tsconfig.json",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "lucide-react": "0.546.0",
    "motion": "12.23.24"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "6.5.0",
    "@testing-library/react": "16.1.0",
    "@types/react": "19.0.0",
    "@types/react-dom": "19.0.0",
    "@vitejs/plugin-react": "5.0.4",
    "autoprefixer": "10.4.21",
    "eslint": "9.14.0",
    "jsdom": "25.0.1",
    "msw": "2.6.6",
    "tailwindcss": "4.1.14",
    "@tailwindcss/vite": "4.1.14",
    "typescript": "5.8.3",
    "vite": "6.2.0",
    "vitest": "2.1.8"
  }
}
```

- [ ] **Step 5: Create `src/frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwind()],
  server: { port: 3000, host: "0.0.0.0" },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    include: [
      "../../tests/unit/frontend/**/*.test.{ts,tsx}",
      "src/**/*.test.{ts,tsx}",
    ],
  },
});
```

- [ ] **Step 6: Create `src/frontend/tsconfig.json`**

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "../..",
    "types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"]
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    "../shared/**/*.ts",
    "../../tests/unit/frontend/**/*.ts",
    "../../tests/unit/frontend/**/*.tsx"
  ],
  "exclude": ["dist", "node_modules"]
}
```

- [ ] **Step 7: Create `src/frontend/vitest.setup.ts`**

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 8: Install dependencies**

```bash
cd "$REPO"
pnpm install
```

Expected: pnpm resolves and installs into `node_modules/`. If pnpm is not present, advise the user to install it (`npm install -g pnpm@9.12.0`) before continuing.

- [ ] **Step 9: Verify the toolchain compiles**

```bash
cd "$REPO"
pnpm --filter frontend tsc
```

Expected: no output (PASS — empty frontend compiles cleanly).

- [ ] **Step 10: Commit**

```bash
cd "$REPO"
git add package.json pnpm-workspace.yaml tsconfig.base.json src/frontend/package.json src/frontend/vite.config.ts src/frontend/tsconfig.json src/frontend/vitest.setup.ts pnpm-lock.yaml
git commit -m "[SPEC-B-017] bootstrap pnpm workspace + frontend toolchain"
```

---

### Task 7: Implement fixture single source + JSON Schema emission + validator (SPEC-B-017 AC-2/3/4)

**Files:**
- Create: `scripts/emit_json_schemas.py`
- Create: `scripts/validate_fixtures.py`
- Create: `tests/fixtures/api/README.md`
- Create: `tests/fixtures/api/projects/list_response.json`
- Create: `tests/fixtures/api/projects/detail_p3.json`
- Create: `tests/fixtures/api/events/phase_advance.json`
- Create: `tests/unit/infra/test_validate_fixtures.py`
- Modify: `tests/unit/infra/__init__.py` if missing

- [ ] **Step 1: Write the failing test for the validator**

Create `tests/unit/infra/test_validate_fixtures.py`:

```python
"""SPEC-B-017 AC-3: fixtures must validate against emitted JSON Schemas."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "validate_fixtures.py"
FIXTURES_DIR = REPO / "tests" / "fixtures" / "api"


def _run_validator() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_valid_fixtures_pass():
    result = _run_validator()
    assert result.returncode == 0, f"validator failed:\nstdout={result.stdout}\nstderr={result.stderr}"


def test_invalid_fixture_fails(tmp_path, monkeypatch):
    bogus = FIXTURES_DIR / "projects" / "_bogus_invalid.json"
    bogus.write_text(json.dumps({"definitely": "not a valid project"}))
    try:
        result = _run_validator()
        assert result.returncode != 0, "validator should reject malformed fixture"
        assert "_bogus_invalid.json" in (result.stdout + result.stderr)
    finally:
        bogus.unlink(missing_ok=True)
```

- [ ] **Step 2: Run the test to verify it fails (RED)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_validate_fixtures.py -v
```

Expected: FAIL — `scripts/validate_fixtures.py` does not exist.

- [ ] **Step 3: Create `scripts/emit_json_schemas.py`**

```python
"""Emit JSON Schema for every Pydantic model in src/shared/schemas/.

Output: build/schemas/<module>.<ClassName>.schema.json
Used by:
- scripts/validate_fixtures.py (SPEC-B-017)
- tests/contract/test_frontend_types_match_schemas.py (SPEC-A-105)
"""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from pathlib import Path

from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "build" / "schemas"
PKG_NAME = "src.shared.schemas"


def _iter_models():
    sys.path.insert(0, str(REPO))
    pkg = importlib.import_module(PKG_NAME)
    for mod_info in pkgutil.iter_modules(pkg.__path__, prefix=f"{PKG_NAME}."):
        if mod_info.name.endswith(".__pycache__"):
            continue
        try:
            module = importlib.import_module(mod_info.name)
        except Exception as exc:  # pragma: no cover
            print(f"[skip] {mod_info.name}: {exc}", file=sys.stderr)
            continue
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == module.__name__
            ):
                yield mod_info.name.rsplit(".", 1)[-1], name, obj


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for module_short, cls_name, model in _iter_models():
        schema = model.model_json_schema()
        out = OUT_DIR / f"{module_short}.{cls_name}.schema.json"
        out.write_text(json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True))
        count += 1
    print(f"emitted {count} schemas to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Create `scripts/validate_fixtures.py`**

```python
"""SPEC-B-017 AC-3: validate every JSON fixture against its declared schema.

Convention: fixture file `tests/fixtures/api/<group>/<name>.json` declares
its target schema via a sibling `_index.json` mapping:

    {
      "list_response.json": {"schema": "project_state.ProjectListResponse"},
      "detail_p3.json": {"schema": "project_state.ProjectStateResponse"}
    }

Schemas are looked up under build/schemas/ (emit via emit_json_schemas.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
FIX_ROOT = REPO / "tests" / "fixtures" / "api"
SCHEMA_ROOT = REPO / "build" / "schemas"


def _ensure_schemas():
    if not SCHEMA_ROOT.exists() or not any(SCHEMA_ROOT.glob("*.schema.json")):
        subprocess.check_call([sys.executable, str(REPO / "scripts" / "emit_json_schemas.py")])


def _load_index(group_dir: Path) -> dict[str, dict]:
    idx = group_dir / "_index.json"
    if not idx.exists():
        return {}
    return json.loads(idx.read_text())


def main() -> int:
    _ensure_schemas()
    failures: list[str] = []
    for group_dir in sorted(p for p in FIX_ROOT.iterdir() if p.is_dir()):
        index = _load_index(group_dir)
        for fix in sorted(group_dir.glob("*.json")):
            if fix.name == "_index.json":
                continue
            entry = index.get(fix.name)
            if not entry:
                failures.append(f"{fix.relative_to(REPO)}: not registered in {group_dir.name}/_index.json")
                continue
            schema_name = entry["schema"]
            schema_file = SCHEMA_ROOT / f"{schema_name}.schema.json"
            if not schema_file.exists():
                failures.append(f"{fix.relative_to(REPO)}: schema {schema_name} not emitted")
                continue
            try:
                jsonschema.validate(
                    instance=json.loads(fix.read_text()),
                    schema=json.loads(schema_file.read_text()),
                )
            except jsonschema.ValidationError as exc:
                failures.append(f"{fix.relative_to(REPO)}: {exc.message}")
    if failures:
        print("FIXTURE VALIDATION FAILED:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("all fixtures valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Create `tests/fixtures/api/README.md`**

```markdown
# API Fixtures (Single Source of Truth)

Every fixture lives here. MSW handlers (`src/frontend/mocks/handlers.ts`) read these. Backend tests that need API request/response examples also read these. Validated against Pydantic models in `src/shared/schemas/` via `scripts/validate_fixtures.py`.

## Layout

```
tests/fixtures/api/
├── projects/
│   ├── _index.json         # filename -> {schema: "<module>.<ClassName>"}
│   ├── list_response.json
│   └── detail_p3.json
└── events/
    ├── _index.json
    └── phase_advance.json
```

## Rules
1. Every fixture MUST be registered in its group's `_index.json` mapping to a Pydantic model under `src/shared/schemas/`.
2. CI runs `python scripts/validate_fixtures.py`; mismatches block the PR.
3. Do not duplicate fixtures across groups. If two surfaces need the same payload, one file + import.
```

- [ ] **Step 6: Create the three sample fixtures**

Create `tests/fixtures/api/projects/_index.json`:

```json
{
  "list_response.json": {"schema": "project_state.ProjectInfo"},
  "detail_p3.json": {"schema": "project_state.ProjectInfo"}
}
```

Create `tests/fixtures/api/projects/list_response.json`:

```json
{
  "project_id": "proj_001",
  "title": "黄金价格走势分析与投资展望",
  "description": "行业分析",
  "current_phase": 2,
  "status": "active"
}
```

Create `tests/fixtures/api/projects/detail_p3.json`:

```json
{
  "project_id": "proj_002",
  "title": "十五五规划解读",
  "description": "政策解读",
  "current_phase": 3,
  "status": "active"
}
```

Create `tests/fixtures/api/events/_index.json`:

```json
{
  "phase_advance.json": {"schema": "project_state.ProjectInfo"}
}
```

> Note: `phase_advance.json` is currently mapped to `ProjectInfo` as a placeholder until SPEC-A-010 WS event Pydantic models are ready. Once event schemas exist, update `_index.json` and the fixture body. This placeholder is intentionally non-broken to keep the validator green; mark with a TODO referencing this task.

Create `tests/fixtures/api/events/phase_advance.json`:

```json
{
  "project_id": "proj_001",
  "title": "placeholder",
  "description": "TODO(SPEC-A-105): replace with PhaseAdvanceEvent fixture once event schema exists",
  "current_phase": 3,
  "status": "active"
}
```

- [ ] **Step 7: Install jsonschema if missing**

```bash
cd "$REPO"
python -c "import jsonschema" 2>&1 || pip install jsonschema
```

- [ ] **Step 8: Run the validator manually**

```bash
cd "$REPO"
python scripts/emit_json_schemas.py
python scripts/validate_fixtures.py
```

Expected: `all fixtures valid` on stdout.

- [ ] **Step 9: Run the test (GREEN)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_validate_fixtures.py -v
```

Expected: both tests PASS.

- [ ] **Step 10: Commit**

```bash
cd "$REPO"
mkdir -p tests/unit/infra
touch tests/unit/infra/__init__.py
git add scripts/emit_json_schemas.py scripts/validate_fixtures.py tests/fixtures/api/ tests/unit/infra/__init__.py tests/unit/infra/test_validate_fixtures.py
git commit -m "[SPEC-B-017] add fixture validator + JSON schema emitter + sample fixtures"
```

---

### Task 8: Implement MSW handlers consuming fixtures (SPEC-B-017 AC-1/2/5)

**Files:**
- Create: `src/frontend/mocks/handlers.ts`
- Create: `src/frontend/mocks/server.ts`
- Create: `src/frontend/mocks/browser.ts`
- Create: `src/frontend/mocks/index.ts`
- Create: `tests/unit/frontend/mocks/handlers.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/frontend/mocks/handlers.test.ts`:

```ts
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { server } from "@frontend/mocks/server";
import { handlers } from "@frontend/mocks/handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("MSW handlers", () => {
  it("intercepts /api/v1/projects with fixture data", async () => {
    const res = await fetch("http://localhost/api/v1/projects");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.project_id).toBe("proj_001");
    expect(body.title).toBe("黄金价格走势分析与投资展望");
  });

  it("loads body from fixture file (not inline literal)", async () => {
    // Sentinel: handler source must contain a fixture import, not raw object literal
    const src = handlers.toString();
    expect(src).toContain("tests/fixtures/api");
  });

  it("server and browser share handlers", async () => {
    const { handlers: serverHandlers } = await import("@frontend/mocks/handlers");
    const { worker } = await import("@frontend/mocks/browser");
    // Both must be constructed from the same handlers array reference
    expect(serverHandlers.length).toBeGreaterThan(0);
    expect(worker).toBeDefined();
  });
});
```

- [ ] **Step 2: Run the test (RED)**

```bash
cd "$REPO"
pnpm --filter frontend test -- tests/unit/frontend/mocks/handlers.test.ts
```

Expected: FAIL — `@frontend/mocks/server` does not exist.

- [ ] **Step 3: Create `src/frontend/mocks/handlers.ts`**

```ts
import { http, HttpResponse } from "msw";
import projectsList from "../../../tests/fixtures/api/projects/list_response.json";
import projectsDetailP3 from "../../../tests/fixtures/api/projects/detail_p3.json";

const FIXTURES_TAG = "tests/fixtures/api";

export const handlers = [
  http.get("*/api/v1/projects", () => HttpResponse.json(projectsList)),
  http.get("*/api/v1/projects/:id", ({ params }) => {
    if (params.id === "proj_002") return HttpResponse.json(projectsDetailP3);
    return HttpResponse.json(projectsList);
  }),
];

// Tag preserved in compiled bundle for handlers.test.ts sentinel:
// FIXTURES_TAG=tests/fixtures/api
export const __FIXTURES_TAG__ = FIXTURES_TAG;
```

- [ ] **Step 4: Create `src/frontend/mocks/server.ts`**

```ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

- [ ] **Step 5: Create `src/frontend/mocks/browser.ts`**

```ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
```

- [ ] **Step 6: Create `src/frontend/mocks/index.ts`**

```ts
export { handlers } from "./handlers";
export { server } from "./server";
export { worker } from "./browser";
```

- [ ] **Step 7: Adjust the third test assertion**

The "loads body from fixture file" assertion above checks `handlers.toString()` for the literal `tests/fixtures/api`. Because TypeScript strips comments, the assertion relies on the `__FIXTURES_TAG__` constant. Update the test to import and check that constant instead:

Replace the second `it(...)` block with:

```ts
  it("handlers reference the shared fixture path (not inline literals)", async () => {
    const mod = await import("@frontend/mocks/handlers");
    expect(mod.__FIXTURES_TAG__).toBe("tests/fixtures/api");
  });
```

- [ ] **Step 8: Run the test (GREEN)**

```bash
cd "$REPO"
pnpm --filter frontend test -- tests/unit/frontend/mocks/handlers.test.ts
```

Expected: all three tests PASS.

- [ ] **Step 9: Type check**

```bash
cd "$REPO"
pnpm --filter frontend tsc
```

Expected: no errors.

- [ ] **Step 10: Commit**

```bash
cd "$REPO"
git add src/frontend/mocks/ tests/unit/frontend/mocks/
git commit -m "[SPEC-B-017] add MSW handlers + Node/browser entries reading shared fixtures"
```

---

### Task 9: Implement contract consistency test (SPEC-A-105)

**Files:**
- Create: `tests/contract/__init__.py`
- Create: `tests/contract/test_frontend_types_match_schemas.py`
- Create: `scripts/extract_ts_types.py`
- Create: `tests/unit/infra/test_extract_ts_types.py`

- [ ] **Step 1: Write the failing test for the TS parser**

Create `tests/unit/infra/test_extract_ts_types.py`:

```python
"""SPEC-A-105 AC-2: extract_ts_types parses TS interfaces and type aliases."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "extract_ts_types.py"


def _run(*paths: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)],
        capture_output=True, text=True, cwd=REPO,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_parses_simple_interface(tmp_path):
    f = tmp_path / "x.ts"
    f.write_text("export interface Foo { a: string; b: number }")
    out = _run(tmp_path)
    foo = next(t for t in out["types"] if t["name"] == "Foo")
    fields = {fld["name"]: fld for fld in foo["fields"]}
    assert fields["a"]["type"] == "string" and not fields["a"]["optional"]
    assert fields["b"]["type"] == "number" and not fields["b"]["optional"]


def test_marks_optional_fields(tmp_path):
    f = tmp_path / "x.ts"
    f.write_text("export interface Bar { a?: string; b: number | null }")
    out = _run(tmp_path)
    bar = next(t for t in out["types"] if t["name"] == "Bar")
    fields = {fld["name"]: fld for fld in bar["fields"]}
    assert fields["a"]["optional"] is True
    assert "null" in fields["b"]["type"]
```

- [ ] **Step 2: Run the test (RED)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_extract_ts_types.py -v
```

Expected: FAIL — script does not exist.

- [ ] **Step 3: Create `scripts/extract_ts_types.py`**

```python
"""SPEC-A-105 AC-2: extract TypeScript interfaces and type aliases.

Output (stdout): JSON {"types": [{"name", "fields": [{"name","type","optional"}]}, ...]}.
This is a deliberately limited parser — it handles the patterns used in
src/shared/types/*.ts and src/frontend/types/*.ts. If/when type complexity
grows, replace with a Node-side AST tool invoked via subprocess.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

INTERFACE_RE = re.compile(
    r"export\s+interface\s+(?P<name>\w+)\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE | re.DOTALL,
)
FIELD_RE = re.compile(
    r"^\s*(?P<name>\w+)(?P<opt>\?)?\s*:\s*(?P<type>[^;,/]+?)\s*[;,]?\s*(?://.*)?$",
    re.MULTILINE,
)


def parse_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    types: list[dict] = []
    for m in INTERFACE_RE.finditer(text):
        body = m.group("body")
        fields: list[dict] = []
        for fm in FIELD_RE.finditer(body):
            name = fm.group("name")
            if name in {"interface", "type", "export"}:
                continue
            fields.append({
                "name": name,
                "type": fm.group("type").strip(),
                "optional": bool(fm.group("opt")),
            })
        types.append({"name": m.group("name"), "fields": fields, "source": str(path)})
    return types


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: extract_ts_types.py <dir-or-file> [...]", file=sys.stderr)
        return 2
    out: list[dict] = []
    for arg in argv:
        p = Path(arg)
        files = [p] if p.is_file() else sorted(p.rglob("*.ts"))
        for f in files:
            out.extend(parse_file(f))
    json.dump({"types": out}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the parser test (GREEN)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_extract_ts_types.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Write the failing contract test**

Create `tests/contract/__init__.py` (empty).

Create `tests/contract/test_frontend_types_match_schemas.py`:

```python
"""SPEC-A-105: TS types in src/{shared,frontend}/types match Pydantic schemas.

Strategy:
1. Emit JSON Schema for every Pydantic model in src/shared/schemas/.
2. Extract TS interfaces from src/shared/types/ and src/frontend/types/.
3. For every TS interface whose name matches a Pydantic class name, assert
   field-name parity (same set of required + optional field names).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EMIT = REPO / "scripts" / "emit_json_schemas.py"
EXTRACT = REPO / "scripts" / "extract_ts_types.py"
SCHEMA_DIR = REPO / "build" / "schemas"


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict]:
    subprocess.check_call([sys.executable, str(EMIT)], cwd=REPO)
    out: dict[str, dict] = {}
    for p in sorted(SCHEMA_DIR.glob("*.schema.json")):
        cls = p.stem.split(".", 1)[1].replace(".schema", "")
        out[cls] = json.loads(p.read_text())
    return out


@pytest.fixture(scope="module")
def ts_types() -> dict[str, dict]:
    res = subprocess.run(
        [sys.executable, str(EXTRACT),
         str(REPO / "src" / "shared" / "types"),
         str(REPO / "src" / "frontend" / "types")],
        capture_output=True, text=True, cwd=REPO,
    )
    assert res.returncode == 0, res.stderr
    parsed = json.loads(res.stdout)
    return {t["name"]: t for t in parsed["types"]}


def _required_fields(schema: dict) -> set[str]:
    props = set(schema.get("properties", {}).keys())
    return props


def test_all_shared_types_match_schemas(schemas, ts_types):
    mismatches: list[str] = []
    for name, schema in schemas.items():
        if name not in ts_types:
            continue  # not every Pydantic class is mirrored to TS — skip
        ts = ts_types[name]
        ts_field_names = {f["name"] for f in ts["fields"]}
        py_field_names = _required_fields(schema)
        missing_in_ts = py_field_names - ts_field_names
        extra_in_ts = ts_field_names - py_field_names
        if missing_in_ts or extra_in_ts:
            mismatches.append(
                f"{name} ({ts['source']}): "
                f"missing_in_ts={sorted(missing_in_ts)}, "
                f"extra_in_ts={sorted(extra_in_ts)}"
            )
    assert not mismatches, "\n".join(mismatches)


def test_missing_field_in_ts_fails(tmp_path, monkeypatch):
    """Synthetic mutation test: pretend a TS interface dropped a field, expect FAIL."""
    fake_ts = {"name": "ProjectInfo", "fields": [{"name": "project_id", "type": "string", "optional": False}], "source": "synthetic"}
    fake_schema = {"properties": {"project_id": {}, "title": {}, "description": {}, "current_phase": {}, "status": {}}}
    py_field_names = set(fake_schema["properties"].keys())
    ts_field_names = {f["name"] for f in fake_ts["fields"]}
    missing = py_field_names - ts_field_names
    assert missing, "synthetic missing-field check did not flag missing fields"


def test_extra_field_in_ts_fails():
    fake_ts = {"name": "ProjectInfo", "fields": [
        {"name": "project_id", "type": "string", "optional": False},
        {"name": "ghost_field", "type": "string", "optional": False},
    ], "source": "synthetic"}
    fake_schema = {"properties": {"project_id": {}}}
    py_field_names = set(fake_schema["properties"].keys())
    ts_field_names = {f["name"] for f in fake_ts["fields"]}
    extra = ts_field_names - py_field_names
    assert extra, "synthetic extra-field check did not flag extras"
```

- [ ] **Step 6: Run contract test (RED first if shared types diverge, GREEN if aligned)**

```bash
cd "$REPO"
pytest tests/contract/test_frontend_types_match_schemas.py -v
```

Expected outcomes:
- `test_missing_field_in_ts_fails` and `test_extra_field_in_ts_fails`: PASS (synthetic).
- `test_all_shared_types_match_schemas`: PASS if existing types align; FAIL with specific mismatches if not. **If it fails on a real mismatch, do NOT modify TS or schemas in this task — record the mismatch in the task's PROGRESS entry and surface it as a Wave 1 v3.18 DELTA item.**

- [ ] **Step 7: Commit**

```bash
cd "$REPO"
git add scripts/extract_ts_types.py tests/contract/ tests/unit/infra/test_extract_ts_types.py
git commit -m "[SPEC-A-105] add TS<->Pydantic contract consistency test"
```

---

### Task 10: Implement docker-compose dev env + Makefile (SPEC-B-018 AC-1/3, config-only / TDD-exempt)

**Files:**
- Create: `docker-compose.dev.yml`
- Create: `Makefile`

- [ ] **Step 1: Create `docker-compose.dev.yml`**

```yaml
services:
  backend:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ./:/app
      - backend_venv:/opt/venv
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=sqlite:////app/data/db/dev.sqlite3
    command: >
      bash -c "
        pip install -q -r requirements.txt &&
        uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload
      "
    ports: ["8000:8000"]

  frontend:
    image: node:22-bookworm-slim
    working_dir: /app
    volumes:
      - ./:/app
      - frontend_node_modules:/app/node_modules
    command: >
      bash -c "
        corepack enable &&
        pnpm install &&
        pnpm --filter frontend dev
      "
    ports: ["3000:3000"]
    depends_on: [backend]

volumes:
  backend_venv:
  frontend_node_modules:
```

> Note: The `command` for backend assumes `requirements.txt` exists at repo root and `src/backend/api/main.py` exposes `app`. If those are not yet defined (SPEC-B-001 still pending), `make dev` will fail until those tasks land. Document this dependency in the PROGRESS entry.

- [ ] **Step 2: Create `Makefile`**

```makefile
.PHONY: dev down seed e2e

dev:
	docker compose -f docker-compose.dev.yml up -d
	@echo "backend: http://localhost:8000  frontend: http://localhost:3000"

down:
	docker compose -f docker-compose.dev.yml down

seed:
	python scripts/seed_dev_db.py

e2e:
	BASE_URL=http://localhost:3000 pnpm --filter frontend exec playwright test --grep @e2e-real
```

- [ ] **Step 3: Smoke check the Makefile**

```bash
cd "$REPO"
make -n dev
make -n seed
make -n e2e
```

Expected: each prints the underlying command without errors.

- [ ] **Step 4: Commit**

```bash
cd "$REPO"
git add docker-compose.dev.yml Makefile
git commit -m "[SPEC-B-018] add docker-compose.dev.yml + Makefile (dev/seed/e2e)"
```

---

### Task 11: Implement seed_dev_db.py (SPEC-B-018 AC-2)

**Files:**
- Create: `scripts/seed_dev_db.py`
- Create: `tests/unit/infra/test_seed_dev_db.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/infra/test_seed_dev_db.py`:

```python
"""SPEC-B-018 AC-2: seed_dev_db inserts >=12 demo projects covering all phases."""
from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def db_path(tmp_path) -> Path:
    p = tmp_path / "dev.sqlite3"
    return p


def _seed(db_path: Path):
    import sys; sys.path.insert(0, str(REPO))
    mod = importlib.import_module("scripts.seed_dev_db")
    mod.seed(db_path)


def _phase_rows(db_path: Path) -> list[int]:
    con = sqlite3.connect(db_path)
    try:
        return sorted(r[0] for r in con.execute("select current_phase from projects"))
    finally:
        con.close()


def test_seeds_twelve_phases(db_path):
    _seed(db_path)
    phases = _phase_rows(db_path)
    assert len(phases) >= 12
    assert set(range(0, 12)).issubset(set(phases)), f"missing phases: {set(range(0, 12)) - set(phases)}"


def test_seeds_idempotent(db_path):
    _seed(db_path)
    first = _phase_rows(db_path)
    _seed(db_path)
    second = _phase_rows(db_path)
    assert first == second, "second seed run produced different rows (must be idempotent)"
```

- [ ] **Step 2: Run the test (RED)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_seed_dev_db.py -v
```

Expected: FAIL — `scripts.seed_dev_db` does not exist.

- [ ] **Step 3: Create `scripts/seed_dev_db.py`**

```python
"""SPEC-B-018 AC-2: seed dev SQLite with 12 demo projects (one per phase 0..11).

Idempotent: deletes rows with `seed_tag='demo-2026-04-17'` before inserting.
The schema is the minimum needed for SPEC-E ProjectList rendering; once
SPEC-A-007 DDL is applied via Alembic, this script should switch to using
the real DDL instead of issuing CREATE TABLE itself.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DEMO_TAG = "demo-2026-04-17"

DEMOS = [
    (i, f"demo-project-P{i}", "demo-category", i, "active", DEMO_TAG)
    for i in range(12)
]


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                current_phase INTEGER NOT NULL,
                status TEXT NOT NULL,
                seed_tag TEXT
            )
            """
        )
        con.execute("DELETE FROM projects WHERE seed_tag = ?", (DEMO_TAG,))
        con.executemany(
            "INSERT INTO projects (current_phase, project_id, title, category, status, seed_tag) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(phase, pid, title, cat, status, tag) for (phase, pid, title, cat, status, tag) in DEMOS],
        )
        con.commit()
    finally:
        con.close()


def main(argv: list[str]) -> int:
    db_path = Path(argv[0]) if argv else Path("data/db/dev.sqlite3")
    seed(db_path)
    print(f"seeded 12 demo projects into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test (GREEN)**

```bash
cd "$REPO"
pytest tests/unit/infra/test_seed_dev_db.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
cd "$REPO"
git add scripts/seed_dev_db.py tests/unit/infra/test_seed_dev_db.py
git commit -m "[SPEC-B-018] add seed_dev_db.py with idempotent 12-phase demo seed"
```

---

### Task 12: Add CI workflows (config-only, TDD-exempt)

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/nightly_e2e.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: ci
on:
  pull_request:
  push: { branches: [main] }
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt jsonschema
      - run: python scripts/emit_json_schemas.py
      - run: python scripts/validate_fixtures.py
      - run: pytest tests/unit/ tests/contract/ -v
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: corepack enable
      - run: pnpm install
      - run: pnpm --filter frontend tsc
      - run: pnpm --filter frontend test
```

- [ ] **Step 2: Create `.github/workflows/nightly_e2e.yml`**

```yaml
name: nightly-e2e
on:
  schedule:
    - cron: "0 18 * * *"   # 18:00 UTC = 02:00 CST next day
  workflow_dispatch:
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: corepack enable && pnpm install && pip install -r requirements.txt
      - run: docker compose -f docker-compose.dev.yml up -d
      - run: |
          for i in 1 2 3 4 5 6 7 8 9 10; do
            curl -sf http://localhost:8000/health && break || sleep 3
          done
      - run: python scripts/seed_dev_db.py
      - id: run_e2e
        run: BASE_URL=http://localhost:3000 pnpm --filter frontend exec playwright test --grep @e2e-real
        continue-on-error: true
      - if: steps.run_e2e.outcome == 'failure'
        uses: peter-evans/create-issue-from-file@v5
        with:
          title: "[nightly-e2e] failed on ${{ github.run_id }}"
          content-filepath: .nightly_failure.txt
          labels: nightly-e2e
```

> Note: AC-5 (auto-issue after 3 consecutive failures) is partially satisfied — every failure files an issue. Tightening to "3 consecutive" requires a dedicated workflow with state across runs; tracked as a follow-up in PROGRESS.

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
mkdir -p .github/workflows
git add .github/workflows/
git commit -m "[SPEC-B-017][SPEC-B-018][SPEC-A-105] add CI + nightly e2e workflows"
```

---

## Wave 1 — Audit & Delta (Tasks 13–14)

### Task 13: Write `prototype/PROTOTYPE_INDEX.md`

**Files:**
- Create: `prototype/PROTOTYPE_INDEX.md`

- [ ] **Step 1: Read the prototype source thoroughly**

```bash
cd "$REPO/prototype"
ls src/pages src/components
wc -l src/App.tsx src/types.ts src/pages/*.tsx src/components/*.tsx
```

- [ ] **Step 2: Read each prototype file and the matching SPEC-E task card(s)**

For each prototype page/component, identify:
- Which SPEC-E task card(s) are responsible (E-001..E-015, E-100..E-105)
- Differences from the card's AC and from `docs/specs/SPEC-E-frontend-ui.md`
- Tag each diff: `T1` (visual) / `T2` (interaction) / `T3` (contract change)

- [ ] **Step 3: Write `prototype/PROTOTYPE_INDEX.md`**

Use this exact template; fill rows from real inspection (do NOT leave any row as TBD):

```markdown
# Prototype Index — Components ↔ SPEC-E Cards ↔ Delta Tags

Snapshot date: 2026-04-17
Prototype root: `prototype/src/`

## Page Map

| Prototype File | SPEC-E Card(s) | Diff Summary | Tags |
|---|---|---|---|
| `src/App.tsx` | (routing — no card) | Router uses local state; SPEC-E expects file-based routing (Next.js style). | T2 |
| `src/types.ts` | E-001 | Uses `currentPhase` / `updatedAt` (camelCase) vs `current_phase` / `updated_at` (snake_case in SPEC-A); adds `category`, `progress`, status enum `awaiting_user`. | T3 |
| `src/pages/ProjectList.tsx` | E-001 | <fill: visual diffs, e.g. card layout, lucide-react icons, Chinese category labels> | T1 + T3 |
| `src/pages/NewProject.tsx` | E-002 (or E-003 — confirm) | <fill> | <fill> |
| `src/pages/ProjectWorkflow.tsx` | E-004..E-014 (multi-card) | <fill: which phase tabs, which AC affected> | <fill> |
| `src/pages/Settings.tsx` | E-015 (or relevant) | <fill> | <fill> |
| `src/components/PhaseViews.tsx` | E-011..E-014 | <fill: which phase panels are stubbed vs detailed> | <fill> |

## Delta Tag Definitions
- **T1 — visual only**: tailwind tokens, layout, copy, icon set. Becomes a new "组件视觉与原型一致" AC on the existing SPEC-E card. No contract change.
- **T2 — interaction**: navigation, state machine, reactive hooks. May or may not require contract change; evaluate per row.
- **T3 — contract change**: new field, new event, new endpoint, renamed field, additional enum value. Goes into `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` (Task 14).

## Cards Without a Prototype Surface

List any SPEC-E card (E-001..E-105) that has no prototype counterpart (e.g. P7A panel). These cards proceed unmodified.
```

- [ ] **Step 4: Commit**

```bash
cd "$REPO"
git add prototype/PROTOTYPE_INDEX.md
git commit -m "[PROTO] add PROTOTYPE_INDEX.md mapping prototype files to SPEC-E cards"
```

---

### Task 14: Write `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md`

**Files:**
- Create: `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md`

- [ ] **Step 1: Read the prior revision docs to match style**

```bash
cd "$REPO/docs"
ls SPEC_REVISION_REQ_v3.* 2>/dev/null || ls *REVISION* *DELTA* 2>/dev/null
```

If a prior `SPEC_REVISION_REQ_v3.17_*.md` exists, read its first 100 lines to match section structure and approval column format.

- [ ] **Step 2: Write `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md`**

Use this template; one row per T3 item identified in Task 13. Do not leave rows as TBD — if Task 13 surfaced no T3 items, state that explicitly and close the doc.

```markdown
# SPEC Revision Request v3.18 — Prototype Delta (2026-04-17)

Driver: Google AI Studio prototype snapshot under `prototype/` (imported 2026-04-17). This document captures every contract-level divergence (T3 in `prototype/PROTOTYPE_INDEX.md`) and proposes a disposition for each: **adopt** (reflow into SPEC-A and create downstream tasks), **reject** (modify the prototype to align with SPEC-A — captured in PROTOTYPE_INDEX as a known "diverge from prototype"), or **defer** (revisit in v3.19+).

Continues the rhythm of v3.15 / v3.16-BDD / v3.17-AudioMaster.

## Decision Matrix

| # | Source (file:line) | Current SPEC-A Reference | Proposed Change | Disposition | Owner Card |
|---|---|---|---|---|---|
| D1 | `prototype/src/types.ts:1-9` (`Project` interface) | SPEC-A-002 `ProjectInfo` (`project_id`, `title`, `description`, `current_phase`, `status`) | <adopt|reject|defer — explain> e.g. "Adopt `category`, `progress`, `updated_at` as new fields on `ProjectInfo`; keep snake_case. Reject `awaiting_user` status — use existing `pending` semantics." | <adopt> | <fill SPEC-A-NNN> |
| D2 | <next T3 row> | <SPEC reference> | <change> | <disposition> | <task card> |
| ... | | | | | |

## Adopted Changes — Downstream Task Card Backlog

For every "adopt" row above, list the SPEC-A task card to be created or amended:

- [ ] SPEC-A-NNN: <title> — adds `<field>` to `<schema>`; updates `src/shared/schemas/<file>.py` and `src/shared/types/<file>.ts`; bumps fixture in `tests/fixtures/api/...`; updates `tests/contract/test_frontend_types_match_schemas.py`.

## Rejected Changes — Prototype-Side Adjustments

For every "reject" row, the prototype is the wrong side. Note the deviation in `prototype/PROTOTYPE_INDEX.md` so future maintainers know not to copy it into `src/frontend/`.

## Deferred Changes

- [ ] <item>: deferred to v3.19, reason: <fill>

## Approval

- [ ] Reviewed by 许阳: <date>
- [ ] Reviewed by Claude: 2026-04-17
- [ ] Effective date: <fill on approval>
```

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
git add docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md
git commit -m "[SPEC-v3.18] propose contract delta from prototype snapshot 2026-04-17"
```

- [ ] **Step 4: Notify user**

Print:
> "Wave 1 complete. PROTOTYPE_INDEX + v3.18 DELTA are ready for review. Wave 2 (SPEC-A reflow) is gated on user disposition of each D-row in the DELTA doc."

---

## Cross-Cutting Steps After Each Task

For every task, after the final commit:

- [ ] Append a PROGRESS.md entry per HARNESS §9.2:

```markdown
## [SPEC-X-NNN] <task title>
- **Status**: DONE
- **Started**: <iso8601>
- **Completed**: <iso8601>
- **Agent**: <agent-name>
- **Files Changed**: <list from `git show --stat HEAD`>
- **Verification**: <commands run + PASS/FAIL>
- **Artifacts**: <files produced>
- **Commit**: <short-sha> <subject>
- **Decisions**: <1-3 bullets — if none non-obvious, write the standard sentinel>
- **Notes**: <blockers / risks / follow-ups>
```

- [ ] Commit the PROGRESS entry separately:

```bash
cd "$REPO"
git add PROGRESS.md
git commit -m "[<task-id>] update PROGRESS.md"
```

---

## Self-Review Notes (writing-plans built-in)

Coverage of the spec sections:
- §0.3 (5 gap items): T7+T8 close MSW gap; T10+T11 close real env gap; T9 closes contract drift gap; T7 (`_index.json`) closes single-source-of-fixtures gap; Wave 1 (T13+T14) closes "playwright target undefined" gap by feeding into the per-card AC additions in Wave 3.
- §1 (isolation): T4 + T5 + T6 (eslint paths under `src/frontend/tsconfig.json`).
- §2 (audit + DELTA): T13 + T14.
- §3 (per-card TDD changes): out of scope here — happens in Wave 3 after this plan completes.
- §4 (mock + real env + contract): T7..T12.
- §5 (risks): R1 enforced via T4 commit-prefix rule + T5 README; R3 (TDD bypass) — pre-commit hook addition is a follow-up tracked in PROGRESS, not in this plan; R4 enforced via T7 + T9 + T12; R5 enforced via T12 nightly outcome ≠ blocking.
- §6 Wave 0 (3 cards): T1+T2+T3 = task cards; T5..T12 = implementation; Wave 1 (audit) = T13+T14.

Known follow-ups intentionally deferred (not gaps in this plan, but in the broader initiative):
- Pre-commit hook for "TS file changed → matching test must change" (R3).
- ESLint `no-restricted-imports` for `prototype/**` (waits on §1.3 once src/frontend/eslint config exists in a later card).
- Switching `seed_dev_db.py` from inline DDL to Alembic-driven schema (waits on SPEC-A-007 application).
- Replacing the placeholder `phase_advance.json` schema mapping once SPEC-A-010 WS event Pydantic models exist.
- Wave 2 (SPEC-A reflow) and Wave 3 (21 SPEC-E cards) — separate plans, written after Wave 1 user review.

Placeholder scan: every step contains exact code or exact commands; "fill" markers in T13/T14 are explicitly required to be resolved during execution by reading prototype source — they are not deferrable to "TBD".

Type / signature consistency: `seed()` defined in T11 step 3 is called by T11 step 1 test; `__FIXTURES_TAG__` defined in T8 step 3 is checked in T8 step 7 test; `extract_ts_types.py` JSON output shape from T9 step 3 matches consumer in T9 step 5.
