# [SPEC-A-012] Unified Structured Logging Format (SPEC-13B)

## Metadata
- **task_id**: SPEC-A-012
- **spec_ref**: SPEC-13B
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M

## Scope
Define the JSON Lines structured log format, the log level usage rules, the 5 mandatory event names (router_fallback, capability_gap, source_fallback, cost_warning, leak_scan_hit), and the sanitization contract (SECRET_REGEXES, no raw prompt/response in logs). Implement as a Python logging formatter and a TypeScript logger interface.

## Allowed Files
- `src/shared/logging/formatter.py`
- `src/shared/logging/log_schema.py`
- `src/shared/logging/log_schema.ts`
- `src/shared/logging/sanitizer.py`
- `src/shared/constants/log_events.py`
- `src/shared/constants/log_events.ts`
- `tests/unit/contracts/test_logging_format.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: Log line schema defines required fields: ts, level, service, event
- [ ] AC-2: Log line schema defines optional fields: project_id, phase, agent, duration_ms, error_code, extra
- [ ] AC-3: Python JSON formatter outputs valid JSON Lines (each line parseable by json.loads)
- [ ] AC-4: 5 special event names defined as constants: router_fallback, capability_gap, source_fallback, cost_warning, leak_scan_hit
- [ ] AC-5: source_fallback events require extra fields: source_attempted, reason_failed, source_used
- [ ] AC-6: Log level rules documented: DEBUG=dev-only, INFO=business-events, WARN=non-fatal, ERROR=fatal
- [ ] AC-7: Production config suppresses DEBUG level output
- [ ] AC-8: Sanitizer strips patterns matching SECRET_REGEXES before log output
- [ ] AC-9: service field constrained to 'api' | 'worker'

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_012.py -v
mypy src/shared/logging/formatter.py src/shared/logging/sanitizer.py --strict
```

## Completion Definition
JSON formatter produces valid structured logs. All 5 special events defined. Sanitizer strips secrets. Log level rules enforced. Tests verify format, required/optional fields, special event constraints, and sanitization.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_012.py | test_required_fields_present |
| AC-2 | tests/unit/contracts/test_spec_a_012.py | test_optional_fields_accepted |
| AC-3 | tests/unit/contracts/test_spec_a_012.py | test_json_lines_parseable |
| AC-4 | tests/unit/contracts/test_spec_a_012.py | test_special_event_constants |
| AC-5 | tests/unit/contracts/test_spec_a_012.py | test_source_fallback_extra_fields |
| AC-6 | tests/unit/contracts/test_spec_a_012.py | test_log_level_documentation |
| AC-7 | tests/unit/contracts/test_spec_a_012.py | test_production_no_debug |
| AC-8 | tests/unit/contracts/test_spec_a_012.py | test_sanitizer_strips_secrets |
| AC-9 | tests/unit/contracts/test_spec_a_012.py | test_service_field_enum |
