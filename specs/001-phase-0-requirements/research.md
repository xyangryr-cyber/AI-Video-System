# Research: Phase 0 Technical Decisions

**Date**: 2026-05-02
**Context**: Phase 0 implementation plan for AI Video Requirements Definition

## Decision 1: Frontend Data Fetching Strategy

**Decision**: Replace WorkflowPage mock data imports with API-backed hooks (`useProjectState`, `useTasks`, `usePhaseArtifact`).

**Rationale**:
- `WorkflowPage.tsx` imports `MOCK_PROJECT_TITLE`, `MOCK_CURRENT_TASK_TITLE`, `MOCK_TASKS`, `MOCK_FACTUAL_DATA` from `mockData.ts`
- Backend API endpoints (`GET /projects/{id}/state`, `GET /projects/{id}/tasks`, `GET /projects/{id}/phases/0/artifact`) are fully functional
- `P0RequirementsView.tsx` is already implemented and ready to consume real artifact data
- `useChat` and `useAdvance` hooks already call real APIs — only the display data is mocked

**Alternatives considered**:
- **Keep mock data with feature flags**: Rejected — mock data doesn't reflect real state transitions and would hide integration bugs
- **New data fetching library (React Query/SWR)**: Rejected — existing `useProjectState` hook pattern is sufficient; adding a new dependency increases complexity without benefit

**Implementation approach**:
1. `MOCK_PROJECT_TITLE` → `project.title` from `useProjectState(projectId)`
2. `MOCK_TASKS` / `MOCK_CURRENT_TASK_TITLE` → `tasks` from `GET /projects/{id}/tasks` (polled or via WebSocket)
3. `MOCK_FACTUAL_DATA` → Remove from Phase 0 UI (FactualLedger belongs to Phase 2+, not Phase 0)
4. Task status updates → WebSocket `task.updated` events for real-time refresh

## Decision 2: RequirementsAgent Output — Schema Alignment

**Decision**: Add a serialization adapter in `requirements_agent.py` that transforms its internal output dict into the canonical `Requirements` Pydantic model before persisting to `requirements.json`.

**Rationale**:
- `RequirementsAgent.produce()` returns a flat dict: `{"platform": "web", "target_duration_seconds": 600, ...}`
- Canonical `Requirements` schema (`src/shared/schemas/artifacts.py`) expects: `platform: list[PlatformEntry]`, `target_duration: TargetDuration`, `target_word_count: TargetWordCount`
- The mismatch means `requirements.json` written to disk doesn't conform to the shared schema
- Downstream phases (P1+) consume `requirements.json` and expect canonical shape

**Alternatives considered**:
- **Change canonical schema to match agent output**: Rejected — the canonical schema is richer and used by all 12 phases; simplifying it for one agent would ripple downstream
- **Change agent output to match canonical schema**: Rejected — the agent's LLM prompt is tuned to produce flat output; changing the response model would require re-tuning prompts and eval sets
- **Adapter layer (chosen)**: Minimal change, clean separation of concerns, preserves both the agent's tuned output format and the canonical schema

**Implementation approach**:
```python
# In requirements_agent.py, after produce():
def _to_canonical(raw: dict) -> Requirements:
    return Requirements(
        project_id=raw["project_id"],
        title=raw["title"],
        topic=raw["clarified_topic"] or raw["topic"],
        target_duration=TargetDuration(
            min_sec=raw["target_duration_seconds"],
            max_sec=raw["target_duration_seconds"]
        ),
        target_word_count=TargetWordCount(
            min=raw["target_word_count"]["min"],
            max=raw["target_word_count"]["max"]
        ),
        platform=[PlatformEntry(
            name=raw["platform"],
            specs={}  # populated from platform_profiles.json
        )],
        category=Category(
            level1=raw["category"]["level1"],
            level2=raw["category"]["level2"]
        ),
    )
```

## Decision 3: GateP0 Registration

**Decision**: Register `GateP0` in `gate_registry.py` and verify `GateKeeper.check(phase=0)` dispatches to it.

**Rationale**:
- `GateP0` is implemented in `src/backend/gates/gate_p0.py` with 2 checks (artifact existence, review PASS)
- It is NOT registered in `gate_registry.py`, making it undiscoverable through the registry system
- `POST /projects/{id}/advance` calls `GateKeeper.check()` which should dispatch to `GateP0` for phase 0
- Spec FR-023/FR-024 require that GateKeeper programmatically verifies conditions before enabling the advance button

**Implementation approach**:
1. Add `GateP0` to `gate_registry.py`: `register_gate(0, GateP0)`
2. Verify `GateKeeper.check(phase=0)` delegates to `GateP0`
3. Add unit test confirming registration and dispatch

## Decision 4: CompletenessReviewer Package Placement

**Decision**: Re-export `CompletenessReviewer` from `src/backend/reviewers/__init__.py` rather than moving the file.

