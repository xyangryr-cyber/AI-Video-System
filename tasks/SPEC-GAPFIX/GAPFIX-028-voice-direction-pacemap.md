# [SPEC-GAPFIX-028] voice_direction PACE_MAP 5 级映射

## Metadata
- **task_id**: SPEC-GAPFIX-028
- **spec_ref**: Design Spec §7.3
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: S

## Scope
Fix `src/backend/services/voice_direction_bridge.py` PACE_MAP: change from 3-level `{slow: 0.8, medium: 1.0, fast: 1.2}` to 5-level per SPEC.

## Allowed Files
- `src/backend/services/voice_direction_bridge.py`
- `tests/unit/services/test_voice_direction.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: PACE_MAP 包含 5 个级别: `much_slower` (0.7), `slightly_slower` (0.9), `normal` (1.0), `slightly_faster` (1.1), `much_faster` (1.3)
- [ ] AC-2: 所有引用 PACE_MAP 的代码已更新
- [ ] AC-3: `"slow"`, `"medium"`, `"fast"` 旧键不再存在

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_voice_direction.py -v
.venv/bin/python3 -c "
from src.backend.services.voice_direction_bridge import PACE_MAP
assert PACE_MAP == {'much_slower': 0.7, 'slightly_slower': 0.9, 'normal': 1.0, 'slightly_faster': 1.1, 'much_faster': 1.3}, f'Unexpected PACE_MAP: {PACE_MAP}'
print('PACE_MAP: 5-level OK')
"
```

## Completion Definition
PACE_MAP 为 5 级映射，旧 3 级键已移除。测试通过。
