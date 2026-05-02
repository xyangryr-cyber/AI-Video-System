# [SPEC-A-006] REST API Route Definitions (25 Endpoints)

## Metadata
- **task_id**: SPEC-A-006
- **spec_ref**: SPEC-1A
- **depends_on**: [SPEC-A-001, SPEC-A-002, SPEC-A-003]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Define the authoritative API route registry containing all 25 REST endpoints from SPEC-1A. This is the contract layer only -- route paths, methods, request/response schemas, and caller annotations. No handler implementation. Includes request/response Pydantic models for each endpoint and a route registry constant that downstream code can import.

## Allowed Files
- `src/shared/contracts/api_routes.py`
- `src/shared/contracts/api_routes.ts`
- `src/shared/schemas/api_requests.py`
- `src/shared/schemas/api_responses.py`
- `src/shared/types/api_requests.ts`
- `src/shared/types/api_responses.ts`
- `tests/unit/contracts/test_api_routes.py`

## Forbidden Files
- `src/backend/api/routes/**`
- `src/backend/api/handlers/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: Route registry defines exactly 25 REST endpoints (excluding WS) with method, path, description
- [ ] AC-2: Each route entry specifies request_schema and response_schema references
- [ ] AC-3: POST /api/projects request validates description ≥ 10 chars
- [ ] AC-4: POST /api/projects/{id}/advance request includes optional confirmed_preferences
- [ ] AC-5: POST /api/projects/{id}/skip is constrained to phase P5/P6 only (documented in route metadata)
- [ ] AC-6: GET /api/projects/{id}/events supports query params limit (default 50) and before (cursor)
- [ ] AC-7: GET /api/settings/preferences/snapshots supports query param limit (default 20)
- [ ] AC-8: WS endpoint `/ws/{project_id}` documented in registry as type='websocket'
- [ ] AC-9: All POST/PUT/DELETE routes annotated with error_response_schema referencing SPEC-13A format
- [ ] AC-10: Route registry exported as both Python dict and TypeScript const for cross-language consumption

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_006.py -v
mypy src/shared/contracts/api_routes.py src/shared/schemas/api_requests.py src/shared/schemas/api_responses.py --strict
npx tsc --noEmit src/shared/contracts/api_routes.ts
```

## Completion Definition
Route registry contains all 25+1(WS) endpoints. Request/response schemas defined for every endpoint. Tests verify completeness (no missing endpoints), constraint annotations, and schema validity.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_006.py | test_exactly_25_rest_endpoints |
| AC-2 | tests/unit/contracts/test_spec_a_006.py | test_all_routes_have_schemas |
| AC-3 | tests/unit/contracts/test_spec_a_006.py | test_create_project_min_description |
| AC-4 | tests/unit/contracts/test_spec_a_006.py | test_advance_request_schema |
| AC-5 | tests/unit/contracts/test_spec_a_006.py | test_skip_phase_constraint |
| AC-6 | tests/unit/contracts/test_spec_a_006.py | test_events_pagination_params |
| AC-7 | tests/unit/contracts/test_spec_a_006.py | test_snapshots_pagination_params |
| AC-8 | tests/unit/contracts/test_spec_a_006.py | test_ws_endpoint_in_registry |
| AC-9 | tests/unit/contracts/test_spec_a_006.py | test_mutating_routes_have_error_schema |
| AC-10 | tests/unit/contracts/test_spec_a_006.py | test_route_registry_export_formats |
