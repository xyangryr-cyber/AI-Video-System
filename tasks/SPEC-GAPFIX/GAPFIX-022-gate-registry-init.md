# [SPEC-GAPFIX-022] gate_registry 显式绑定

## Metadata
- **task_id**: SPEC-GAPFIX-022
- **spec_ref**: Design Spec §6.3
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: S

## Scope
Create `src/backend/gates/__init__.py` that explicitly registers all 12 gates (P0-P11) into `gate_registry`. Currently `gate_registry.py` exists but no code calls `register()`.

## Allowed Files
- `src/backend/gates/__init__.py`
- `tests/unit/gates/test_gate_registry.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `gates/__init__.py` 存在
- [ ] AC-2: 导入所有 12 个 gate 类 (GateP0..GateP11)
- [ ] AC-3: 通过 `gate_registry.register(i, gate_cls)` 注册每个 gate
- [ ] AC-4: `.venv/bin/python3 -c "from src.backend.gates import gate_registry; assert len(gate_registry) == 12"` 通过

## Verification Commands
```bash
.venv/bin/python3 -c "from src.backend.gates import gate_registry; assert len(gate_registry) == 12; print(f'{len(gate_registry)} gates registered')"
.venv/bin/python3 -m pytest tests/unit/gates/test_gate_registry.py -v
```

## Completion Definition
`gates/__init__.py` 存在，12 个 gate 全部显式注册到 gate_registry。测试通过。

## Implementation Notes
```python
from src.backend.gates.gate_registry import gate_registry
from src.backend.gates.gate_p0 import GateP0
from src.backend.gates.gate_p1 import GateP1
# ... all 12 gates

for i, gate_cls in enumerate([GateP0, GateP1, ..., GateP11]):
    gate_registry.register(i, gate_cls)
```
