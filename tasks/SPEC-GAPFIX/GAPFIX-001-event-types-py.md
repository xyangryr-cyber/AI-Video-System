# [SPEC-GAPFIX-001] event_types.py — 17 种 WS 事件枚举

## Metadata
- **task_id**: SPEC-GAPFIX-001
- **spec_ref**: Design Spec §2.1
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Define 17 WebSocket event types as a Python StrEnum in `src/shared/contracts/event_types.py`, per SPEC-11A.

## Allowed Files
- `src/shared/contracts/event_types.py`
- `tests/unit/contracts/test_event_types.py`

## Forbidden Files
- `src/backend/api/**`
- `src/backend/engine/**`
- `src/frontend/**`
- `HARNESS.md`
- `CLAUDE.md`

## Acceptance Criteria
- [ ] AC-1: `EventType` enum 包含恰好 17 个成员
- [ ] AC-2: 覆盖 SPEC-11A 全部类别：phase (3), task (5), review (2), artifact (2), error (1), project (3), preference (1), ws (2), heartbeat (1) — 注意实际为 20，但 SPEC-11A 声明 17，以 SPEC 为准
- [ ] AC-3: 每个 enum 值为小写点分隔格式 (如 `"phase.entered"`)
- [ ] AC-4: `EventType` 可通过字符串值构造 (如 `EventType("phase.entered")`)

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/contracts/test_event_types.py -v
.venv/bin/python3 -c "from src.shared.contracts.event_types import EventType; print(f'{len(EventType)} event types defined')"
```

## Completion Definition
`EventType` StrEnum 存在，包含 17 个成员，每个值符合 SPEC-11A 定义的小写点分隔格式。所有测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_event_type_has_exactly_17_members |
| AC-2 | test_event_type_covers_all_spec_11a_categories |
| AC-3 | test_event_type_values_are_dot_separated |
| AC-4 | test_event_type_constructible_from_string |
