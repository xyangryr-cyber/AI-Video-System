# [SPEC-B-008] 敏感字段脱敏与泄露扫描

## Metadata
- **task_id**: SPEC-B-008
- **spec_ref**: SPEC-13.3
- **depends_on**: [SPEC-A-xxx] (SPEC-13B 统一日志格式), [SPEC-B-007]
- **priority**: P1
- **estimated_complexity**: S
- **bdd_tags**: [@observability]

## Scope
实现 SECRET_REGEXES 7 条脱敏规则，应用于 `agent_call_log` 的 prompt/response 字段写入前。实现 >8KB 截断策略（首 2KB + 尾 2KB + MD5）。编写 `scripts/leak_scan.py` 每日采样 1000 行检查泄露。

## Allowed Files
- `src/backend/core/redaction.py`
- `src/backend/core/llm_client.py`
- `scripts/leak_scan.py`
- `tests/unit/infra/test_redaction.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 含 `sk-` 前缀的 API Key 在 prompt 写入后仅含 `[REDACTED]`
- [ ] AC-2: SECRET_REGEXES 包含 7 条规则（覆盖常见密钥格式）
- [ ] AC-3: >8KB 的 prompt/response 截断为首 2KB + 尾 2KB + MD5
- [ ] AC-4: `scripts/leak_scan.py` 可执行，采样 1000 行，命中数=0 时通过
- [ ] AC-5: 脱敏在写入 DB 前完成（非查询时脱敏）

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_008.py -v
python scripts/leak_scan.py --dry-run
```

## Completion Definition
所有 LLM 日志写入前经过脱敏处理，泄露扫描脚本可运行且无命中。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_008.py | test_sk_prefix_redacted |
| AC-2 | tests/unit/infra/test_spec_b_008.py | test_secret_regexes_count_7 |
| AC-3 | tests/unit/infra/test_spec_b_008.py | test_large_payload_truncation |
| AC-4 | tests/unit/infra/test_spec_b_008.py | test_leak_scan_zero_hits |
| AC-5 | tests/unit/infra/test_spec_b_008.py | test_redaction_before_db_write |
