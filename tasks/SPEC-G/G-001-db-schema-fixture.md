# [SPEC-G-001] BDD 测试数据库 Schema 迁移 Fixture

## Metadata
- **task_id**: SPEC-G-001
- **spec_ref**: SPEC-G1.1
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S
- **TDD 起点**: @gatekeeper / @observability / @performance 的 .feature scenario 当前 FAIL（视为 RED）→ 补齐 fixture 使相关 step 能访问完整 schema → scenario PASS（GREEN）

## Scope
在 `tests/integration/bdd/conftest.py` 中添加 `bdd_db_conn` fixture，在 `:memory:` SQLite 数据库上按顺序运行所有 schema migration 脚本，使 GateKeeper/Observability/Performance 等 BDD 场景不再因 `no such table: phases` 等错误而失败。

**迁移脚本路径（两个目录，按 V001 → V005 顺序执行）**:
1. `src/backend/db/migrations/001_initial.sql` — 核心表 DDL
2. `migrations/V002__create_claim_tables.sql` — `claim_registry`
3. `migrations/V003__create_stage_preferences.sql` — `stage_preferences`
4. `migrations/V004__add_latest_reached_phase.sql` — `latest_reached_phase`
5. `migrations/V005__extend_task_ledger_types.sql` — `task_ledger` 类型扩展

G-001 fixture 若只跑第一个目录，则 `claim_registry`、`stage_preferences`、`latest_reached_phase`、`task_ledger.target_version` 等字段都缺失。

## Allowed Files
- `tests/integration/bdd/conftest.py`
- `tests/integration/bdd/steps/common_steps.py`
- `tests/integration/bdd/steps/observability_steps.py`
- `tests/integration/bdd/steps/performance_steps.py`
- `tests/integration/bdd/steps/gatekeeper_steps.py`

## Read-Only (必要时可读但不修改)
- `src/backend/db/migrations/` — 读取 SQL 路径常量
- `migrations/` — 读取 V002..V005
- `src/backend/db/` — 确认 schema 与运行时连接 PRAGMA 一致（如 `foreign_keys`、`journal_mode`）

## Forbidden Files
- `src/backend/**` (除上述 Read-Only 外不修改 SUT)
- `src/frontend/**`
- `docs/specs/**`
- `HARNESS.md`
- `CLAUDE.md`

## Acceptance Criteria
- [ ] AC-1: `bdd_db_conn` fixture 在 `:memory:` 数据库上运行全部 5 个迁移脚本（V001..V005），返回可用连接
- [ ] AC-2: `_run_gatekeeper()` 使用 fixture 提供的连接而非自行创建 `sqlite3.connect(":memory:")`
- [ ] AC-3: 6 个 @gatekeeper 场景全部从 FAIL→PASS（`no such table: phases` 类错误消失）
- [ ] AC-4: @observability 的"成本记录失败只告警不阻塞门禁"场景通过
- [ ] AC-5: @performance 的"用户关闭浏览器后长任务仍应恢复可见"因 `async_tasks` 表存在而不再因 table missing 失败
- [ ] AC-6: `verify_no_skip_stubs.py` exit 0（无新 stub）

## Verification Commands
```bash
pytest tests/integration/bdd/features/gatekeeper.feature -v
pytest tests/integration/bdd/features/observability.feature -v
pytest tests/integration/bdd/features/performance.feature -v
ruff check tests/integration/bdd/conftest.py tests/integration/bdd/steps/
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`bdd_db_conn` fixture 存在且被所有需要 DB 的 step definitions 使用。6 个 gatekeeper + 1 个 observability + 1 个 performance（共 8 个）场景因正确 schema 而不再因 table missing 失败。其他失败原因（如 SUT API gap）不在本 task 范围内。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/integration/bdd/conftest.py | `bdd_db_conn` fixture |
| AC-3 | tests/integration/bdd/features/gatekeeper.feature | 6 scenarios under @gatekeeper |
| AC-4 | tests/integration/bdd/features/observability.feature | 成本记录失败只告警不阻塞门禁 |
| AC-5 | tests/integration/bdd/features/performance.feature | 用户关闭浏览器后长任务仍应恢复可见 |
