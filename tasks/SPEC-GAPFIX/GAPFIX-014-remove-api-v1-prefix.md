# [SPEC-GAPFIX-014] 删除 /api/v1/ 前缀 (8 文件 13 处)

## Metadata
- **task_id**: SPEC-GAPFIX-014
- **spec_ref**: Design Spec §4.1
- **depends_on**: [GAPFIX-011]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Remove all `/api/v1/` string literals from frontend source files. Replace with `/api/` prefix.

## Allowed Files
- `src/frontend/mocks/handlers.ts`
- `src/frontend/types/project.ts`
- `src/frontend/components/CandidateSelector.tsx`
- `src/frontend/hooks/useProjects.ts`
- `src/frontend/hooks/useCreateProject.ts`
- `src/frontend/hooks/usePreferenceWriteback.ts`
- `src/frontend/hooks/useEventStream.ts`
- `src/frontend/hooks/useProjectState.ts`
- `tests/unit/frontend/test_api_prefix.py` (if pytest) or vitest test

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `grep -rn '/api/v1/' src/frontend/` 返回 0 行
- [ ] AC-2: 所有 13 处 `/api/v1/` 替换为 `/api/`
- [ ] AC-3: `cd src/frontend && npx vitest run` 通过 (259 tests)

## Verification Commands
```bash
grep -rn '/api/v1/' src/frontend/ | wc -l  # 期望 0
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
`grep -rn '/api/v1/' src/frontend/` 返回空。vitest 259 tests 通过。

## Detailed Changes
| 文件 | 行号 | 改动 |
|------|------|------|
| `mocks/handlers.ts` | 11,12,13,17,18 | `/api/v1/` → `/api/` |
| `types/project.ts` | 1 | 注释 `GET /api/v1/projects` → `GET /api/projects` |
| `components/CandidateSelector.tsx` | 22 | `/api/v1/projects/` → `/api/projects/` |
| `hooks/useProjects.ts` | 12 | `/api/v1/projects` → `/api/projects` |
| `hooks/useCreateProject.ts` | 10 | `/api/v1/projects` → `/api/projects` |
| `hooks/usePreferenceWriteback.ts` | 29,45 | `/api/v1/` → `/api/` |
| `hooks/useEventStream.ts` | 12 | `/api/v1/` → `/api/` |
| `hooks/useProjectState.ts` | 8 | `/api/v1/` → `/api/` |
