# AI-Video-System -- Agent Navigation Map

> This is a map, not a manual. It tells you WHERE to find things.
> Read HARNESS.md for HOW to work. Read task cards for WHAT to do.

---

<!-- SPECKIT START -->
**Active Plan**: [specs/001-phase-0-requirements/plan.md](specs/001-phase-0-requirements/plan.md)
**Spec**: [specs/001-phase-0-requirements/spec.md](specs/001-phase-0-requirements/spec.md)
**Branch**: `001-phase-0-requirements`
<!-- SPECKIT END -->

## Quick Orientation

**What is this?** A web-based AI video production system for financial content creators.
**Architecture?** Deterministic FSM + stateless LLM agents + SQLite + 12-phase pipeline.
**Tech stack?** FastAPI (backend) + Next.js (frontend) + Remotion (video render) + SQLite.

---

## Where to Find Things

| Need | Go To |
|---|---|
| **What to build** | `tasks/SPEC-{..}/` -- atomic task cards |
| **How to build** | `HARNESS.md` -- global constraints, TDD rules, naming |
| **What the system does** | `docs/specs/SPEC-*.md` -- authoritative specifications |
| **Why it's designed this way** | `docs/` -- architecture rationale |
| **What's done / what's next** | `PROGRESS.md` -- dev log |
| **Shared types & schemas** | `src/shared/` -- cross-layer contracts |
| **Backend code** | `src/backend/` -- API, engine, agents, services |
| **Frontend code** | `src/frontend/` -- React components, pages, hooks |
| **Tests** | `tests/` -- unit, integration, eval, e2e |
| **Build & deploy scripts** | `scripts/` -- setup, migration, CI helpers |
| **Runtime config** | `config/` -- model_config, theme defaults |

---

## SPEC Dependency Order (Build Sequence)

```
SPEC-A (contracts)     -- Layer 0, start here
  |
  +-- SPEC-B (infra)   -- Layer 1, after A
  |     |
  |     +-- SPEC-C (backend core) -- Layer 2, after B
  |           |
  |           +-- SPEC-D (pipeline) -- Layer 3, after C
  |
  +-- SPEC-E (frontend) -- Layer 4, can scaffold after A
  |
  +-- SPEC-F (media render) -- Layer 4-5, needs A + D
```

**Parallel tracks after SPEC-A:**
- Track 1: B -> C -> D (backend vertical)
- Track 2: E (frontend scaffold, full impl after D)
- Track 3: F (media render, after D)

---

## Task Card Format

Every task card in `tasks/SPEC-X/` contains:

```yaml
task_id: SPEC-X-NNN
title: ...
spec_ref: SPEC section reference
allowed_files: [files you MAY modify]
forbidden_files: [files you MUST NOT touch]
depends_on: [prerequisite task IDs]
verification_commands: [commands to run after implementation]
completion_definition: [what "done" means]
acceptance_criteria: [mapped to test files]
```

**Read the task card BEFORE writing any code.**

---

## Development Flow

```
1. Pick task from tasks/SPEC-X/ (respect depends_on order)
2. Read task card -> understand scope
3. Read relevant SPEC section -> understand requirements
4. Write failing test (RED)
5. Implement minimum code (GREEN)
6. Refactor (keep tests green)
7. Run verification_commands from task card
8. Update PROGRESS.md
9. Commit: [SPEC-X-NNN] <description>
10. Pick next task
```

---

## Problem? Check Here First

| Problem | Check |
|---|---|
| "What type should I use?" | `src/shared/types/` and `docs/specs/SPEC-A-contracts.md` |
| "What API endpoint exists?" | `docs/specs/SPEC-A-contracts.md` SPEC-1A (25 endpoints) |
| "What DB tables exist?" | `docs/specs/SPEC-A-contracts.md` SPEC-1B (10 tables DDL) |
| "What events can I emit?" | `docs/specs/SPEC-A-contracts.md` SPEC-11A (17 event types) |
| "What error codes to use?" | `docs/specs/SPEC-A-contracts.md` SPEC-13A (17 error codes) |
| "How does phase X work?" | `docs/specs/SPEC-D-pipeline-phases.md` SPEC-9.X |
| "What does the UI look like?" | `docs/specs/SPEC-E-frontend-ui.md` SPEC-2/11/24/25 |
| "How does rendering work?" | `docs/specs/SPEC-F-media-render.md` SPEC-18/19/20/21/22/23 |
| "What infra decisions?" | `docs/specs/SPEC-B-infra-deploy.md` SPEC-1/10/12/13/14/15 |
| "Worker/queue behavior?" | `docs/specs/SPEC-B-infra-deploy.md` SPEC-10 |
| "Import not allowed?" | `HARNESS.md` section 2 (dependency direction) |
| "File too big?" | `HARNESS.md` section 6 (complexity limits) |
| "How to name things?" | `HARNESS.md` section 3 (naming conventions) |
| "Test failing?" | Check test is RED for the right reason, then GREEN minimum impl |

---

## Key Architecture Decisions (Quick Reference)

1. **FSM is deterministic code, LLM only fills content** -- never let LLM decide flow
2. **SQLite is the single source of truth** -- no dual-write, no file-as-DB
3. **Agents are stateless** -- every call is a fresh function invocation
4. **Canonical timeline** -- `timeline.json` from P4 is the ONE time source
5. **Dual-layer Reviewer** -- L1 programmatic (0 cost) -> L2 LLM semantic
6. **Three-layer visualization** -- ECharts animation + React community + Remotion orchestration
7. **Contract-first** -- shared types defined before implementation

---

@HARNESS.md
