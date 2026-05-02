# [SPEC-GAPFIX-029] routes SDK 生成脚本 (.py + .ts)

## Metadata
- **task_id**: SPEC-GAPFIX-029
- **spec_ref**: Design Spec §8.1
- **depends_on**: [GAPFIX-011]
- **priority**: P2
- **estimated_complexity**: M

## Scope
Create `scripts/generate_routes_sdk.py` and `scripts/generate_routes_sdk.ts` that read from the contracts `api_routes.py/.ts` and generate type-safe API client SDKs. The generated code is the canonical way to make API calls — direct URL string literals are forbidden after this.

## Allowed Files
- `scripts/generate_routes_sdk.py`
- `scripts/generate_routes_sdk.ts`
- `tests/unit/scripts/test_generate_routes_sdk.py`

## Forbidden Files
- `src/shared/contracts/api_routes.py` (read-only)
- `src/shared/contracts/api_routes.ts` (read-only)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `generate_routes_sdk.py` 读取 `api_routes.py` → 生成 `src/backend/api/routes_sdk.py`
- [ ] AC-2: `generate_routes_sdk.ts` 读取 `api_routes.ts` → 生成 `src/frontend/api/routesSdk.ts`
- [ ] AC-3: 生成的 SDK 为每个路由生成类型安全函数 (参数类型、返回类型)
- [ ] AC-4: 脚本运行后 Python/Typescript 编译通过

## Verification Commands
```bash
.venv/bin/python3 scripts/generate_routes_sdk.py
.venv/bin/python3 -m py_compile src/backend/api/routes_sdk.py
cd src/frontend && npx tsc --noEmit src/frontend/api/routesSdk.ts
.venv/bin/python3 -m pytest tests/unit/scripts/test_generate_routes_sdk.py -v
```

## Completion Definition
生成脚本可用，产物编译通过。测试通过。
