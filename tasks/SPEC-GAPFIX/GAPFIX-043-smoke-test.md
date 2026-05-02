# [SPEC-GAPFIX-043] 应用冒烟测试

## Metadata
- **task_id**: SPEC-GAPFIX-043
- **spec_ref**: 第四轮扫描报告 发现 4.2; 根因报告根因 1
- **depends_on**: [GAPFIX-034, GAPFIX-035, GAPFIX-036, GAPFIX-037, GAPFIX-038]
- **priority**: P1
- **estimated_complexity**: M

## Scope
`tests/smoke/` 目录不存在, 没有任何测试验证应用能否启动和核心功能。

创建冒烟测试套件, 验证:
1. 应用能否正常启动 (FastAPI + Vite)
2. 关键端点是否返回 200 (非 501/5xx)
3. 前端 MSW 是否正确初始化
4. Docker 环境中前后端能否通信

## Allowed Files
- `tests/smoke/__init__.py` (新建)
- `tests/smoke/test_app_startup.py` (新建)
- `tests/smoke/test_key_endpoints.py` (新建)
- `tests/smoke/conftest.py` (新建, fixtures)

## Forbidden Files
- `src/**` (只新增测试, 不改源码)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `tests/smoke/` 目录存在
- [ ] AC-2: `test_app_startup.py` 验证: FastAPI `/health` 返回 `{"status": "ok"}`
- [ ] AC-3: `test_app_startup.py` 验证: Vite dev server 返回 HTML (非 5xx)
- [ ] AC-4: `test_key_endpoints.py` 验证: `GET /api/projects` 返回 200 (非 501)
- [ ] AC-5: `test_key_endpoints.py` 验证: `GET /api/projects/{id}/state` 返回 200 (非 501)
- [ ] AC-6: `test_key_endpoints.py` 验证: `GET /api/projects/{id}/events` 返回 200
- [ ] AC-7: `test_key_endpoints.py` 验证: `POST /api/projects` 返回 201
- [ ] AC-8: `pytest tests/smoke/ -v` 通过 (依赖外部服务时 skip)

## Verification Commands
```bash
# 冒烟测试
.venv/bin/python -m pytest tests/smoke/ -v
# 全量单元测试确保无回归
.venv/bin/python -m pytest tests/unit/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
`tests/smoke/` 目录含至少 2 个冒烟测试文件, 覆盖应用启动、关键端点 200 验证。冒烟测试通过或在无服务时正确 skip。

## Note
TDD 流程: 先写冒烟测试 → 验证测试在无服务时 skip (RED 阶段用标记) → 启动服务后测试通过 (GREEN)。冒烟测试是环境依赖测试, 使用 `pytest.mark.skipif` 在没有运行服务时自动跳过。
