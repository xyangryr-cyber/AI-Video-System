# [SPEC-GAPFIX-018] ConnectionManager — 连接池 + broadcast

## Metadata
- **task_id**: SPEC-GAPFIX-018
- **spec_ref**: Design Spec §5.1
- **depends_on**: [GAPFIX-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Extend `src/backend/api/routes/websocket.py` from 50-line ping/pong to a full ConnectionManager with per-project connection pooling and broadcast capability.

## Allowed Files
- `src/backend/api/routes/websocket.py`
- `tests/unit/api/test_websocket.py`

## Forbidden Files
- `src/backend/core/event_bus.py` (handled by GAPFIX-019)
- `src/backend/engine/**` (no circular imports)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `ConnectionManager` 类存在，包含 `connect()`, `disconnect()`, `broadcast()` 方法
- [ ] AC-2: `connect()` 接受 `project_id` 和 `WebSocket`，加入连接池
- [ ] AC-3: `disconnect()` 从连接池移除
- [ ] AC-4: `broadcast(project_id, event_type, payload)` 向该 project 的所有连接发送 JSON 消息
- [ ] AC-5: 消息格式为 `{"event_type": "...", "payload": {...}, "ts": "..."}`
- [ ] AC-6: 保持现有 ping/pong 心跳机制
- [ ] AC-7: 模块级 `manager = ConnectionManager()` 单例

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_websocket.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/websocket.py
```

## Completion Definition
`ConnectionManager` 类实现连接池 + broadcast，模块级 `manager` 单例可用。测试通过。

## Implementation Notes
- 不直接 import `src/backend/engine/` 模块以避免循环依赖
- broadcast 函数签名接受 `(project_id: str, event_type: str, payload: dict)`
- 使用 `asyncio` 原生异步，不引入额外依赖
