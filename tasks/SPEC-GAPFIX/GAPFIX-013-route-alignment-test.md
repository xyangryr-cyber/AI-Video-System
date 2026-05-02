# [SPEC-GAPFIX-013] 路由对齐集成测试

## Metadata
- **task_id**: SPEC-GAPFIX-013
- **spec_ref**: Design Spec §3 验证命令
- **depends_on**: [GAPFIX-011]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create `tests/unit/api/test_route_alignment.py` with automated tests that verify route diff is clean (missing=0, extra=0, double-prefix=0).

## Allowed Files
- `tests/unit/api/test_route_alignment.py`

## Forbidden Files
- `src/backend/api/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `test_route_diff_missing_zero` — 验证 missing routes = 0
- [ ] AC-2: `test_route_diff_extra_zero` — 验证 extra routes = 0
- [ ] AC-3: `test_route_diff_double_prefix_zero` — 验证 double-prefix = 0
- [ ] AC-4: `test_health_endpoint_exists` — 验证 /health 端点存在
- [ ] AC-5: `test_all_routes_return_valid_status` — 对所有路由发 GET/POST 请求，验证不返回 404

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_route_alignment.py -v
```

## Completion Definition
所有 5 个路由对齐测试通过，route diff 全零。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_route_diff_missing_zero |
| AC-2 | test_route_diff_extra_zero |
| AC-3 | test_route_diff_double_prefix_zero |
| AC-4 | test_health_endpoint_exists |
| AC-5 | test_all_routes_return_valid_status |
