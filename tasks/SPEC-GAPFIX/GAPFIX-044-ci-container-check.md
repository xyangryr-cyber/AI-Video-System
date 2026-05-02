# [SPEC-GAPFIX-044] CI 加入容器连通性验证

## Metadata
- **task_id**: SPEC-GAPFIX-044
- **spec_ref**: 第四轮扫描报告 发现 6.1
- **depends_on**: [GAPFIX-034, GAPFIX-035, GAPFIX-036, GAPFIX-037, GAPFIX-038]
- **priority**: P1
- **estimated_complexity**: S

## Scope
当前 CI (`.github/workflows/ci.yml`) 不验证 Docker 环境连通性:
- 不验证 `docker compose up` 是否成功
- 不验证容器间 HTTP 通信
- 不验证前端→后端 API 代理是否工作

修复: 在 `ci.yml` 添加 `container-smoke` job, 启动 docker compose 并验证:
1. 后端 `/health` 返回 200
2. 前端返回非错误 HTML
3. 前端 proxy `/api/projects` 转发成功

## Allowed Files
- `.github/workflows/ci.yml`

## Forbidden Files
- `src/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `ci.yml` 新增 `container-smoke` job
- [ ] AC-2: 包含 `docker compose -f docker-compose.dev.yml up -d`
- [ ] AC-3: 包含 `curl -sf http://localhost:8000/health` 健康检查 (含 retry)
- [ ] AC-4: 包含 `curl -sf http://localhost:3000` 前端可访问
- [ ] AC-5: `curl http://localhost:3000/api/projects | python3 -c "import json,sys; json.load(sys.stdin)"` API proxy 验证

## Verification Commands
```bash
# 验证 job 定义
grep -A20 "container-smoke" .github/workflows/ci.yml
# 验证 docker compose 步骤
grep -n "docker compose" .github/workflows/ci.yml
# 验证 health check
grep -n "health\|curl" .github/workflows/ci.yml
```

## Completion Definition
`ci.yml` 含 `container-smoke` job, PR 合并前自动验证 Docker 环境连通性。配置语法正确 (可用 `act` 或 push 触发验证)。

## Note
Per HARNESS §4.3, CI config changes are TDD-exempt. 容器冒烟 job 使用 `docker-compose.dev.yml` 以匹配 CI 的 Ubuntu runner 环境 (无 Dockerfile build, 用 slim image 快速启动)。