**Rationale**:
- `CompletenessReviewer` currently lives in `src/backend/agents/completeness_reviewer.py`
- Design docs reference it as a Reviewer, not a Producer Agent
- Moving the file would break imports in `gate_p0.py` and `projects.py`
- Re-exporting preserves backward compatibility while establishing the correct logical package

**Implementation approach**:
```python
# In src/backend/reviewers/__init__.py:
from src.backend.agents.completeness_reviewer import CompletenessReviewer
```

## Decision 5: Real-Time Task Status Updates

**Decision**: Use existing WebSocket infrastructure to push `task.updated` events for Phase 0 task status changes. Frontend `useWebSocket` hook already exists.

**Rationale**:
- Spec FR-021 requires real-time task status updates without manual page refresh
- TECH_PLAN_v3.3 §5 specifies WebSocket push with REST fallback
- Existing `src/backend/api/routes/websocket.py` handles WS connections
- Existing task lifecycle events (`task.created`, `task.started`, `task.completed`, `task.failed`) are emitted by `WorkflowEngine`
- Frontend `useWebSocket` hook in `src/frontend/hooks/` already exists

**Implementation approach**:
1. Verify `task.*` events are emitted during Phase 0 task lifecycle
2. Use `useWebSocket(projectId)` in `WorkflowPage.tsx` to subscribe to task events
3. Update task list UI on each event (no polling needed)
4. REST fallback: `GET /projects/{id}/tasks` on mount and WS reconnect

## Decision 6: Testing Strategy

**Decision**: Three-layer test strategy — contract tests (API boundary), integration tests (Phase 0 flow), E2E tests (Playwright browser tests).

**Rationale**:
- Spec requires "前后端接口契约 集成测试 e2e测试"
- Contract tests verify API request/response shapes match shared schemas
- Integration tests verify the full Phase 0 flow: create → generate → review → revise → advance
- E2E tests (Playwright) verify the complete user journey in a real browser
- Existing `tests/e2e/playwright/phase0-bdd-acceptance.spec.ts` provides extensive BDD coverage (50+ scenarios)

**Implementation approach**:

### Contract Tests (`tests/contract/test_phase0_contracts.py`)
- Verify `POST /projects` response matches `ProjectCreateResponse` schema
- Verify `GET /projects/{id}/state` response includes Phase 0 data
- Verify `GET /projects/{id}/phases/0/artifact` returns valid `Requirements`
- Verify `POST /projects/{id}/chat` request/response shapes
- Verify WebSocket event payloads match `WSEvent` schemas

### Integration Tests (`tests/integration/test_phase0_flow.py`)
- Happy path: create project → wait for artifact → verify review → advance
- Revise flow: create → chat revise → verify new artifact version → new review
- Regenerate flow: create → chat regenerate → verify fresh artifact
- Gate blocking: verify advance blocked when review FAIL
- Gate blocking: verify advance blocked when tasks running
- Error recovery: simulate LLM failure → verify retry → verify success

### E2E Tests (Playwright)
- Existing `phase0-bdd-acceptance.spec.ts` covers BDD scenarios
- Add manual scenario tests from `Phase0_Manual_Test_Scenario.md`
- Verify task list default-collapsed behavior (FR-020)
- Verify advance button disabled states (FR-024)

## Decision 7: Model Routing for Phase 0

**Decision**: Follow TECH_PLAN_v3.3 model routing — Claude for Router/Reviewer/GateKeeper, 豆包 for RequirementsAgent (Producer).

**Rationale**:
- TECH_PLAN_v3.3 §1: "高风险→Claude, 执行→豆包"
- IntentRouter: Claude Haiku (needs high accuracy for intent classification, 3s timeout)
- CompletenessReviewer: Claude (binary PASS/FAIL decision, must be reliable)
- RequirementsAgent: 豆包 (content generation, lower cost)
- GateKeeper: Deterministic code (no LLM call, 0 cost)

**Implementation approach**:
- Router model configured via `model_config.json` `router.model` field
- Reviewer model configured via `model_config.json` `reviewer.model` field
- Producer model configured via `model_config.json` `producer.model` field
- GateKeeper uses only programmatic checks (L1), no LLM

## Decision 8: Error Handling & Recovery

**Decision**: Follow TECH_PLAN_v3.3 §8 failure paths. Phase 0 specific handling:

| Failure | Handling |
|---------|----------|
| RequirementsAgent LLM call fails | Auto-retry 3 times; all fail → task `failed`, frontend shows error + retry button |
| CompletenessReviewer LLM call fails | Auto-retry 3 times; all fail → review skipped, Gate 0 blocks advance with "审核未完成" |
| Router JSON parse failure / timeout | Fallback to `clarify` intent; show 4 action candidate buttons |
| 2 consecutive clarifies | Show action candidate buttons (revise, regenerate, advance, clarify) |
| requirements.json schema validation fails | Task marked `failed`, error details in task result |
| Worker crash during Phase 0 task | Huey retry (default 3 attempts); status visible in task ledger |
