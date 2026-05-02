# HARNESS -- Global Constraints for AI-Video-System

> Version: 1.1.0
> Date: 2026-04-20
> Purpose: Deterministic guardrails for all agents working in this project.
> Authority: This file overrides agent defaults. Violations trigger task rejection.
> Changelog: v1.1.0 — §9 PROGRESS.md switched from append-only narrative to one-line-per-commit index (commit body is source of truth, 100-line rotation).

---

## 1. Directory Authority Matrix

### 1.1 Allowed (Write)

| Path Pattern | Who May Write | Notes |
|---|---|---|
| `src/backend/**` | Backend agents | API, engine, agents, services, models, workers |
| `src/frontend/**` | Frontend agents | Components, pages, hooks, types, utils |
| `src/shared/types/**` | Contract agent (SPEC-A tasks only) | Shared TypeScript/Python types |
| `src/shared/schemas/**` | Contract agent (SPEC-A tasks only) | JSON Schema / Pydantic models |
| `src/shared/constants/**` | Any agent (with task card authorization) | Enums, config constants |
| `tests/**` | Any agent (must match task card) | Unit, integration, eval, e2e |
| `scripts/**` | Infra agent (SPEC-B tasks only) | Build, deploy, migration scripts |
| `config/**` | Infra agent (SPEC-B tasks only) | model_config.json, theme defaults |
| `tasks/SPEC-*/` | Orchestrator only | Task card status updates |
| `PROGRESS.md` | Any agent (append one row per commit, see section 9) | Dev log index |
| `prototype/**` | Prototype maintainer (red-light approval) | Snapshot of external prototype source; imports from `prototype/**` into `src/frontend/**` are forbidden. |

### 1.2 Forbidden (Never Modify Without Red-Light Approval)

| Path Pattern | Reason |
|---|---|
| `HARNESS.md` | Meta-constraint, requires human approval |
| `CLAUDE.md` | Project map, requires human approval |
| `docs/specs/SPEC-*.md` | Upstream spec is read-only reference |
| `docs/TECH_PLAN_v3.3.md` | Upstream tech plan is read-only reference |
| `.env*` | Secrets, never in code |
| `*.pem, *.key, *.p12` | Certificates |
| `data/db/*.sqlite3` | Runtime DB, never committed |
| `prototype/**` | Read-only imported prototype. Modify only via `[PROTO]` commits to refresh the imported snapshot. Do NOT import from `src/frontend/**`. |

### 1.3 Read-Only Reference

| Path | Purpose |
|---|---|
| `docs/specs/` | Authoritative SPEC definitions |
| `docs/TECH_PLAN_v3.3.md` | Architecture decisions and rationale |
| `tasks/` | Task cards (read for scope, do not modify content) |

---

## 2. Dependency Direction (Enforced)

```
Layer 0: src/shared/types/, src/shared/schemas/, src/shared/constants/
    ^
Layer 1: src/backend/models/
    ^
Layer 2: src/backend/services/, src/backend/engine/
    ^
Layer 3: src/backend/agents/
    ^
Layer 4: src/backend/api/, src/backend/workers/
    ^
Layer 5: src/frontend/types/, src/frontend/utils/
    ^
Layer 6: src/frontend/hooks/, src/frontend/components/
    ^
Layer 7: src/frontend/pages/
```

### Rules

- **Import direction: downward only.** Layer N may import from Layer 0..N-1, never from N+1..7.
- **Cross-layer import forbidden:** `src/backend/` MUST NOT import from `src/frontend/` and vice versa. Communication is via `src/shared/` types + REST/WS at runtime.
- **Circular dependency = build failure.** CI checks with `madge --circular` (backend) and `madge --circular` (frontend).
- **Shared types are the contract boundary.** If two layers need the same type, it lives in `src/shared/types/`.

---

## 3. Naming Conventions

### 3.1 Files

