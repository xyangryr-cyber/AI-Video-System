# [SPEC-GAPFIX-041] 3 个缺失后端路由

## Metadata
- **task_id**: SPEC-GAPFIX-041
- **spec_ref**: 第四轮扫描报告 发现 3.4; SPEC-1A
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M

## Scope
前端调用了 3 个后端路由表中完全不存在 API 路径:

| 前端调用 | 源文件 |
|----------|--------|
| `POST /api/projects/{id}/materials/supplement` | `src/frontend/api/material_actions.ts:18` |
| `GET /api/projects/{id}/preferences/writeback-suggestions` | `src/frontend/hooks/usePreferenceWriteback.ts:28` |
| `POST /api/projects/{id}/preferences/stage` | `src/frontend/hooks/usePreferenceWriteback.ts:44` |

修复:
1. 在 `src/backend/api/routes/projects.py` 添加 3 个路由 (或创建独立 route 文件)
2. `POST .../materials/supplement`: 接收 `{ shot_id, material_type, description }`, 返回 `{ task_id, material_id }`
3. `GET .../preferences/writeback-suggestions`: 返回 `{ suggestions: WritebackSuggestion[] }`
4. `POST .../preferences/stage`: 接收 `{ suggestion_ids: string[] }`, 暂存偏好

## Allowed Files
- `src/backend/api/routes/projects.py`
- `tests/unit/backend/test_missing_routes.py` (新建)

## Forbidden Files
- `src/frontend/**` (前端调用正确, 不改)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `POST /api/projects/{id}/materials/supplement` 存在且返回 200 (非 501)
- [ ] AC-2: `GET /api/projects/{id}/preferences/writeback-suggestions` 存在且返回 200
- [ ] AC-3: `POST /api/projects/{id}/preferences/stage` 存在且返回 200
- [ ] AC-4: 3 个路由的响应格式匹配前端期望的类型
- [ ] AC-5: `pytest tests/unit/backend/test_missing_routes.py -v` 通过

## Verification Commands
```bash
# 验证路由存在
grep -n "materials/supplement\|writeback-suggestions\|preferences/stage" src/backend/api/routes/projects.py
# 路由测试
.venv/bin/python -m pytest tests/unit/backend/test_missing_routes.py -v
# 全量回归
.venv/bin/python -m pytest tests/unit/ tests/contract/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
3 个缺失路由全部存在, 返回符合前端类型定义的响应。路由测试覆盖: 成功/404/参数校验。全量回归通过。

## Note
这些路由实现初期可返回 mock/fixture 数据, 确保前后端接口对齐。完整业务逻辑留待对应 SPEC 任务实现。
