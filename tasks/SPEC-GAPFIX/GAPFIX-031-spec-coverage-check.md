# [SPEC-GAPFIX-031] check_spec_coverage.py

## Metadata
- **task_id**: SPEC-GAPFIX-031
- **spec_ref**: Design Spec §8.3
- **depends_on**: [GAPFIX-001, GAPFIX-003, GAPFIX-005..013, GAPFIX-018, GAPFIX-020..025]
- **priority**: P2
- **estimated_complexity**: M

## Scope
Create `scripts/check_spec_coverage.py` — a CI script that checks 12 phases × 4 dimensions (Producer/Reviewer/Gate/Worker) for coverage. Outputs missing items list, non-zero exit on gaps.

## Allowed Files
- `scripts/check_spec_coverage.py`
- `tests/unit/scripts/test_spec_coverage.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 扫描所有 12 个 Phase，检查 Producer（agent）、Reviewer（L1+L2）、Gate（进入条件）、Worker（异步任务）是否存在
- [ ] AC-2: 发现缺失项时输出 `MISSING: <phase> <dimension>` 格式
- [ ] AC-3: 有缺失项时 `sys.exit(1)`
- [ ] AC-4: 全绿时 `sys.exit(0)` 且输出 "ALL 12 PHASES COVERED"

## Verification Commands
```bash
.venv/bin/python3 scripts/check_spec_coverage.py
.venv/bin/python3 -m pytest tests/unit/scripts/test_spec_coverage.py -v
```

## Completion Definition
`check_spec_coverage.py` 可用，输出 12 Phase × 4 维度覆盖状态。测试通过。
