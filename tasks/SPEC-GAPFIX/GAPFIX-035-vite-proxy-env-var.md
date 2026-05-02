# [SPEC-GAPFIX-035] vite.config.ts proxy target 改用环境变量

## Metadata
- **task_id**: SPEC-GAPFIX-035
- **spec_ref**: 第四轮扫描报告 发现 2.1
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
`src/frontend/vite.config.ts:31-32` 中 proxy target 硬编码 `http://localhost:8000`。Docker 网络中 `localhost` 指向容器自身, 不指向后端容器, 所有 `/api` 代理请求失败。

修复: 读取 `VITE_API_TARGET` 环境变量, 默认值 `http://localhost:8000`。Docker 环境中通过 `docker-compose.dev.yml` 传入 `VITE_API_TARGET=http://backend:8000`。

## Allowed Files
- `src/frontend/vite.config.ts`

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: proxy `/api` target 从 `process.env.VITE_API_TARGET` 读取, 默认 `http://localhost:8000`
- [ ] AC-2: proxy `/ws` target 从同一变量派生 (http→ws), 默认 `ws://localhost:8000`
- [ ] AC-3: 保留 `port: 3000, host: "0.0.0.0"` 配置
- [ ] AC-4: `docker-compose.dev.yml` 中 frontend 服务添加 `VITE_API_TARGET=http://backend:8000`
- [ ] AC-5: `pnpm --filter frontend test` 全部通过

## Verification Commands
```bash
# 验证 proxy target 不再是硬编码 localhost
grep -A3 'proxy' src/frontend/vite.config.ts
# 验证 dev compose 中的环境变量
grep "VITE_API_TARGET" docker-compose.dev.yml
# 前端测试
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
vite.config.ts proxy 从环境变量读取 target, docker-compose.dev.yml 传入正确的容器间地址。前端测试通过。

## Note
Per HARNESS §4.3, config file changes (vite.config.ts) are TDD-exempt.
