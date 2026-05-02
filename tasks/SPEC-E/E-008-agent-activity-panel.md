# [SPEC-E-008] Agent Activity Panel (Event Stream)

## Metadata
- **task_id**: SPEC-E-008
- **spec_ref**: SPEC-11.4
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the Agent Activity Panel showing the last 50 events in `[HH:MM:SS] [agent_name] [action] [result/progress]` format. Historical events loaded via `GET /api/projects/{id}/events?limit=50` on page load. Real-time events received via WebSocket `/ws/{project_id}`. Panel prioritizes real-time events; on reconnect, fetches missed events from REST API. Supports scroll-to-top to trigger history loading. DOM update within 200ms of WebSocket message (measured via Performance.mark).

## Allowed Files
- `src/frontend/components/AgentActivityPanel.tsx`
- `src/frontend/components/ActivityEventRow.tsx`
- `src/frontend/hooks/useEventStream.ts`
- `src/frontend/hooks/useWebSocket.ts`
- `src/frontend/types/events.ts`
- `tests/unit/frontend/AgentActivityPanel.test.tsx`
- `tests/unit/frontend/useEventStream.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Panel displays up to 50 events with format `[HH:MM:SS] [agent_name] [action] [result/progress]`
- [ ] AC-2: On page load, fetches history via `GET /api/projects/{id}/events?limit=50`
- [ ] AC-3: Real-time events arrive via WebSocket and append to panel
- [ ] AC-4: DOM update completes within 200ms of `WebSocket.onmessage` (Performance.mark instrumentation)
- [ ] AC-5: Scrolling to top triggers loading of older events (pagination)
- [ ] AC-6: After WebSocket disconnect/reconnect, missed events are fetched via REST and merged without duplicates

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_008.py -v
tsc --noEmit
```

## Completion Definition
Agent activity panel displays 50 events, receives real-time updates via WebSocket, handles reconnection with gap-fill, supports scroll-to-load-more. Performance target met. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_008.py | test_renders_50_events_formatted |
| AC-2 | tests/unit/frontend/test_spec_e_008.py | test_fetches_history_on_mount |
| AC-3 | tests/unit/frontend/test_spec_e_008.py | test_appends_ws_events |
| AC-4 | tests/unit/frontend/test_spec_e_008.py | test_dom_update_within_200ms |
| AC-5 | tests/unit/frontend/test_spec_e_008.py | test_scroll_top_loads_history |
| AC-6 | tests/unit/frontend/test_spec_e_008.py | test_reconnect_fills_gap_no_duplicates |
