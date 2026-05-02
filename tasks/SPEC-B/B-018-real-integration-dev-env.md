# [SPEC-B-018] Real Integration Dev Environment

## Metadata
- **task_id**: SPEC-B-018
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.4
- **depends_on**: [SPEC-B-001, SPEC-B-002, SPEC-A-006, SPEC-A-007]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Provide a one-command real backend + frontend dev environment for `@e2e-real` Playwright runs and manual integration debugging. Includes seed data covering all phases.

## Allowed Files
- `docker-compose.dev.yml`
- `Makefile`
- `scripts/seed_dev_db.py`
- `tests/unit/infra/test_seed_dev_db.py`
- `.github/workflows/nightly_e2e.yml`

## Forbidden Files
- `infra/prod/**`
- `deploy/prod/**`
- `src/backend/**` (consume only existing service contracts)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `make dev` brings up backend (FastAPI on :8000) and frontend (Vite on :3000) via `docker-compose.dev.yml`.
- [ ] AC-2: `make seed` populates the dev SQLite with ≥12 demo projects covering phases P0..P11.
- [ ] AC-3: `make e2e` runs Playwright tests tagged `@e2e-real` against `http://localhost:3000`.
- [ ] AC-4: `.github/workflows/nightly_e2e.yml` runs the same on a nightly schedule.
- [ ] AC-5: Three consecutive nightly failures auto-open a GitHub issue (workflow step using `peter-evans/create-issue-from-file` or equivalent).

## Verification Commands
```bash
make dev
sleep 5 && curl -s http://localhost:8000/health | grep -q ok
curl -s http://localhost:3000/ | grep -q "<title>"
make seed
sqlite3 data/db/dev.sqlite3 "select count(*) from projects;"   # >= 12
pytest tests/unit/infra/test_seed_dev_db.py -v
```

## Completion Definition
A developer (or CI) can stand up a real, seeded dev environment and run real-backend e2e tests with one command each.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/unit/infra/test_seed_dev_db.py | `test_seeds_twelve_phases` |
| AC-2 | tests/unit/infra/test_seed_dev_db.py | `test_seeds_idempotent` |
