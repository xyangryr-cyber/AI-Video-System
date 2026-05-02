# AI-Video-System Development Progress Log

> **Archive notices**:
>
> - `PROGRESS.md.full.backup.2026-04-27.md` — full 733-line history up to 2026-04-27 (SMOKE-FIX chain complete).
> - `PROGRESS.md.full.backup.2026-04-25.md` — full 1668-line history up to 2026-04-25 (30+ DONE narrative blocks).
> - `PROGRESS.md.full.backup.2026-04-20.md` — pre-2026-04-20 history (1998 lines, 30 task entries).
> - Long Decisions/Verification/Artifacts belong in commit bodies per HARNESS §9.1.

---

## Status snapshot (2026-05-02)

| Phase                   | Tasks     | Status                                                                                         |
| ----------------------- | --------- | ---------------------------------------------------------------------------------------------- |
| Phase 1 (Setup)         | T001-T002 | DONE                                                                                           |
| Phase 2 (Foundational)  | T003-T006 | DONE                                                                                           |
| Phase 3 (US1)           | T007-T015 | DONE                                                                                           |
| Phase 4 (US2)           | T016-T020 | DONE                                                                                           |
| Phase 5 (US3)           | T021-T023 | DONE                                                                                           |
| Phase 6 (US4)           | T024-T029 | DONE                                                                                           |
| Phase 7 (Cross-Cutting) | T030-T032 | DONE                                                                                           |
| Phase 8 (E2E)           | T033-T037 | PENDING (needs frontend dev server)                                                            |
| Phase 9 (Polish)        | T038-T042 | T038 PENDING, T039 DONE (61/63 pass, 2 pre-existing fails), T040 PENDING, T041 DONE, T042 DONE |

### Test Status

- **Frontend vitest**: 61/63 files pass (486/498 tests). 2 pre-existing failures: PhasePreviewRouter (11), visual test "目标受众时长" (1).
- **Python unit**: Blocked by Python 3.9 `Type | None` syntax in deepeval (pre-existing env issue).
- **Integration/Contract**: Tests written but need backend running with LLM to execute.

## Status snapshot (2026-04-27) — ARCHIVED

| SPEC                    | Done (distinct task IDs)              | Notes                                                                                |
| ----------------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| A -- Contracts          | A-001..A-018, A-100..A-115 (34)       | 485 passed, 0 skipped                                                                |
| B -- Infra              | B-001..B-018, B-100 (19)              | 168 passed, 0 skipped, 0 failed                                                      |
| C -- Backend Core       | C-001..C-022, C-100..C-106 (29)       | 28 DONE + 1 POC (C-106)                                                              |
| D -- Pipeline           | D-001..D-022, D-100..D-103 (26)       | 294 passed, 0 skipped                                                                |
| E -- Frontend           | E-001..E-015, E-100..E-105, E-WAVE-3A | 67 passed (vitest + pytest)                                                          |
| F -- Media Render       | F-001..F-014, F-100..F-102 (17)       | 205 passed, 0 skipped                                                                |
| G -- BDD Acceptance     | 18 of 18                              | All 18 BDD scenarios DONE                                                            |
| TTS -- Provider         | ByteDanceTTSProvider DONE             | Real HTTP provider; access token pending admin grant                                 |
| GAPFIX (Phase 1-3)      | GAPFIX-034..044 + SMOKE-FIX-001..003  | Phase 1-3 DONE                                                                       |
| **SMOKE-FIX (round 6)** | **SMOKE-FIX-004..016 (13 tasks)**     | **All 13 API endpoints real (0x 501), 9/9 preflight checks real, 27 new tests PASS** |
| **Full unit suite**     |                                       | **2137 passed, 1 skipped, 3 failed (known regressions)**                             |

---

## Recent commits (latest first)

