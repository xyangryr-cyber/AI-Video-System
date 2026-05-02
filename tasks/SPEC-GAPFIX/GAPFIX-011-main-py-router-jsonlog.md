# [SPEC-GAPFIX-011] main.py — router 注册去 prefix + JSON 日志

## Metadata
- **task_id**: SPEC-GAPFIX-011
- **spec_ref**: Design Spec §3.7 + §3.9
- **depends_on**: [GAPFIX-005, GAPFIX-006, GAPFIX-007, GAPFIX-008, GAPFIX-009, GAPFIX-010]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Update `src/backend/api/main.py`: remove `prefix=` from all `include_router` calls (prefixes are now in each router), add `projects.router`, add JSON line logging, register EVID_ error handler.

## Allowed Files
- `src/backend/api/main.py`
- `tests/unit/api/test_main.py`

## Forbidden Files
- `src/backend/api/routes/*.py` (handled by GAPFIX-005..010)
- `HARNESS.md`

## Current State
```python
app.include_router(system.router, prefix="/api/system", ...)      # extra prefix
app.include_router(tasks.router, prefix="/api/tasks", ...)        # extra prefix
app.include_router(preferences.router, prefix="/api/projects", ...) # extra prefix
app.include_router(observability.router, prefix="/api/observability", ...) # extra prefix
app.include_router(cost.router, prefix="/api/cost", ...)          # extra prefix
app.include_router(settings_bridge.router)  # OK
app.include_router(websocket.router)        # OK
# No projects router
# No JSON logging
# No EVID_ error handler
```

## Acceptance Criteria
- [ ] AC-1: 所有 `include_router` 调用不再传 `prefix=` (settings_bridge, websocket 不变)
- [ ] AC-2: 新增 `app.include_router(projects.router)`
- [ ] AC-3: 导入 `from src.backend.api.routes import projects`
- [ ] AC-4: JSON 日志初始化 (JsonLineFormatter)
- [ ] AC-5: 注册 `evid_error_handler` 为 HTTPException 和 Exception handler
- [ ] AC-6: route diff 脚本输出 missing=0, extra=0, double-prefix=0

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_main.py -v
.venv/bin/python3 -m ruff check src/backend/api/main.py

# Route diff 验证
.venv/bin/python3 -c "
from src.backend.api.main import app
from src.shared.contracts.api_routes import API_ROUTES
import re
def norm(p): return re.sub(r'\{[^}]+\}', '{}', p)
actual = {(m, norm(r.path)) for r in app.routes if hasattr(r,'methods') for m in r.methods if m not in {'HEAD','OPTIONS'}}
expected = {(r['method'], norm(r['path'])) for r in API_ROUTES if r['type']=='rest'}
missing = expected - actual
extra = actual - expected
double = [p for _,p in actual if '/api/' in p[5:]]
assert len(missing) == 0, f'MISSING({len(missing)}): {missing}'
assert len(extra) == 0, f'EXTRA({len(extra)}): {extra}'
assert len(double) == 0, f'DOUBLE({len(double)}): {double}'
print('ALL ROUTE CHECKS PASSED')
"
```

## Completion Definition
`main.py` 所有 router 注册无额外 prefix，route diff 全零，JSON 日志已配置，EVID_ error handler 已注册。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_main_no_extra_prefix_on_include_router |
| AC-5 | test_evid_error_handler_registered |
| AC-6 | test_route_diff_missing_zero |
| AC-6 | test_route_diff_extra_zero |
| AC-6 | test_route_diff_double_prefix_zero |
