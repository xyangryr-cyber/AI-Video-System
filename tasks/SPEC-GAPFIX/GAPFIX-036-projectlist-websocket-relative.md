# [SPEC-GAPFIX-036] ProjectList.tsx WebSocket URL 改为相对路径

## Metadata
- **task_id**: SPEC-GAPFIX-036
- **spec_ref**: 第四轮扫描报告 发现 1.2 + 发现 2.2
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
`src/frontend/pages/ProjectList.tsx:8` 中 WebSocket URL 硬编码 `ws://localhost:8000/ws/projects`, 在 Docker 环境中 `localhost:8000` 指向前端容器自身, WebSocket 连接必然失败。

修复: 将硬编码 URL 改为从 `location.host` 构建相对路径, 经 Vite proxy 转发:
```typescript
const wsUrl = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/projects`
```

这使 WebSocket 请求走浏览器当前 host, Vite dev server 的 proxy 会将其转发到后端。

## Allowed Files
- `src/frontend/pages/ProjectList.tsx`

## Forbidden Files
- `src/backend/**`
- `src/frontend/hooks/useProjects.ts` (接口设计正确, 不需要改)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 不再出现硬编码 `localhost:8000` 字符串
- [ ] AC-2: wsUrl 使用 `location.protocol` + `location.host` 构建
- [ ] AC-3: 支持 `wss:` (http→ws, https→wss 自动适配)
- [ ] AC-4: `pnpm --filter frontend test` 全部通过

## Verification Commands
```bash
# 确认无 localhost:8000 硬编码
grep -n "localhost:8000" src/frontend/pages/ProjectList.tsx && echo "FAIL: still hardcoded" || echo "PASS: no hardcoded localhost"
# 确认相对路径逻辑
grep -n "location.protocol\|location.host\|/ws/projects" src/frontend/pages/ProjectList.tsx
# 前端测试
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -10
```

## Completion Definition
ProjectList.tsx 中 WebSocket URL 不再硬编码 localhost, 改为从浏览器 location 构建相对路径。前端测试通过。
