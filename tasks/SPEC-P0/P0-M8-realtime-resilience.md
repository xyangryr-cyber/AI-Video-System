# [SPEC-P0-M8] 实时通信与状态恢复

## Metadata
- **task_id**: SPEC-P0-M8
- **spec_ref**: Phase0需求.md §10.2, §10.3; TECH_PLAN_v3.3.md §3.2, §5, §7
- **depends_on**: [SPEC-P0-M1]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现 WebSocket 实时事件推送和前端状态恢复机制。后端在 task 状态变更、phase 状态变更时广播事件。前端通过 WebSocket 接收事件实时更新 UI，断线后通过 REST 兜底恢复完整状态。浏览器关闭后重新打开可恢复，服务重启后从 SQLite 恢复。

**业务闭环**: 系统事件产生 → 实时推送到前端 → UI 无刷新更新；浏览器关闭/服务重启 → 状态完整恢复，用户可继续工作。

## Allowed Files
- `src/backend/api/ws.py`
- `src/backend/services/event_service.py`
- `src/frontend/hooks/useWebSocket.ts`
- `src/frontend/hooks/useProjectState.ts`
- `src/frontend/hooks/useHealthPolling.ts`
- `tests/unit/test_websocket.py`
- `tests/integration/test_realtime.py`
- `tests/integration/test_state_recovery.py`

## Forbidden Files
- `src/backend/agents/**`
- `src/backend/engine/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: WebSocket 端点 `/ws/projects/{id}` 建立连接后，task 状态变更时推送事件（含 task_id / type / old_status / new_status / timestamp）
- [ ] AC-2: phase 状态变更时推送事件（含 phase_number / old_status / new_status / timestamp）
- [ ] AC-3: Agent 活动事件推送（agent_name / action / duration_ms / tokens / cost）
- [ ] AC-4: 前端 WebSocket hook 自动重连（指数退避：1s → 2s → 4s → 8s，最大 30s）
- [ ] AC-5: WebSocket 断线期间前端通过 `GET /projects/{id}/state` REST 兜底拉取全量状态，合并后渲染
- [ ] AC-6: `GET /projects/{id}/state` 返回完整项目状态：project 信息 + phases 数组 + task_ledger 数组 + async_tasks 数组
- [ ] AC-7: 前端页面首次加载时调用 `GET /projects/{id}/state` 获取初始状态，恢复时间 ≤ 10s
- [ ] AC-8: 浏览器关闭后重新打开 → 前端从 SQLite 恢复完整状态（通过 REST API），不依赖内存状态
- [ ] AC-9: 服务重启后 → API 从 SQLite 恢复所有状态，不需要 Agent 参与恢复
- [ ] AC-10: 前端任务清单面板通过 WebSocket 实时更新状态图标和持续时间，无需手动刷新
- [ ] AC-11: Pre-flight 健康检查每 30s 轮询（`/projects/{id}` 页面），状态变化实时更新 Banner

## Verification Commands
```bash
# WebSocket unit tests
pytest tests/unit/test_websocket.py -v

# Integration tests - realtime events
pytest tests/integration/test_realtime.py::test_task_status_event_pushed -v
pytest tests/integration/test_realtime.py::test_phase_status_event_pushed -v
pytest tests/integration/test_realtime.py::test_websocket_reconnect -v

# Integration tests - state recovery
pytest tests/integration/test_state_recovery.py::test_api_returns_full_state -v
pytest tests/integration/test_state_recovery.py::test_browser_close_recovery -v
pytest tests/integration/test_state_recovery.py::test_service_restart_recovery -v

# Frontend hook tests
npx vitest run tests/frontend/test_useWebSocket.test.ts
npx vitest run tests/frontend/test_useProjectState.test.ts

# Type check
mypy src/backend/api/ws.py --strict
npx tsc --noEmit
```

## Completion Definition
WebSocket 正确推送 task/phase/agent 事件。前端实时更新 UI 无需手动刷新。断线自动重连 + REST 兜底恢复。浏览器关闭/服务重启后状态完整恢复。Pre-flight 轮询正常。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-1, AC-10 | 场景 1.2-1.4 — 任务状态实时更新 | 1.2e → 1.3e-f → 1.4a 状态自动变化 |
| AC-2 | 场景 4.4 — Phase 状态变更 | 4.4a-c Phase 0 变勾 + Phase 1 高亮 |
| AC-7, AC-8 | 场景 6.3 — 页面恢复 | 6.3 关闭浏览器 → 重新打开 → 状态恢复 |
| AC-11 | Pre-flight 轮询 | 健康状态变化实时更新 Banner |
