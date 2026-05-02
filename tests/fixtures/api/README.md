# API Fixtures (Single Source of Truth)

Every fixture lives here. MSW handlers (`src/frontend/mocks/handlers.ts`) read these. Backend tests that need API request/response examples also read these. Validated against Pydantic models in `src/shared/schemas/` via `scripts/validate_fixtures.py`.

## Layout

```
tests/fixtures/api/
├── projects/
│   ├── _index.json         # filename -> {schema: "<module>.<ClassName>"}
│   ├── list_response.json
│   └── detail_p3.json
└── events/
    ├── _index.json
    └── phase_advance.json
```

## Rules
1. Every fixture MUST be registered in its group's `_index.json` mapping to a Pydantic model under `src/shared/schemas/`.
2. CI runs `python scripts/validate_fixtures.py`; mismatches block the PR.
3. Do not duplicate fixtures across groups. If two surfaces need the same payload, one file + import.
