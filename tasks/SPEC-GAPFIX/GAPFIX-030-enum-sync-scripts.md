# [SPEC-GAPFIX-030] 枚举同步脚本

## Metadata
- **task_id**: SPEC-GAPFIX-030
- **spec_ref**: Design Spec §8.2
- **depends_on**: [GAPFIX-001, GAPFIX-003]
- **priority**: P2
- **estimated_complexity**: M

## Scope
Create `scripts/generate_event_types.py` (Python→TypeScript) and `scripts/generate_error_codes.py` (Python→TypeScript) that auto-generate cross-language enum files from the Python source of truth. Also support `--check` mode for CI.

## Allowed Files
- `scripts/generate_event_types.py`
- `scripts/generate_error_codes.py`
- `tests/unit/scripts/test_enum_sync.py`

## Forbidden Files
- `src/shared/contracts/event_types.py` (source of truth, read-only for generation)
- `src/shared/contracts/error_codes.py` (source of truth, read-only for generation)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `generate_event_types.py` 读取 `event_types.py` → 生成/更新 `event_types.ts`
- [ ] AC-2: `generate_error_codes.py` 读取 `error_codes.py` → 生成/更新 `error_codes.ts`
- [ ] AC-3: `--check` 模式在不一致时非零退出 (CI 集成)
- [ ] AC-4: 生成产物的跨语言一致性测试通过

## Verification Commands
```bash
.venv/bin/python3 scripts/generate_event_types.py --check
.venv/bin/python3 scripts/generate_error_codes.py --check
.venv/bin/python3 -m pytest tests/unit/scripts/test_enum_sync.py -v
```

## Completion Definition
两个生成脚本可用，`--check` 模式验证跨语言一致性。测试通过。
