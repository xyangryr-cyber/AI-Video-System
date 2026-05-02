# [SPEC-GAPFIX-019] event_bus 回调注入 + WS 集成测试

## Metadata
- **task_id**: SPEC-GAPFIX-019
- **spec_ref**: Design Spec §5.2-5.3
- **depends_on**: [GAPFIX-018]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create `src/backend/core/event_bus.py` with a callback injection pattern. This allows engine/pipeline code to emit events without importing websocket modules, breaking the circular dependency.

## Allowed Files
- `src/backend/core/event_bus.py`
- `src/backend/api/routes/websocket.py` (add `set_broadcast_handler` call point)
- `tests/integration/test_ws_broadcast.py`

## Forbidden Files
- `src/backend/engine/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `event_bus.py` 导出 `set_broadcast_handler(handler)` 和 `emit(project_id, event_type, payload)`
- [ ] AC-2: `emit()` 调用已注册的 handler，未注册时 no-op (不抛异常)
- [ ] AC-3: WS 集成测试: 连接 WS → 模拟 phase advance → 断言收到事件
- [ ] AC-4: 集成测试覆盖 3+ 种事件类型

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/integration/test_ws_broadcast.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no  # 验证无回归
```

## Completion Definition
`event_bus.py` 回调注入模式可用。WS 集成测试通过，覆盖 3+ 种事件类型。无循环依赖。

## Implementation Notes
```python
# event_bus.py 核心模式:
_broadcast_handler: Callable | None = None

def set_broadcast_handler(handler):
    global _broadcast_handler
    _broadcast_handler = handler

async def emit(project_id: str, event_type: str, payload: dict):
    if _broadcast_handler:
        await _broadcast_handler(project_id, event_type, payload)
```
