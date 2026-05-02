# [SPEC-GAPFIX-020] preflight — 真实检查器 (llm/tts/sqlite/disk)

## Metadata
- **task_id**: SPEC-GAPFIX-020
- **spec_ref**: Design Spec §6.1
- **depends_on**: [GAPFIX-011]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Replace 4 of 9 `_stub_ok()` preflight checkers with real implementations. Critical checks (llm, tts, sqlite, disk) must verify the actual dependency is reachable. Degradable checks can remain stub with WARN logging.

## Allowed Files
- `src/backend/core/preflight.py`
- `tests/unit/core/test_preflight.py`

## Forbidden Files
- `src/backend/api/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `check_llm` — 发送轻量 LLM completion (1 token) 验证连通性
- [ ] AC-2: `check_tts` — ping TTS provider health endpoint
- [ ] AC-3: `check_sqlite` — `SELECT 1` + 写测试验证 DB 可读写
- [ ] AC-4: `check_disk` — `shutil.disk_usage` 验证可用空间 ≥ 100MB
- [ ] AC-5: 5 个降级检查器 (web_search, material, bgm, financial_data) 保留 stub 但记录 WARN 日志
- [ ] AC-6: `grep -c '_stub_ok' src/backend/core/preflight.py` 输出 < 9

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/core/test_preflight.py -v
.venv/bin/python3 -m ruff check src/backend/core/preflight.py
grep -c '_stub_ok' src/backend/core/preflight.py  # 期望 < 9
```

## Completion Definition
4 个关键检查器有真实实现，5 个降级检查器为 stub+WARN。测试通过。
