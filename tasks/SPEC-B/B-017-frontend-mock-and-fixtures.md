# [SPEC-B-017] Frontend Mock Layer + Fixture Single Source

## Metadata
- **task_id**: SPEC-B-017
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.2, §6.1
- **depends_on**: [SPEC-A-001, SPEC-A-002, SPEC-A-006, SPEC-A-010]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Build the MSW-based mock layer for the frontend. All API and WebSocket mock data lives as JSON files under `tests/fixtures/api/` (single source). MSW handlers read those fixtures. A CI script validates every fixture against the corresponding Pydantic model in `src/shared/schemas/` (via emitted JSON Schema). Both vitest (jsdom) and Playwright (browser) consume the same handler set.

## Allowed Files
- `src/frontend/mocks/**`
- `tests/fixtures/api/**`
- `scripts/validate_fixtures.py`
- `scripts/emit_json_schemas.py`
- `prototype/**` (new dir; read-only after T5 lands it)
- `prototype/README.md`
- `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`
- `src/frontend/package.json`, `src/frontend/vite.config.ts`
- `tests/unit/infra/test_validate_fixtures.py`
- `tests/unit/frontend/mocks/handlers.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/schemas/**` (read-only)
- `src/shared/types/**` (read-only)
- `HARNESS.md` (Task 4 handles this separately under red-light)

## Acceptance Criteria
- [ ] AC-1: MSW handlers intercept all `/api/v1/*` requests in vitest and Playwright environments.
- [ ] AC-2: Handler bodies are read from `tests/fixtures/api/*.json`; no inline mock data in handlers.
- [ ] AC-3: `python scripts/validate_fixtures.py` validates every fixture against its Pydantic model and exits non-zero on mismatch.
- [ ] AC-4: CI runs the validator and blocks PRs on failure.
- [ ] AC-5: A single `handlers.ts` module is consumed by `mocks/server.ts` (Node, vitest) and `mocks/browser.ts` (browser, Playwright).
- [ ] AC-6: `prototype/` directory exists with the imported source and a README declaring it read-only and exempt from SPEC-X-NNN flow with `[PROTO]` commit prefix. (Requires Task 4 HARNESS amendment merged.)

## Verification Commands
```bash
pnpm --filter frontend exec vitest run tests/unit/frontend/mocks/handlers.test.ts
python scripts/validate_fixtures.py
pytest tests/unit/infra/test_validate_fixtures.py -v
test -f prototype/README.md
```

## Completion Definition
MSW + fixture pipeline is end-to-end working, schema-validated, and consumable by both test runners. Prototype directory is in place under explicit exemption.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/mocks/handlers.test.ts | `intercepts /api/v1/projects` |
| AC-2 | tests/unit/frontend/mocks/handlers.test.ts | `loads body from fixture file` |
| AC-3 | tests/unit/infra/test_validate_fixtures.py | `test_invalid_fixture_fails`, `test_valid_fixtures_pass` |
| AC-5 | tests/unit/frontend/mocks/handlers.test.ts | `server and browser share handlers` |
