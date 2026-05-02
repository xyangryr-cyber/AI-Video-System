# [SPEC-GAPFIX-040] POST /api/projects/{id}/preferences/confirm 实现

## Metadata
- **task_id**: SPEC-GAPFIX-040
- **spec_ref**: 第四轮扫描报告 发现 3.3; SPEC-1A
- **depends_on**: [GAPFIX-038]
- **priority**: P1
- **estimated_complexity**: M

## Scope
`src/backend/api/routes/projects.py:104` 中 `confirm_preferences()` 返回 501。前端 `CandidateSelector.tsx:22` 调用此 API 确认候选方案选择。

修复: 实现 `confirm_preferences()`, 接收 `{ phase, decisions: { candidate_id, action } }`, 将偏好决策写入 DB, 返回确认结果。

## Allowed Files
- `src/backend/api/routes/projects.py`
- `tests/unit/backend/test_preferences_confirm.py` (新建)

## Forbidden Files
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `POST /api/projects/{id}/preferences/confirm` 返回 200 (非 501)
- [ ] AC-2: 接受 `phase` (int) 和 `decisions` (object with `candidate_id` + `action`)
- [ ] AC-3: 不存在的 project_id 返回 404
- [ ] AC-4: 参数校验: 缺少必填字段返回 422
- [ ] AC-5: `pytest tests/unit/backend/test_preferences_confirm.py -v` 通过

## Verification Commands
```bash
# 单元测试
.venv/bin/python -m pytest tests/unit/backend/test_preferences_confirm.py -v
# 全量回归
.venv/bin/python -m pytest tests/unit/ tests/contract/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
`POST /api/projects/{id}/preferences/confirm` 接受偏好决策并持久化。单元测试覆盖: 成功/404/422。全量回归通过。

## Note
如果 preferences 相关 DB 表尚不存在, 本 card 先实现内存存储 (dict), 返回符合 SPEC 格式的响应。后续 card 迁移到 DB。
