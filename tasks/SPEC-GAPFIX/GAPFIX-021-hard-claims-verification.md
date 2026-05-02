# [SPEC-GAPFIX-021] hard claims 验证阻断

## Metadata
- **task_id**: SPEC-GAPFIX-021
- **spec_ref**: Design Spec §6.2
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M

## Scope
Add `check_hard_claims()` to `gate_p8.py`, `gate_p10.py`, `gate_p11.py` that queries unverified claims from the DB and blocks phase advance if any exist.

## Allowed Files
- `src/backend/gates/gate_p8.py`
- `src/backend/gates/gate_p10.py`
- `src/backend/gates/gate_p11.py`
- `tests/unit/gates/test_hard_claims.py`

## Forbidden Files
- `src/backend/api/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `check_hard_claims(db, project_id)` 查询 `claims` 表中 `verification_status != 'verified'` 的记录
- [ ] AC-2: 存在未验证 claim 时返回非空列表，每个元素包含 `claim_id`
- [ ] AC-3: 全部 verified 时返回空列表
- [ ] AC-4: gate_p8/p10/p11 在 check() 中调用 `check_hard_claims`，非空时返回 BLOCK

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/gates/test_hard_claims.py -v
.venv/bin/python3 -m ruff check src/backend/gates/gate_p8.py src/backend/gates/gate_p10.py src/backend/gates/gate_p11.py
```

## Completion Definition
3 个 gate 文件均包含 `check_hard_claims` 调用，未验证 claim 阻断 phase advance。测试通过。

## Implementation Notes
```python
def check_hard_claims(db: sqlite3.Connection, project_id: str) -> list[str]:
    rows = db.execute(
        "SELECT claim_id FROM claims WHERE project_id = ? AND verification_status != 'verified'",
        (project_id,)
    ).fetchall()
    return [r['claim_id'] for r in rows]
```
