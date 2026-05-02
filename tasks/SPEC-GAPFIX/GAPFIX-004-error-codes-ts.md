# [SPEC-GAPFIX-004] error_codes.ts — TypeScript 版本

## Metadata
- **task_id**: SPEC-GAPFIX-004
- **spec_ref**: Design Spec §2.4
- **depends_on**: [GAPFIX-003]
- **priority**: P0
- **estimated_complexity**: S

## Scope
Define 17 EVID_ error codes as a TypeScript const in `src/shared/contracts/error_codes.ts`, mirroring `error_codes.py`. The frontend `utils/errorUxMap.ts` will import from this file.

## Allowed Files
- `src/shared/contracts/error_codes.ts`
- `tests/unit/contracts/test_error_codes_crosslang.py`

## Forbidden Files
- `src/backend/**`
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: TypeScript 包含恰好 17 个错误码
- [ ] AC-2: 错误码名称与 Python 版本完全一致
- [ ] AC-3: 每个错误码包含 `code`, `status`, `message` 字段

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/contracts/test_error_codes_crosslang.py -v
cd src/frontend && npx tsc --noEmit src/shared/contracts/error_codes.ts
```

## Completion Definition
`error_codes.ts` 存在，17 个错误码与 Python 版本一致，跨语言测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_ts_has_17_error_codes |
| AC-2 | test_py_and_ts_error_codes_identical |
| AC-3 | test_ts_error_codes_have_code_status_message |
