# [SPEC-GAPFIX-017] apiClient 重构 — 消除字面量路径

## Metadata
- **task_id**: SPEC-GAPFIX-017
- **spec_ref**: Design Spec §4.1 (apiClient 部分)
- **depends_on**: [GAPFIX-014, GAPFIX-016]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create a shared `apiClient` module that all hooks use instead of inlining fetch URLs. This prevents future `/api/v1/` regressions.

## Allowed Files
- `src/frontend/hooks/useProjects.ts`
- `src/frontend/hooks/useCreateProject.ts`
- `src/frontend/hooks/usePreferenceWriteback.ts`
- `src/frontend/hooks/useEventStream.ts`
- `src/frontend/hooks/useProjectState.ts`
- `src/frontend/components/CandidateSelector.tsx`
- `src/frontend/utils/api.ts` (new — shared API helper)

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 新建 `src/frontend/utils/api.ts` 导出 `apiUrl(path)` helper
- [ ] AC-2: 所有 hooks 使用 `apiUrl()` 而非字符串拼接 URL
- [ ] AC-3: 不再有任何文件直接写 `/api/` 字面量拼接
- [ ] AC-4: `cd src/frontend && npx vitest run` 通过

## Verification Commands
```bash
# 检查 apiUrl 被所有 hook 使用
grep -l 'apiUrl' src/frontend/hooks/*.ts

# vitest
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
`utils/api.ts` 存在且被所有 hooks 使用。vitest 259 tests 通过。无裸 `/api/` 字面量拼接。
