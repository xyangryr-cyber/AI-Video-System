# [SPEC-A-011] HTTP Error Code System (SPEC-13A)

## Metadata
- **task_id**: SPEC-A-011
- **spec_ref**: SPEC-13A
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@error_ux]

## Scope
Define the unified API error response format `{error: {code, message, details?}}`, the EVID error code constant registry (17 codes across 5 domains), and the Gate failure details structure. All error codes must be defined as constants -- no magic strings.

## Allowed Files
- `src/shared/constants/error_codes.py`
- `src/shared/constants/error_codes.ts`
- `src/shared/schemas/error_response.py`
- `src/shared/types/error_response.ts`
- `tests/unit/contracts/test_error_codes.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: Error response schema: `{error: {code: string, message: string, details?: object}}`
- [ ] AC-2: 17 EVID error codes defined as constants (EVID_1001 through EVID_5003)
- [ ] AC-3: Each error code maps to correct HTTP status (400/404/409/422/500/503/504)
- [ ] AC-4: Error code prefix domains: 1xxx=project, 2xxx=workflow, 3xxx=agent, 4xxx=artifact, 5xxx=system
- [ ] AC-5: EVID_1001 validates description < 10 chars with message "Description too short (min 10 chars)"
- [ ] AC-6: EVID_2001 gate failure details structure includes failed_checks[] and passed_checks[]
- [ ] AC-7: Gate failure does not short-circuit -- all checks reported (documented in code)
- [ ] AC-8: No error code string literals outside the constants module (enforced by test grep)

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_011.py -v
mypy src/shared/constants/error_codes.py src/shared/schemas/error_response.py --strict
npx tsc --noEmit src/shared/constants/error_codes.ts src/shared/types/error_response.ts
```

## Completion Definition
All 17 error codes defined with HTTP status, message template, and domain prefix. Error response schema defined in both languages. Gate failure details structure implemented. Tests verify completeness, HTTP mappings, and no magic strings.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_011.py | test_error_response_schema |
| AC-2 | tests/unit/contracts/test_spec_a_011.py | test_exactly_17_error_codes |
| AC-3 | tests/unit/contracts/test_spec_a_011.py | test_error_code_http_status_mapping |
| AC-4 | tests/unit/contracts/test_spec_a_011.py | test_error_code_domain_prefixes |
| AC-5 | tests/unit/contracts/test_spec_a_011.py | test_evid_1001_message |
| AC-6 | tests/unit/contracts/test_spec_a_011.py | test_gate_failure_details_structure |
| AC-7 | tests/unit/contracts/test_spec_a_011.py | test_gate_no_short_circuit_documented |
| AC-8 | tests/unit/contracts/test_spec_a_011.py | test_no_magic_error_strings |