| SHA      | Task                   | Title                                                                                                                                  | Date       |
| -------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| pending  | SPEC-D-002 (phase5-9)  | US3 clarification UI (T022-T023), US4 advance tests+impl (T024-T029), cross-cutting tests (T030-T032), remove MOCK_FACTUAL_DATA (T041) | 2026-05-02 |
| pending  | SPEC-D-002 (phase1-4)  | GateP0 fix, CompletenessReviewer re-export, requirements_agent adapter, US1+US2 frontend-backend integration                           | 2026-05-02 |
| 6fb4dded | SPEC-P0-PRD            | restructure PRD v3.3 to 10 parts, lift Phase 0 to Phase0需求.md                                                                        | 2026-04-30 |
| 0e10dd1b | SPEC-D-DOC             | slim TECH_PLAN_v3.3.md to current architecture decisions only                                                                          | 2026-04-30 |
| cb175c1d | SPEC-INIT              | relax SPEC-tag regex to accept multi-segment IDs                                                                                       | 2026-04-30 |
| eacd87a0 | SPEC-INIT              | gitignore runtime artifacts and test reports                                                                                           | 2026-04-30 |
| 3938fdf1 | SPEC-G-E2E             | add Phase 0 + full pipeline browser E2E specs                                                                                          | 2026-04-30 |
| 0faa4495 | SPEC-P-DOC             | add SPEC-P0 task cards + Phase 0 requirements/test docs                                                                                | 2026-04-30 |
| 81263b8c | SPEC-E-UI              | adapt phase previews to artifact_data API shape                                                                                        | 2026-04-30 |
| 62b2b3ba | SPEC-P-M4              | route substantive utterances to refine_requirements                                                                                    | 2026-04-30 |
| b8e9aede | SPEC-D-002             | make OutlineAgent LLM-only and accept LLM field aliases                                                                                | 2026-04-30 |
| 6cda63a1 | SPEC-E-UI-V2 (round 2) | document backend API requirements for redesigned WorkflowPage                                                                          | 2026-04-30 |
| a43048ee | SPEC-E-UI-V2           | redesign WorkflowPage with new collaborative terminal layout                                                                           | 2026-04-30 |
| 6c2fe07  | SPEC-F-014             | add uniform color frame detection to keyframe render agent                                                                             | 2026-04-29 |
| f78a232  | SPEC-D-005             | write measured TTS duration and propagate to downstream phases                                                                         | 2026-04-29 |
| f113535  | SPEC-D-007             | implement content-driven broll matching                                                                                                | 2026-04-29 |
| 1c891f8  | VIS-002                | fix 4 visual alignment gaps from prototype comparison                                                                                  | 2026-04-28 |
| 2a5b40d  | VIS-001                | enable Tailwind CSS pipeline by adding index.css entry                                                                                 | 2026-04-28 |
| d0f4eb3  | SMOKE-FIX-017          | backfill PROGRESS.md with SMOKE-FIX-004..016 commits                                                                                   | 2026-04-27 |
| 1e3fd01  | SMOKE-FIX-016          | expand smoke test endpoint coverage to all 13 endpoints                                                                                | 2026-04-27 |
| 90a628c  | SMOKE-FIX-015          | replace 5 preflight stubs with real import checks                                                                                      | 2026-04-27 |
| f79a1e2  | SMOKE-FIX-014          | fix write-path separation: confirm_preferences + material_supplement                                                                   | 2026-04-27 |
| 7fe9f4e  | SMOKE-FIX-013          | implement GET /artifact and POST /cancel endpoints                                                                                     | 2026-04-27 |
| 2902847  | SMOKE-FIX-012          | wire POST /chat to IntentRouter                                                                                                        | 2026-04-27 |
| 1c2fe0b  | SMOKE-FIX-011          | wire POST /skip to PhaseOps.skip                                                                                                       | 2026-04-27 |
| d36a9e2  | SMOKE-FIX-010          | wire POST /rollback to PhaseOps.rollback                                                                                               | 2026-04-27 |
| 966086c  | SMOKE-FIX-009          | wire POST /advance to PhaseOps + BaseGate                                                                                              | 2026-04-27 |
| 71a80b5  | SMOKE-FIX-008          | wire preflight startup into FastAPI lifespan                                                                                           | 2026-04-27 |
| 3a283b0  | SMOKE-FIX-007          | implement DELETE /api/projects/{id} soft-delete endpoint                                                                               | 2026-04-27 |
| 4fc58df  | SMOKE-FIX-006          | implement GET /api/projects/{id} endpoint                                                                                              | 2026-04-27 |
| 29ea336  | SMOKE-FIX-005          | complete project creation: INSERT projects + 12 phase rows                                                                             | 2026-04-27 |
| a7137ca  | SMOKE-FIX-004          | add migration runner and wire into API startup lifespan                                                                                | 2026-04-27 |
| 86b53b8  | PROGRESS               | add SMOKE-FIX-001/002/003 entries to recent commits                                                                                    | 2026-04-27 |
| e52aab1  | SMOKE-FIX-003          | stabilize pnpm MSW peer dependency resolution                                                                                          | 2026-04-27 |
| 824c2b7  | SMOKE-FIX-001          | add Vite proxy bypass for frontend api/ source files                                                                                   | 2026-04-27 |
| 6201198  | SMOKE-FIX-002          | implement SQLite connection management and wire get_db                                                                                 | 2026-04-27 |

Full history (pre-2026-04-27 commits + all DONE narrative blocks) lives in the backup files listed above.

---

## Open follow-ups

- **SMOKE-FIX 3 test regressions (2026-04-27)**:
  1. `test_missing_routes.py::test_returns_task_id_on_success` — fixture needs migration runner (no `async_tasks` table)
  2. `test_preferences_confirm.py::test_returns_200_for_valid_request` — fixture needs migration runner (no `preferences` table)
  3. `test_spec_b_002.py::test_all_db_writes_live_under_repositories` — projects.py:98/111/155 contain SQL writes outside repository layer (documented tradeoff, SMOKE-FIX-004 decisions)
- **ByteDance TTS resource grant pending (2026-04-25)**: APP_ID `9061824843` needs `volc.tts.default` grant on ByteDance OpenSpeech console.
- **G-012 eval bucket residual**: `inject_subtask` action needs SPEC-C edit (HARNESS §1.2 forbidden_files). Tracked under SPEC-G-014.
- **Venv baseline (2026-04-25)**: 2017 passed / 2 failed / 1 skipped.
- **Py3.9 `Type \| None` syntax** in `src/backend/startup/ensure_user_dir.py:6` — pre-existing, unrelated to current work.
- **4 pre-existing contract test failures** — see REMAINING-WORK-PLAN.md #4.

---

1. Each `[SPEC-X-NNN]` commit appends exactly one row to the Recent-commits table above. That is the DONE entry.
2. **Put the long story in the commit body** (Files Changed / Verification / Decisions / Artifacts per HARNESS §9.3), not here.
3. Multi-round fix/verify/review cycles: one row per round with a `(round N)` suffix in the Task column.
4. Running total check: if this file exceeds 100 lines again, snapshot-and-prune following the same backup pattern.
