# [SPEC-GAPFIX-046] docker-compose 服务命名统一

## Metadata
- **task_id**: SPEC-GAPFIX-046
- **spec_ref**: 第四轮扫描报告 发现 5.1
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: M

## Scope
两个 compose 文件服务命名不一致:

| 维度 | `docker-compose.yml` | `docker-compose.dev.yml` |
|------|---------------------|--------------------------|
| 前端服务名 | `web` | `frontend` |
| 后端服务名 | `api` | `backend` |
| Worker | 有 | 无 |

修复方案（最小变更原则 — 只改 dev 文件让其统一到 prod 命名）:
1. `docker-compose.dev.yml`: `frontend` → `web`, `backend` → `api`
2. `docker-compose.dev.yml`: 添加 `worker` 服务 (与 prod 一致, 即使当前无逻辑)
3. `docker-compose.dev.yml`: 更新 `depends_on: [api]`
4. `docker-compose.yml`: 添加 `web` 的 `depends_on: api`

不在本次 scope 内:
- dev 和 prod 的镜像构建方式差异 (dev 用 slim image 快速启动是合理的)
- 依赖安装时机差异 (dev 启动时安装是设计选择)

## Allowed Files
- `docker-compose.dev.yml`
- `docker-compose.yml` (仅添加 depends_on)

## Forbidden Files
- `src/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `docker-compose.dev.yml` 前端服务名统一为 `web`
- [ ] AC-2: `docker-compose.dev.yml` 后端服务名统一为 `api`
- [ ] AC-3: `docker-compose.dev.yml` 添加 `worker` 服务
- [ ] AC-4: `docker-compose.yml` 中 `web` 添加 `depends_on: [api]`
- [ ] AC-5: `docker compose -f docker-compose.dev.yml config` 语法正确
- [ ] AC-6: `docker compose -f docker-compose.yml config` 语法正确
- [ ] AC-7: 更新所有引用旧服务名的文档/脚本 (如 nightly_e2e.yml)

## Verification Commands
```bash
# 验证 dev compose 语法
docker compose -f docker-compose.dev.yml config --quiet 2>&1
# 验证 prod compose 语法
docker compose -f docker-compose.yml config --quiet 2>&1
# 确认服务名统一
grep -A1 "services:" docker-compose.dev.yml | head -5
grep -A1 "services:" docker-compose.yml | head -5
# 确认 nightly_e2e.yml 无旧服务名
grep -rn "backend\|frontend" .github/workflows/nightly_e2e.yml || echo "OK: no old names"
```

## Completion Definition
两个 compose 文件服务名统一 (web/api/worker), depends_on 链完整。compose config 语法正确。

## Note
Per HARNESS §4.3, config file changes are TDD-exempt. 本 card 是纯配置变更, 不涉及代码逻辑。
