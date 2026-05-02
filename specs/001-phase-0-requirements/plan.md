# Implementation Plan: Phase 0 - AI Video Requirements Definition

**Branch**: `001-phase-0-requirements` | **Date**: 2026-05-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-phase-0-requirements/spec.md`

## Summary

Implement Phase 0 of the AI Video System pipeline: users create a project with a natural language description, an AI RequirementsAgent extracts structured video production requirements, a CompletenessReviewer audits the result, and the user can revise through natural language chat before advancing to Phase 1 via a gated advance button.

**Current state**: Backend infrastructure (RequirementsAgent, IntentRouter, API endpoints) is largely functional. Frontend WorkflowPage uses mock data and must be wired to real APIs. The plan focuses on frontend-backend integration, fixing schema mismatches, and comprehensive testing.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI + Pydantic (backend API), React + Vite + @remotion/player (frontend), LiteLLM + Instructor (LLM calls), Huey + SQLite (task queue)
**Storage**: SQLite (authoritative state: projects, phases, task_ledger, events, agent_call_log, preferences), File system (large artifacts: requirements.json, dialogue logs)
**Testing**: pytest (backend unit/integration/contract), Vitest (frontend unit/component), Playwright (E2E), DeepEval (agent eval)
**Target Platform**: Linux server (Docker Compose: 3 containers — frontend :3000, API :8000, worker)
**Project Type**: Web application (FastAPI backend + React SPA frontend)
**Performance Goals**: Requirements generation within 30s of submission (SC-001), project state recovery within 10s (SC-006), real-time task status updates via WebSocket
**Constraints**: Single-user single-project single-tab (V1), WAL-mode SQLite, stateless agents, deterministic FSM skeleton
**Scale/Scope**: Phase 0 of 12-phase pipeline, ~26 functional requirements, 4 user stories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on HARNESS.md and TECH_PLAN_v3.3 design philosophy:

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Deterministic FSM + Stateless LLM** | PASS | RequirementsAgent is a pure function; IntentRouter is stateless; WorkflowEngine controls flow deterministically |
| **II. SQLite Single Source of Truth** | PASS | All state in `projects`, `phases`, `task_ledger` tables; artifacts on filesystem as read-only snapshots |
| **III. TDD Mandatory** | PASS | Tests exist before implementation changes; RED-GREEN-REFACTOR cycle per task card |
| **IV. Contract-First Development** | PASS | Shared schemas in `src/shared/schemas/artifacts.py`; API contracts documented before implementation |
| **V. LLM Content-Only, No Flow Control** | PASS | IntentRouter classifies intent deterministically; GateKeeper is hard-coded; LLM only fills requirements JSON |
| **VI. Real-Time Observability** | PASS | WebSocket events for task status; agent_call_log for cost/token tracking; events table for audit trail |
| **VII. Failure Visibility** | PASS | Failed tasks show red badge; LLM errors surface as user-facing messages; retry buttons for recoverable failures |
| **VIII. Single-Worker Sequential Execution** | PASS | Huey worker=1 for Phase 0 tasks; no concurrency conflicts |

**Gate Result**: ALL PASS — proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-0-requirements/
├── plan.md              # This file
├── research.md          # Phase 0 output — technical decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — dev setup & workflow
├── contracts/           # Phase 1 output — API contracts
│   ├── rest-api.md      # REST endpoint contracts
│   └── websocket.md     # WebSocket event contracts
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── backend/
│   ├── agents/
│   │   ├── requirements_agent.py      # RequirementsAgent (EXISTS — refine schema output)
│   │   ├── completeness_reviewer.py   # CompletenessReviewer (EXISTS — re-export from reviewers/)
│   │   └── intent_router.py           # IntentRouter (EXISTS — no changes needed)
│   ├── api/
│   │   └── routes/
│   │       └── projects.py            # Phase 0 endpoints (EXISTS — verify correctness)
│   ├── engine/
│   │   ├── workflow_engine.py         # FSM engine (EXISTS — no changes)
│   │   └── gatekeeper.py             # GateKeeper (EXISTS — verify GateP0 registration)
│   ├── gates/
│   │   ├── gate_p0.py                 # GateP0 (EXISTS — register in gate_registry.py)
│   │   └── gate_registry.py           # Gate registry (MODIFY — add GateP0)
│   └── reviewers/
│       └── __init__.py                # (MODIFY — re-export CompletenessReviewer)
├── frontend/
│   ├── pages/
│   │   └── WorkflowPage.tsx           # (MODIFY — replace mock data with API calls)
│   ├── components/
│   │   ├── previews/
│   │   │   └── P0RequirementsView.tsx # (EXISTS — verify integration)
│   │   └── workflow/
│   │       └── mockData.ts            # (REFERENCE — data shapes to match)
│   └── hooks/
│       ├── useProjectState.ts         # (VERIFY — correct state fetching)
│       └── useChat.ts                 # (EXISTS — verify chat integration)
└── shared/
    └── schemas/
        └── artifacts.py               # Requirements schema (EXISTS — align agent output)

tests/
├── unit/
│   └── pipeline/
│       └── test_spec_d_002.py         # Phase 0 unit tests (EXISTS — verify coverage)
├── integration/
│   └── test_phase0_flow.py            # (CREATE — integration test for full Phase 0 flow)
├── contract/
│   └── test_phase0_contracts.py       # (CREATE — API contract tests)
└── e2e/
    └── playwright/
        └── phase0-bdd-acceptance.spec.ts  # (EXISTS — verify against updated UI)
```

**Structure Decision**: Web application (Option 2). The existing `src/backend/` + `src/frontend/` + `src/shared/` layout is preserved. No new directories needed.

## Complexity Tracking

No constitution violations. No complexity justifications required.

---

## Phase 0 Artifacts (Generated)

1. [research.md](./research.md) — Technical decisions and rationale
2. [data-model.md](./data-model.md) — Entity definitions, relationships, state transitions
3. [quickstart.md](./quickstart.md) — Development setup and workflow
4. [contracts/](./contracts/) — REST and WebSocket API contracts
