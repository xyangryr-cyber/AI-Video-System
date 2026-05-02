# [SPEC-GAPFIX-024] agent_call_log + redact hook

## Metadata
- **task_id**: SPEC-GAPFIX-024
- **spec_ref**: Design Spec §6.5
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M

## Scope
Add `_log_and_redact()` hook in `src/backend/services/llm_service.py` that writes agent call logs to the `agent_call_log` table with sensitive data redacted before storage.

## Allowed Files
- `src/backend/services/llm_service.py`
- `tests/unit/services/test_llm_service_logging.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 每次 LLM 调用后记录 agent_call_log 行 (agent_name, duration_ms, tokens, cost, project_id)
- [ ] AC-2: prompt/response 中的 API key 等敏感信息在写入前被 redact
- [ ] AC-3: redaction 使用 `src.backend.core.redaction.redact_text`
- [ ] AC-4: 日志记录失败不阻断主流程 (best-effort)

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_llm_service_logging.py -v
.venv/bin/python3 -m ruff check src/backend/services/llm_service.py
```

## Completion Definition
LLM 调用后自动记录 agent_call_log + redact。测试通过。
