# Tasks: Phase 0 - AI Video Requirements Definition

**Input**: Design documents from `/specs/001-phase-0-requirements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Integration tests and E2E tests are explicitly requested. Unit tests already exist for backend components — verify they pass but do not create new ones.

**Organization**: Tasks are grouped by user story for independent implementation and testing. Contract and integration tests are placed BEFORE implementation tasks within each story (TDD: RED first).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify environment and existing state — no new files created

- [ ] T001 Run existing Phase 0 unit tests to establish baseline: `pytest tests/unit/pipeline/test_spec_d_002.py -v`
- [ ] T002 [P] Verify dev environment per quickstart.md — backend API on :8000, frontend on :5173, worker running

---

## Phase 2: Foundational (Backend Gaps)

**Purpose**: Fix backend issues that block all user story work. These are small, pre-existing code fixes.

**CRITICAL**: No frontend work can be verified without these fixes.

- [ ] T003 Fix GateP0: remove preferences_confirmed_at check (check #3) in `src/backend/gates/gate_p0.py` and register GateP0 in `src/backend/gates/gate_registry.py`
- [ ] T004 [P] Re-export CompletenessReviewer from `src/backend/reviewers/__init__.py` by adding `from src.backend.agents.completeness_reviewer import CompletenessReviewer`
- [ ] T005 [P] Add `_to_canonical()` adapter in `src/backend/agents/requirements_agent.py` to transform agent output dict into canonical `Requirements` Pydantic model before persisting to `requirements.json`
- [ ] T006 Verify backend fixes: run `pytest tests/unit/pipeline/test_spec_d_002.py -v` — all tests must pass

**Checkpoint**: Backend is fully correct. Frontend integration can now be verified against real API responses.

---

## Phase 3: User Story 1 - Create Project and Get AI Requirements (Priority: P1)

**Goal**: User creates a project with title + description, AI generates structured requirements, and the requirements card appears in WorkflowPage with real data instead of mock data.

**Independent Test**: Submit a title and description on the new project page, verify a structured requirements summary card appears in the project detail view within 30 seconds.

### Contract Tests for US1 (write FIRST, ensure they FAIL or verify existing API)

- [ ] T007 [P] [US1] Create contract test for `POST /projects` in `tests/contract/test_phase0_contracts.py` — validate request/response schemas match `contracts/rest-api.md` section 1
- [ ] T008 [P] [US1] Create contract test for `GET /projects/{id}/state` in `tests/contract/test_phase0_contracts.py` — validate response includes project metadata and phase_0 status per `contracts/rest-api.md` section 2
- [ ] T009 [P] [US1] Create contract test for `GET /projects/{id}/phases/0/artifact` in `tests/contract/test_phase0_contracts.py` — validate response matches canonical Requirements schema from `src/shared/schemas/artifacts.py`

### Integration Tests for US1 (write FIRST, ensure they FAIL before implementation)

- [ ] T010 [US1] Create integration test for US1 happy path in `tests/integration/test_phase0_flow.py` — create project via API, poll for artifact, verify requirements.json contains all required fields (topic, target_duration, platform, category, target_word_count)

### Implementation for US1

- [ ] T011 [US1] Replace `MOCK_PROJECT_TITLE` import with `useProjectState(projectId)` hook call in `src/frontend/pages/WorkflowPage.tsx` — fetch real project title and phase data from `GET /projects/{id}/state`
- [ ] T012 [US1] Wire `P0RequirementsView` component in `src/frontend/components/previews/P0RequirementsView.tsx` to display real artifact data from `GET /projects/{id}/phases/0/artifact` in WorkflowPage
- [ ] T013 [US1] Integrate task list with real data: replace `MOCK_TASKS` and `MOCK_CURRENT_TASK_TITLE` with data from `GET /projects/{id}/tasks?phase=0` in `src/frontend/pages/WorkflowPage.tsx` — implement default-collapsed view showing only current executing task, expandable to show all tasks (FR-020)
- [ ] T014 [US1] Remove `MOCK_FACTUAL_DATA` import and `FactualLedger` component from Phase 0 UI in `src/frontend/pages/WorkflowPage.tsx` (FactualLedger is Phase 2+, not Phase 0)
- [ ] T015 [US1] Add WebSocket connection via `useWebSocket(projectId)` hook in `src/frontend/pages/WorkflowPage.tsx` — subscribe to `task.created`, `task.started`, `task.completed`, `task.failed`, `artifact.updated` events for real-time UI updates without page refresh (FR-021)

**Checkpoint**: Create project → see real project title, real requirements card, real task list with live status. No more mock data on screen.

---

## Phase 4: User Story 2 - Review Requirements and Confirm Accuracy (Priority: P1)

**Goal**: After AI generates requirements, the CompletenessReviewer audit runs automatically. User sees review result (PASS/FAIL) and can modify requirements through natural language chat (revise, regenerate).

**Independent Test**: Have AI generate requirements, verify review runs automatically, issue revise/regenerate commands through chat input, verify requirements update.

### Contract Tests for US2 (write FIRST)

- [ ] T016 [P] [US2] Create contract test for `POST /projects/{id}/chat` in `tests/contract/test_phase0_contracts.py` — validate request/response for revise, regenerate, inject_subtask, request_advance, clarify intents per `contracts/rest-api.md` section 4

### Integration Tests for US2 (write FIRST)

- [ ] T017 [P] [US2] Create integration test for revise flow in `tests/integration/test_phase0_flow.py` — create project, send revise chat message, verify new artifact version created, old review superseded, new review auto-triggered
- [ ] T018 [P] [US2] Create integration test for regenerate flow in `tests/integration/test_phase0_flow.py` — create project, send regenerate chat message, verify fresh artifact generated, old artifact discarded

### Implementation for US2

- [ ] T019 [US2] Display review verdict (PASS/FAIL badge) in the requirements card in `src/frontend/pages/WorkflowPage.tsx` — consume `review.completed` WebSocket event and update UI with green "审核通过" or red "审核未通过" badge + blocking_issues list
- [ ] T020 [US2] Verify `ChatInput` component in `src/frontend/components/` sends messages to `POST /projects/{id}/chat` and displays intent-aware responses (revise → "已更新...", regenerate → "已重新生成...", inject_subtask → "此功能暂未开放")

**Checkpoint**: Review verdict visible, chat revise/regenerate works end-to-end. User can iterate on requirements.

---

## Phase 5: User Story 3 - Clarify Missing Information (Priority: P2)

**Goal**: When AI cannot determine certain parameters, it raises clarification questions. User answers via quick-reply buttons or free text. Each answer triggers a targeted revision.

**Independent Test**: Submit a vague description ("做一个金融分析视频"), verify clarification questions appear, answer them, verify requirements update without altering confirmed fields.

### Integration Tests for US3 (write FIRST)

- [ ] T021 [US3] Create integration test for clarification flow in `tests/integration/test_phase0_flow.py` — create project with vague description, verify `clarification_needed` array non-empty, answer clarification via chat, verify answer merged and question removed

### Implementation for US3

- [ ] T022 [US3] Display `clarification_needed` questions with quick-reply option buttons in `P0RequirementsView` component at `src/frontend/components/previews/P0RequirementsView.tsx` (FR-011)
- [ ] T023 [US3] Wire quick-reply button clicks to send answer as revise chat message — Router identifies as `revise`, AI merges answer into requirements, clarification question disappears from updated card (FR-012)

**Checkpoint**: Vague input → clarification questions appear → click quick-reply → requirements update without losing confirmed fields.

---

## Phase 6: User Story 4 - Advance to Next Phase (Priority: P1)

**Goal**: User clicks "确认进入下一阶段" button. GateKeeper verifies conditions. If all pass, Phase 0 completes and Phase 1 becomes active.

**Independent Test**: Complete all Phase 0 requirements, click advance button, verify phase status changes to done, Phase 1 becomes active.

### Contract Tests for US4 (write FIRST)

- [ ] T024 [P] [US4] Create contract test for `POST /projects/{id}/advance` in `tests/contract/test_phase0_contracts.py` — validate gate check response format (passed/failed with blocking_reasons) per `contracts/rest-api.md` section 6

### Integration Tests for US4 (write FIRST)

- [ ] T025 [P] [US4] Create integration test for advance happy path in `tests/integration/test_phase0_flow.py` — create project, wait for artifact + review PASS, call advance, verify phase_0 completed, phase_1 active
- [ ] T026 [P] [US4] Create integration test for gate blocking scenarios in `tests/integration/test_phase0_flow.py` — verify advance blocked when review FAIL, verify advance blocked when tasks running, verify advance blocked when no artifact

### Implementation for US4

- [ ] T027 [US4] Add "确认进入下一阶段" advance button to `src/frontend/pages/WorkflowPage.tsx` — button calls `POST /projects/{id}/advance`, displays GateKeeper result
- [ ] T028 [US4] Implement advance button disabled states in `src/frontend/pages/WorkflowPage.tsx` (FR-024):
  - Review FAIL → button disabled, shows "审核未通过" with blocking_issues list
  - Tasks running → button disabled, shows "仍有任务正在执行中，请等待完成"
  - No artifact → button disabled, shows "需求产物尚未生成"
- [ ] T029 [US4] Update PhaseNavigation component in `src/frontend/components/PhaseNavigation.tsx` on advance — Phase 0 shows green checkmark, Phase 1 becomes highlighted as active (FR-022, per `contracts/websocket.md` section 8 `phase.completed` event)

**Checkpoint**: Full loop — create → review → revise if needed → click advance → Phase 1 active. GateKeeper correctly blocks when conditions not met.

---

## Phase 7: Cross-Cutting Integration Tests

**Purpose**: Integration tests that span multiple user stories (end-to-end backend flow). Write and verify against the real API.

- [ ] T030 [P] Create integration test for full Phase 0 happy path in `tests/integration/test_phase0_flow.py` — create project → wait for artifact → verify review PASS → send revise chat → verify new artifact version → verify new review → advance → verify phase_1 active
- [ ] T031 [P] Create integration test for error recovery in `tests/integration/test_phase0_flow.py` — simulate LLM call failure (mock LiteLLM to raise), verify task marked failed, verify error message surfaced, verify retry via regenerate command succeeds
- [ ] T032 [P] Create contract test for WebSocket events in `tests/contract/test_phase0_contracts.py` — connect to `/ws/{project_id}`, create project via REST, verify `task.created`, `task.started`, `task.completed`, `artifact.updated`, `review.completed` events received in order per `contracts/websocket.md`

---

## Phase 8: E2E Tests (Playwright)

**Purpose**: Browser-based E2E tests covering complete user journeys. Existing `phase0-bdd-acceptance.spec.ts` has 50+ scenarios — verify and update for current UI.

- [ ] T033 Verify existing E2E tests: run `npx playwright test tests/e2e/playwright/phase0-bdd-acceptance.spec.ts` in `src/frontend/`, review failures, document which tests need updating due to mock→real API migration
- [ ] T034 [P] Update `tests/e2e/playwright/phase0-bdd-acceptance.spec.ts` — fix selectors to match current WorkflowPage UI (no more mock data), ensure all scenarios pass against real API
- [ ] T035 [P] Create E2E test for task list behavior in `tests/e2e/playwright/phase0-manual-scenarios.spec.ts` — verify default-collapsed view shows only current task, verify expand button reveals all tasks, verify real-time status updates (FR-020, FR-021)
- [ ] T036 [P] Create E2E test for advance button states in `tests/e2e/playwright/phase0-manual-scenarios.spec.ts` — verify button disabled when review FAIL, verify button disabled when tasks running, verify button enabled when all gates pass, verify advance transitions to Phase 1 (FR-023, FR-024)
- [ ] T037 [P] Create E2E test for clarification quick-reply in `tests/e2e/playwright/phase0-manual-scenarios.spec.ts` — submit vague description, verify clarification questions render with quick-reply buttons, click quick-reply, verify requirements card updates (FR-011, FR-012)

---

## Phase 9: Polish & Verification

**Purpose**: Final validation, cleanup, and documentation.

- [ ] T038 Run full manual flow from `quickstart.md` — create project → wait for artifact → check review → send revise chat → advance → verify Phase 1 active — all steps must succeed
- [ ] T039 [P] Verify all existing unit tests still pass: `pytest tests/unit/ -v` and `cd src/frontend && npx vitest run`
- [ ] T040 [P] Run full test suite: `pytest tests/unit/ tests/integration/ tests/contract/ -v` and `cd src/frontend && npx playwright test`
- [ ] T041 Remove unused mock data exports from `src/frontend/components/workflow/mockData.ts` that are no longer referenced after WorkflowPage migration (keep exports used by other pages if any)
- [ ] T042 Update `PROGRESS.md` with one-line commit entries for all completed tasks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (baseline tests must pass first) — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — contract/integration tests FIRST (T007-T010), then implementation (T011-T015)
- **Phase 4 (US2)**: Depends on Phase 3 (needs US1's real API wiring for chat to display correctly)
- **Phase 5 (US3)**: Depends on Phase 4 (clarification builds on revise flow from US2)
- **Phase 6 (US4)**: Depends on Phase 4 (needs review verdict from US2 for GateKeeper states)
- **Phase 7 (Cross-Cutting Tests)**: Depends on Phase 6 (needs full flow implemented)
- **Phase 8 (E2E Tests)**: Depends on Phase 6 (needs full UI implemented), can parallel with Phase 7
- **Phase 9 (Polish)**: Depends on all previous phases complete

### User Story Dependencies

```
Phase 2 (Foundational)
    │
    ▼
