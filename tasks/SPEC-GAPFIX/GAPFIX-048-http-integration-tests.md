# [SPEC-GAPFIX-048] 前后端 HTTP 集成测试

## Metadata
- **task_id**: SPEC-GAPFIX-048
- **spec_ref**: 第四轮扫描报告 发现 4.3
- **depends_on**: [GAPFIX-037, GAPFIX-038]
- **priority**: P2
- **estimated_complexity**: M

## Scope
54 个集成测试主要是后端 pipeline 集成 (contract tests、fixture validation), **前后端 HTTP 集成测试缺失** — 没有测试从前端 API 调用到后端路由的完整链路。

创建集成测试验证前端 API 调用 → 后端路由的完整链路:
1. `test_frontend_api_client_integration.py` — apiClient 通过 HTTP 调用后端
2. `test_proxy_routing.py` — Vite proxy `/api/*` → 后端转发正确

## Allowed Files
- `tests/integration/test_frontend_api_client_integration.py` (新建)
- `tests/integration/test_proxy_routing.py` (新建)

## Forbidden Files
- `src/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `test_frontend_api_client_integration.py` 验证 `GET /api/projects` 返回 200
- [ ] AC-2: `test_frontend_api_client_integration.py` 验证 `POST /api/projects` 返回 201
- [ ] AC-3: `test_frontend_api_client_integration.py` 验证 `GET /api/projects/{id}/state` 返回 200
- [ ] AC-4: `test_proxy_routing.py` 验证 proxy 路径转发正确
- [ ] AC-5: 测试使用 FastAPI TestClient, 不依赖真实 Docker 环境
- [ ] AC-6: `pytest tests/integration/test_frontend_api_client_integration.py tests/integration/test_proxy_routing.py -v` 通过

## Verification Commands
```bash
# HTTP 集成测试
.venv/bin/python -m pytest tests/integration/test_frontend_api_client_integration.py tests/integration/test_proxy_routing.py -v
# 全量回归
.venv/bin/python -m pytest tests/unit/ tests/contract/ tests/integration/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
2 个 HTTP 集成测试文件, 覆盖首屏依赖的 4 个 API 调用链路。测试通过。
