# [SPEC-GAPFIX-015] vite.config.ts 添加 proxy

## Metadata
- **task_id**: SPEC-GAPFIX-015
- **spec_ref**: Design Spec §4.2
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Add proxy configuration to `src/frontend/vite.config.ts` so Vite dev server proxies `/api` to `http://localhost:8000` and `/ws` to `ws://localhost:8000`.

## Allowed Files
- `src/frontend/vite.config.ts`

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `grep -rn 'proxy' src/frontend/vite.config.ts` 返回 proxy 配置
- [ ] AC-2: `/api` 代理到 `http://localhost:8000`
- [ ] AC-3: `/ws` 代理到 `ws://localhost:8000` (WebSocket)
- [ ] AC-4: 保留现有 `port: 3000, host: "0.0.0.0"` 配置

## Verification Commands
```bash
grep -A5 'proxy' src/frontend/vite.config.ts
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
`vite.config.ts` 含 proxy 配置，`/api` → `http://localhost:8000`，`/ws` → `ws://localhost:8000`。vitest 通过。

## Note
Per HARNESS §4.3, config file changes (vite.config.ts) are TDD-exempt.