Phase 3 (US1: Create + AI Requirements)
    │
    ▼
Phase 4 (US2: Review + Revise)
    ├────→ Phase 5 (US3: Clarifications)
    │         │
    └────→ Phase 6 (US4: Advance)
              │
              ▼
         Phase 7 (Cross-Cutting Tests)
         Phase 8 (E2E Tests)
              │
              ▼
         Phase 9 (Polish)
```

### Within Each User Story

1. Contract tests FIRST → verify they detect issues with current API
2. Integration tests FIRST → verify they FAIL (RED)
3. Implementation tasks → make tests pass (GREEN)
4. Refactor if needed (keep tests GREEN)

### Parallel Opportunities

- T003, T004, T005 (Phase 2) can run in parallel — different files
- T007, T008, T009 (US1 contract tests) can run in parallel
- T016 (US2 contract test) can run in parallel with US1 implementation
- T017, T018 (US2 integration tests) can run in parallel
- T024, T025, T026 (US4 tests) can run in parallel
- T030, T031, T032 (cross-cutting tests) can run in parallel
- T034, T035, T036, T037 (E2E tests) can run in parallel
- Phase 7 and Phase 8 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 + US2)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (3 backend fixes)
3. Complete Phase 3: User Story 1 (real data in WorkflowPage)
4. Complete Phase 4: User Story 2 (chat revise/regenerate)
5. **STOP and VALIDATE**: Can create project, see requirements, revise via chat
6. This is the minimum viable Phase 0

### Incremental Delivery

1. Setup + Foundational → backend correct
2. US1 → real requirements display (no more mock data!)
3. US2 → chat interaction works end-to-end
4. US3 → clarification questions with quick-reply
5. US4 → advance button with GateKeeper
6. Cross-cutting + E2E tests → comprehensive regression coverage
7. Polish → cleanup and documentation

### Parallel Team Strategy

With multiple developers after Foundational phase:
- Developer A: US1 implementation (T011-T015)
- Developer B: US1 contract/integration tests (T007-T010) — can start in parallel
- Developer C: US2 integration tests (T017-T018) + US4 contract test (T024)
- Once US1 done: Developer B picks up US3, Developer C picks up US4

---

## Notes

- [P] tasks = different files, no dependencies — can run concurrently
- [Story] label maps task to specific user story for traceability
- Each user story phase includes its own tests (contract + integration) BEFORE implementation
- Backend agents (RequirementsAgent, CompletenessReviewer, IntentRouter) are already implemented — tasks focus on fixing gaps and frontend integration
- Unit tests already exist at `tests/unit/pipeline/test_spec_d_002.py` — do NOT create new unit tests
- Integration tests go in `tests/integration/test_phase0_flow.py`
- Contract tests go in `tests/contract/test_phase0_contracts.py`
- E2E tests update existing `tests/e2e/playwright/phase0-bdd-acceptance.spec.ts` and extend `tests/e2e/playwright/phase0-manual-scenarios.spec.ts`
- Commit after each task or logical group with `[SPEC-D-002]` prefix
- Stop at any checkpoint to validate story independently
