# [SPEC-A-009] V1 Authentication Model (Single-User)

## Metadata
- **task_id**: SPEC-A-009
- **spec_ref**: SPEC-1C
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Implement the V1 single-user authentication model: no auth middleware, fixed user_id constant, auto-creation of default user data directory. The key deliverable is a centralized `DEFAULT_USER_ID` constant that all code references instead of hardcoded "default" strings, plus the startup logic to ensure `data/users/default/` exists.

## Allowed Files
- `src/shared/constants/auth.py`
- `src/shared/constants/auth.ts`
- `src/backend/startup/ensure_user_dir.py`
- `tests/unit/contracts/test_auth_model.py`

## Forbidden Files
- `src/backend/api/middleware/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `DEFAULT_USER_ID` constant equals "default" in both Python and TypeScript
- [ ] AC-2: No hardcoded string "default" for user_id anywhere outside the constant definition (grep-verifiable)
- [ ] AC-3: Startup function creates `data/users/default/` if it does not exist
- [ ] AC-4: Startup function creates `data/users/default/brand_kit.json` template if missing
- [ ] AC-5: No 401 or 403 HTTP status codes defined in error code constants
- [ ] AC-6: Code comments document V1.5 upgrade path: users table + session token + middleware

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_009.py -v
# Grep for hardcoded "default" user_id (negative check: no matches = pass).
# Uses [ -z ] to assert empty output, since `grep` exits 1 on zero matches
# and a bare pipeline would propagate that as a false-positive failure.
out=$(rg '"default"' src/ --type py | grep -v 'DEFAULT_USER_ID' | grep -i user); [ -z "$out" ]
```

## Completion Definition
DEFAULT_USER_ID constant defined centrally. Startup creates user directory. No hardcoded user_id strings. V1.5 upgrade path documented. Tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_009.py | test_default_user_id_value |
| AC-2 | tests/unit/contracts/test_spec_a_009.py | test_no_hardcoded_default_user_id |
| AC-3 | tests/unit/contracts/test_spec_a_009.py | test_ensure_user_dir_creates_directory |
| AC-4 | tests/unit/contracts/test_spec_a_009.py | test_ensure_user_dir_creates_brand_kit_template |
| AC-5 | tests/unit/contracts/test_spec_a_009.py | test_no_401_403_error_codes |
| AC-6 | tests/unit/contracts/test_spec_a_009.py | test_v15_upgrade_path_documented |
