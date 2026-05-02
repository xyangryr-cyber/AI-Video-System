# [SPEC-GAPFIX-045] brandKit.ts 改用 apiClient

## Metadata
- **task_id**: SPEC-GAPFIX-045
- **spec_ref**: 第四轮扫描报告 发现 1.3
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S

## Scope
`src/frontend/render/brandKit.ts:48` 中使用裸 `fetch("/api/settings")` 而非项目统一的 `apiClient`。其他所有前端 API 调用都通过 `apiClient`（统一错误处理、base URL 配置）。

修复: 将 `fetchBrandKit()` 中的 `await fetch("/api/settings")` 替换为 `await apiClient.get("/api/settings")`。

## Allowed Files
- `src/frontend/render/brandKit.ts`

## Forbidden Files
- `src/backend/**`
- `src/frontend/api/client.ts` (apiClient 本身正确, 不需改)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `brandKit.ts` 不再使用裸 `fetch`
- [ ] AC-2: `fetchBrandKit()` 使用 `apiClient.get<{ brand_kit: BrandKit | null }>("/api/settings")`
- [ ] AC-3: 统一错误处理 (apiClient 自动抛出 ApiError)
- [ ] AC-4: `pnpm --filter frontend test` 全部通过

## Verification Commands
```bash
# 确认无裸 fetch
grep -n "fetch(" src/frontend/render/brandKit.ts && echo "FAIL: still uses bare fetch" || echo "PASS"
# 确认使用 apiClient
grep -n "apiClient" src/frontend/render/brandKit.ts
# 前端测试
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -10
```

## Completion Definition
brandKit.ts 不再使用裸 fetch, 改为 apiClient.get 统一错误处理。前端测试通过。
