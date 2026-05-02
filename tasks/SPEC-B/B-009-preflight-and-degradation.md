# [SPEC-B-009] Pre-flight 检查与服务降级

## Metadata
- **task_id**: SPEC-B-009
- **spec_ref**: SPEC-1.3, SPEC-14.1, SPEC-14.2
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL system_status 表, SPEC-1A GET /api/system/status), [SPEC-B-001]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 API 启动时的全量 Pre-flight 检查，写入 `system_status` 表（24h 有效）。检查项分为关键项（LLM/LLM_REVIEW/TTS/SQLite/媒体目录，任一失败阻断创建项目）和可降级项（Web 搜索/素材/BGM/financial_data，失败时黄色 Banner + 功能降级）。新建项目时跑关键项子集。实现 `GET /api/system/status` 接口。

## Allowed Files
- `src/backend/core/preflight.py`
- `src/backend/core/health_checks/*.py`
- `src/backend/db/models/system_status.py`
- `src/backend/db/repositories/system_status_repo.py`
- `src/backend/api/routes/system.py`
- `src/backend/api/middleware/startup.py`
- `tests/unit/infra/test_preflight.py`

## Forbidden Files
- `src/frontend/**` (Banner UI owned by SPEC-E)
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 5 个关键项（llm/llm_review/tts/sqlite/media_dir）均在 `system_status` 表
- [ ] AC-2: 任一关键项 failed → `all_critical_ok=false`，新建项目接口返回 403
- [ ] AC-3: 可降级项（web_search/material/bgm/financial_data）failed → `degraded_services[]` 包含对应 check_name
- [ ] AC-4: 可降级项失败时新建项目仍可创建
- [ ] AC-5: `system_status` 记录 `valid_until` = 创建时间 + 24h
- [ ] AC-6: API 启动时自动跑全量 Pre-flight
- [ ] AC-7: 新建项目时跑关键项子集检查

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_009.py -v
sqlite3 data/db/app.sqlite3 ".schema system_status"
curl http://localhost:8000/api/system/status | python -m json.tool
```

## Completion Definition
Pre-flight 检查在 API 启动和项目创建时正确执行，关键项失败阻断创建，可降级项失败仅降级，system_status API 返回正确状态。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_009.py | test_critical_checks_in_system_status |
| AC-2 | tests/unit/infra/test_spec_b_009.py | test_critical_failure_blocks_project_creation |
| AC-3 | tests/unit/infra/test_spec_b_009.py | test_degraded_services_listed |
| AC-4 | tests/unit/infra/test_spec_b_009.py | test_degraded_does_not_block_creation |
| AC-5 | tests/unit/infra/test_spec_b_009.py | test_valid_until_24h |
| AC-6 | tests/unit/infra/test_spec_b_009.py | test_full_preflight_on_startup |
| AC-7 | tests/unit/infra/test_spec_b_009.py | test_critical_subset_on_project_create |