| Scope | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py` | `workflow_engine.py` |
| Python classes | `PascalCase` | `WorkflowEngine` |
| Python functions/vars | `snake_case` | `advance_phase()` |
| TypeScript files | `PascalCase.tsx` (components), `camelCase.ts` (utils) | `ProjectList.tsx`, `useWebSocket.ts` |
| TypeScript types/interfaces | `PascalCase` | `TemplateProps` |
| TypeScript vars/functions | `camelCase` | `fetchProjectState()` |
| Test files | `test_<module>.py` / `<Component>.test.tsx` | `test_workflow_engine.py` |
| Task cards | `<SPEC>-<NNN>-<slug>.md` | `A-001-artifact-schemas.md` |
| Config files | `snake_case.json` | `model_config.json` |
| SQL migrations | `V<NNN>__<description>.sql` | `V001__create_projects.sql` |

### 3.2 Git

- Branch: `feat/<spec>-<task_id>/<slug>` e.g. `feat/spec-a-001/artifact-schemas`
- Commit: `[SPEC-X-NNN] <imperative verb> <what>` e.g. `[SPEC-A-001] define artifact JSON schemas`
- PR title: same as commit prefix

> Exception: `prototype/**` uses commit prefix `[PROTO] <description>` (snapshot refresh from external prototype source). It is exempt from the `[SPEC-X-NNN]` rule and from per-card task flow.

### 3.3 Database

- Table names: `snake_case`, plural (`projects`, `phases`, `task_ledger`)
- Column names: `snake_case`
- Enum values: `UPPER_SNAKE_CASE` (`PENDING`, `RUNNING`, `COMPLETED`)
- Foreign keys: `<referenced_table_singular>_id` (`project_id`)

---

## 4. TDD Development Mode (Hard Constraint)

### 4.1 The Loop

```
RED   --> Write a failing test that defines the expected behavior
GREEN --> Write the minimum code to make the test pass
REFACTOR --> Clean up while keeping tests green
COMMIT --> git commit with [SPEC-X-NNN] prefix
```

### 4.2 Rules

1. **No implementation code before a failing test.** If you wrote code first, delete it. Start from RED.
2. **Test passes immediately = test is wrong.** Fix the test until it fails for the right reason.
3. **One task card = one RED-GREEN-REFACTOR cycle minimum.** Complex cards may have multiple cycles.
4. **Each cycle ends with a git commit.** Commit message includes task ID. This creates an audit trail.
5. **Test must verify sufficient conditions.** Ask: "Would a stub pass this test?" If yes, the test is too weak.

### 4.3 TDD Exceptions (No TDD Required)

- Config file changes (JSON/YAML/env)
- One-off scripts / data migrations
- Documentation / SKILL.md / task card writing
- User explicitly says "no tests needed"

### 4.4 Dev-Test Loop

```
Agent picks task card
  --> Reads task card (allowed files, forbidden files, AC)
  --> Writes failing test (RED)
  --> Implements minimum code (GREEN)
  --> Refactors (REFACTOR)
  --> Runs verification commands from task card
  --> Commits with [SPEC-X-NNN] prefix (long story in commit body, §9.3)
  --> Appends one row to PROGRESS.md "Recent commits" table (§9.2)
  --> Picks next task card
```

---

## 5. Schema / Type Boundary Validation

### 5.1 Contract-First

- All API request/response types MUST be defined in `src/shared/schemas/` BEFORE implementation.
- All DB models MUST be defined in `src/backend/models/` BEFORE service code.
- Frontend types in `src/frontend/types/` MUST mirror `src/shared/types/` (auto-generated preferred).
- Pydantic models are the Python-side schema authority; TypeScript interfaces are the TS-side authority; `src/shared/schemas/*.json` (JSON Schema) is the cross-language authority.

### 5.2 Validation Points

| Boundary | Validation Tool | When |
|---|---|---|
| API input | Pydantic `response_model` | Every request |
| API output | Pydantic `response_model` | Every response |
| DB write | SQLAlchemy model + Pydantic | Before INSERT/UPDATE |
| LLM output | Instructor `response_model` | Every LLM call |
| WebSocket event | Pydantic `BaseModel` | Before broadcast |
| Template props | TypeScript type check | Compile time |
| Config files | JSON Schema validation | App startup |

---

## 6. File Size & Complexity Limits

| Target | Limit | Action if Exceeded |
|---|---|---|
| Single Python file | 400 lines | Split into submodules |
| Single TypeScript file | 300 lines | Extract components/hooks |
| Single function | 50 lines | Extract helper functions |
| Single test file | 500 lines | Split by test category |
| Cyclomatic complexity per function | 10 | Refactor conditional logic |
| Import count per file | 15 | Review dependency structure |
| Task card scope | Completable in 1 context window | Split into sub-tasks |

---

## 7. Allowed Tools & Forbidden Commands

### 7.1 Allowed

| Tool | Purpose |
|---|---|
| `pytest` | Python test runner |
| `vitest` / `jest` | TypeScript test runner |
| `ruff` | Python linter + formatter |
| `eslint` + `prettier` | TypeScript linter + formatter |
| `mypy` | Python type checker |
| `tsc --noEmit` | TypeScript type checker |
| `madge --circular` | Circular dependency detection |
| `docker compose` | Local dev environment |
| `sqlite3` | DB inspection (read-only in prod) |
| `ffprobe` | Media file inspection |
| `git` | Version control |

### 7.2 Forbidden

| Command | Reason | Alternative |
|---|---|---|
| `rm -rf` on non-temp paths | Destructive | Use git to revert |
| `DROP TABLE` / `TRUNCATE` on prod | Destructive | Migration with rollback |
| `--no-verify` on git hooks | Bypasses quality gates | Fix the hook failure |
| `pip install` without `requirements.txt` update | Undocumented dependency | Add to requirements.txt first |
| `npm install` without `package.json` update | Undocumented dependency | Add to package.json first |
| Direct `curl` / `wget` for dependencies | Unauditable | Use package manager |
| `eval()` / `exec()` in production code | Security risk | Use structured data |
| Raw SQL string concatenation | SQL injection | Use parameterized queries |
| `dangerouslySetInnerHTML` | XSS risk | Use sanitized rendering |

---

## 8. Logging & Observability Standards

### 8.1 Log Format (Unified JSON)

```json
{
  "ts": "2026-04-16T10:30:00.000Z",
  "level": "INFO|WARN|ERROR",
  "module": "workflow_engine",
  "event": "phase.advanced",
  "project_id": "proj_xxx",
  "phase": 3,
  "task_id": "task_yyy",
  "agent_name": "ScriptAgent",
  "duration_ms": 1234,
  "tokens": {"input": 500, "output": 200},
  "cost_usd": 0.003,
  "msg": "Human-readable description"
}
```

### 8.2 Rules

1. **Every agent call MUST log**: agent_name, duration_ms, token counts, cost, phase, project_id.
2. **Every state transition MUST emit an event** to the `events` table.
3. **Sensitive data MUST be redacted** before logging (see `SECRET_REGEXES` in TECH_PLAN).
4. **No `print()` in production code.** Use structured logger.
5. **Error logs MUST include**: stack trace, input summary (first 500 chars), recovery action taken.

---

## 9. Development Log (PROGRESS.md) Maintenance

### 9.1 Principle

PROGRESS.md is a **one-line-per-commit index**, not a narrative log.
The commit body is the single source of truth for Files Changed /
Verification / Decisions / Artifacts — `git show <sha>` replaces prose.
Do not paste verification output, diff summaries, or round-by-round
narratives into PROGRESS.md; that belongs in the commit body (§9.3).

### 9.2 Entry Format (PROGRESS.md)

After every `[SPEC-X-NNN]` commit, append **one row** to the
"Recent commits" table:

```
| <short-sha> | SPEC-X-NNN | <imperative title> | YYYY-MM-DD |
```

- Multi-round fix/verify/review: one row per round, `(round N)` suffix
  in the Task column (e.g. `SPEC-A-009 (round 2)`). No inline narrative.
- Blocked / in-progress notes → "Open follow-ups" section (free-form,
  removed when resolved). Do not create per-task entries for blockers.

PROGRESS.md structure is fixed: archive pointer → Status snapshot
(per-SPEC totals) → Recent commits table → Open follow-ups → Rules.

### 9.3 Commit Body Requirements (where the long story lives)

```
[SPEC-X-NNN] <imperative subject>

Files Changed:
- <path>
...

Verification:
- <command> → <pass/fail + key output>

Decisions:
- <non-obvious choice + why>
(If none: "No non-obvious decisions — straight-line impl of task card.")

Artifacts:
- <concrete outputs: schemas / endpoints / types>
```

Rules:
1. Verification output MUST be real command output, not assumed.
2. Decisions is required. Future agents read `git show <sha>` to understand WHY.
3. If blocked, the blocking reason MUST reference a specific task ID or
   external dependency; commit body documents the blocker even if no code lands.

### 9.4 Rotation (snapshot-and-prune)

When PROGRESS.md exceeds **100 lines**, rotate:

1. Copy current content to `PROGRESS.md.full.backup.<YYYY-MM-DD>.md` (tracked in git).
2. Rewrite PROGRESS.md as: archive pointer → Status snapshot →
   Recent commits table (last ~15 rows) → Open follow-ups → Rules.
3. Commit as `[PROGRESS-ARCHIVE] snapshot + prune to <N>-line index`.

Backups are never deleted; full history lives across the backup chain.

---

## 10. CI / Pre-Commit Checks

### 10.1 Pre-Commit (Must Pass Before Commit)

```bash
ruff check src/backend/          # Python lint
ruff format --check src/backend/ # Python format
mypy src/backend/                # Python types
eslint src/frontend/             # TS lint
tsc --noEmit                     # TS types
pytest tests/unit/ -x            # Unit tests (fail fast)
```

### 10.2 CI Pipeline (Must Pass Before Merge)

```bash
# All of pre-commit, plus:
pytest tests/integration/        # Integration tests
pytest tests/eval/ --eval-mode   # Agent eval sets (if prompts/** changed)
madge --circular src/backend/    # Circular dependency check
madge --circular src/frontend/
```

### 10.3 Eval Regression Gate

- If any file in `src/backend/agents/` or `config/prompts/` changes:
  - Run all eval sets in `tests/eval/`
  - Any agent accuracy drop > 5% blocks merge
  - Results written to `tests/eval/eval_report.json`

---

## 11. Security Constraints

1. **No secrets in code.** All API keys via `.env` (not committed).
2. **No user input in SQL without parameterization.**
3. **No `eval()` / `exec()` / `Function()` in production.**
4. **All LLM outputs validated** through Pydantic/Instructor before use.
5. **File paths from user input sanitized** against path traversal.
6. **CORS restricted** to configured origins only.
7. **WebSocket messages validated** against schema before processing.

---

## 12. Task Card Compliance

Every agent MUST, before writing any code:

1. **Read the task card** for the task they are working on.
2. **Verify they are only modifying files listed in `allowed_files`.**
3. **Verify they are NOT modifying files listed in `forbidden_files`.**
4. **Run the verification commands** listed in the task card after implementation.
5. **Check the completion definition** and ensure all criteria are met.
6. **Update PROGRESS.md** with the task result.

Failure to comply with any of the above = task rejection, code reverted.

---

## 13. Cross-Cutting Rules

1. **ASCII only** in source code (except string literals with CJK content).
2. **No TODO/FIXME without task ID.** Write `# TODO(SPEC-A-003): description` not bare `# TODO`.
3. **No dead code.** If code is unused, delete it. Don't comment it out.
4. **No magic numbers.** Constants go in `src/shared/constants/`.
5. **Imports sorted**: stdlib > third-party > local, alphabetical within groups.
6. **Max 1 class per file** (Python). Exceptions: small dataclasses in a types module.
7. **Test data in fixtures**, not inline in test functions.
