# SPEC A/B/C 本地验收与修复交接文档

> 用途：提交给研发 AI / Developer Agent，按本文件修复 `AI-Video-System` 已提交的 SPEC A/B/C 质量问题。  
> 详细审查报告：`.verify/spec_abc_quality_review_2026-04-25.md`  
> 当前放行结论：**不放行**。必须完成下列 P0/P1 修复并通过验收命令后，才能重新评估 SPEC A/B/C 是否满足 PRD 与 TECH_PLAN。

---

## 0. 研发 AI 执行约束

### 0.1 范围

本轮只修复 SPEC A/B/C 放行阻塞项：

- SPEC-A：契约、接口、固定用户认证模型、任务卡可验证性。
- SPEC-B：基础设施、CI、部署、mock/fixture、持久化写路径、任务卡与测试门禁。
- SPEC-C：后端核心引擎、WorkflowEngine/TaskLedger 边界、canonical 验收测试、静态质量。

不主动修 SPEC-D/E/F 功能，除非它们阻断 SPEC-B CI/部署验收，例如 frontend `tsc` 失败。

### 0.2 红线

- 不修改 `AGENTS.md`、`CLAUDE.md`、`openclaw.json`。
- 不做生产环境操作。
- 不删除需求文档、技术方案、历史 SPEC。
- 不用“跳过测试 / 降低测试标准 / 缩小验收范围”伪装通过。
- 所有“已完成”任务不得保留 `pytest.skip("NOT IMPLEMENTED ...")` 作为 canonical 验收。

### 0.3 完成标准

必须满足：

1. 本文所有 P0 项修复完成。
2. P1 项至少完成到不阻断 CI / A/B/C 验收。
3. `pytest tests/unit/ tests/contract/` 能完整收集并运行。
4. SPEC A/B/C canonical 测试无失败，且无 `NOT IMPLEMENTED` skip。
5. CI/部署基础命令可复现。
6. 最终回复必须列出修改文件、命令结果、残余风险。

---

## 1. 总体修复目标

把当前状态从：

- SPEC-A：`252 passed, 1 failed`
- SPEC-B：`1 failed, 138 passed, 27 skipped`
- SPEC-C：`80 passed, 133 skipped`
- 全量 unit/contract 收集失败
- Docker/CI/dev env 不可运行
- ruff/mypy/frontend tsc 失败

修到：

- SPEC-A canonical tests 全绿。
- SPEC-B canonical tests 全绿，且不再用未实现 skip 掩盖已完成任务。
- SPEC-C canonical tests 全绿，所有已完成任务有真实断言。
- 全量 unit/contract 可收集、可运行、可作为 CI 门禁。
- `docker compose config --quiet`、dev env、CI workflow 不再因缺文件/缺入口失败。

---

## 2. P0 必修项

### P0-1：修复 pytest 全量收集失败

#### 问题

命令：

```bash
.venv/bin/python -m pytest tests/unit/contracts tests/unit/infra tests/unit/backend-core tests/contract -q
```

当前失败：

```text
import file mismatch:
imported module 'test_task_types' ... tests/unit/contracts/test_task_types.py
which is not the same as ... tests/unit/backend-core/test_task_types.py
```

#### 要求

- 消除 `tests/unit/contracts/test_task_types.py` 与 `tests/unit/backend-core/test_task_types.py` 同名模块冲突。
- 不删除测试覆盖；如重命名文件，更新所有引用。
- `pytest tests/unit/ tests/contract/` 必须能完整收集。

#### 验收

```bash
.venv/bin/python -m pytest tests/unit/contracts/test_task_types.py -q
.venv/bin/python -m pytest tests/unit/backend-core/test_task_types.py -q
.venv/bin/python -m pytest tests/unit/contracts tests/unit/infra tests/unit/backend-core tests/contract -q
```

---

### P0-2：修复 SPEC-B runtime / CI / dev env 基础不可运行

#### 问题

当前发现：

- `docker compose config --quiet` 因 `.env` 缺失失败。
- `docker-compose.yml` / `docker-compose.dev.yml` / `src/backend/Dockerfile` 均指向 `src.backend.api.main:app`，但 `src/backend/api/main.py` 不存在。
- `.github/workflows/ci.yml` 和 `.github/workflows/nightly_e2e.yml` 使用 `requirements.txt`，但仓库没有该文件。
- `nightly_e2e.yml` 中 B-018 AC-5 实现不对：任务要求“三次连续 nightly 失败后开 issue”，当前是任意一次失败即开 issue，且 `.nightly_failure.txt` 未生成。

#### 要求

1. 提供可导入的 FastAPI 入口：
   - `src/backend/api/main.py`
   - 暴露 `app`
   - 至少包含 `/health`，返回可被 workflow 检查的健康结果。
   - 注册已有 routers 时不能破坏现有测试。
2. 修复依赖文件策略：
   - 要么补 `requirements.txt`，要么修改 workflow / compose 使用现有 `requirements-dev.txt` 或 `pyproject` 安装方式。
   - CI、Docker、dev compose 三者必须一致。
3. 修复 compose 的 `.env` 策略：
   - `docker compose config --quiet` 在 fresh clone 语境下不应因缺 `.env` 直接失败；可使用 `env_file` optional 策略、默认环境变量、或初始化脚本方案。
   - `.env.example` 仍保留，`.env` 不入库。
4. 修复 nightly e2e：
   - 生成失败 issue 所需内容文件。
   - 实现或明确可验证“三次连续失败”逻辑，不能一次失败即开 issue。

#### 验收

```bash
docker compose config --quiet
.venv/bin/python - <<'PY'
from src.backend.api.main import app
print(app.title)
PY
rg -n "requirements.txt|requirements-dev.txt|pyproject" .github/workflows docker-compose*.yml src/backend/Dockerfile
```

可选运行验收（本地资源允许时）：

```bash
make dev
sleep 5
curl -sf http://localhost:8000/health
curl -sf http://localhost:3000/
make seed
make e2e
```

---

### P0-3：修复 SPEC-A-009 固定用户常量回归

#### 问题

命令：

```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q
```

当前结果：

```text
252 passed, 1 failed
```

失败点：

```text
src/backend/services/preference_service.py:121
get_effective_preferences(self, project_id: str, user_id: str = "default")
```

违反 SPEC-A-009：`user_id="default"` 必须集中定义为 `DEFAULT_USER_ID`，不允许散写字符串。

#### 要求

- 从 `src.shared.constants.auth import DEFAULT_USER_ID` 引用常量。
- 任何与 user_id 语义相关的默认值不得散写 `"default"`。
- 不通过弱化测试或扩大 allowlist 解决。

#### 验收

```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_009.py -q
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q
out=$(rg '"default"' src/ --type py | grep -v 'DEFAULT_USER_ID' | grep -i user || true); test -z "$out"
```

---

### P0-4：修复 SPEC-B-002 / SPEC-C-001 写入边界破坏

#### 问题

当前直接 SQL 写入绕过 repository / WorkflowEngine：

- `src/backend/agents/subtask_agents.py:64`
  - `UPDATE task_ledger SET result_ref = ? WHERE id = ?`
- `src/backend/services/financial_data_service.py:57`
  - `DELETE FROM financial_data_cache ...`
- `src/backend/services/preference_service.py`
  - 多处直接 `UPDATE preferences` / `INSERT INTO preference_snapshots` / `DELETE FROM preference_snapshots` / `INSERT INTO events`

这同时导致：

- SPEC-B-002 repository 集中写入测试失败。
- SPEC-C-001 WorkflowEngine 独占 `task_ledger` 写入测试失败。

#### 要求

1. `task_ledger` 写入只能通过 WorkflowEngine 或其授权 repository。
2. DB 写入必须集中到 `src/backend/db/repositories/**` 或明确的 `src/backend/repositories/**` 体系。
3. `PreferenceService`、`FinancialDataService`、`SubTaskAgent` 不应直接拼 SQL 写业务表。
4. 不通过修改测试白名单绕过架构约束，除非确实有新的 repository 路径且测试同步反映真实架构。

#### 建议文件方向

可新增或扩展：

- `src/backend/db/repositories/task_ledger_repository.py`
- `src/backend/db/repositories/preferences_repo.py`
- `src/backend/db/repositories/financial_data_cache_repo.py`
- `src/backend/db/repositories/event_repo.py`

也可复用已有 repository，但必须保持职责清晰。

#### 验收

```bash
.venv/bin/python -m pytest tests/unit/infra/test_spec_b_002.py -q
.venv/bin/python -m pytest tests/unit/backend-core/test_workflow_engine.py::TestAC1AllStateChangesThroughEngine::test_state_change_only_via_engine -q
.venv/bin/python -m pytest tests/unit/infra/test_spec_b_*.py tests/unit/infra/test_validate_fixtures.py tests/unit/infra/test_seed_dev_db.py -q
```

---

### P0-5：替换 SPEC-C canonical `NOT IMPLEMENTED` skip

#### 问题

命令：

```bash
.venv/bin/python -m pytest tests/unit/backend-core/test_spec_c_*.py -q
```

当前结果：

```text
80 passed, 133 skipped
```

这些 skipped 文件与 `PROGRESS.md` 的“SPEC-C 已完成”状态冲突。

#### 要求

- 对所有已标记 DONE 的 SPEC-C 任务，canonical `test_spec_c_*.py` 必须是真实断言。
- 不允许保留 `pytest.skip("NOT IMPLEMENTED -- waiting for [SPEC-C-xxx]")`。
- 若存在同功能测试在非 canonical 文件中，迁移或 re-export 到 canonical 文件，并确保不会造成 pytest 收集冲突。
- `verify_no_skip_stubs.py` 必须覆盖所有 A/B/C canonical test 文件，而不是只覆盖部分旧列表。

#### 必查列表

当前含 `NOT IMPLEMENTED` skip 的 SPEC-C 文件：

- C-001, C-002, C-003, C-004, C-005, C-006
- C-009, C-010, C-011
- C-015, C-016, C-017, C-019, C-020, C-021, C-022
- C-100, C-101

#### 验收

```bash
rg -n 'pytest\.skip\("NOT IMPLEMENTED' tests/unit/backend-core/test_spec_c_*.py
# 上一条命令应无输出
.venv/bin/python -m pytest tests/unit/backend-core/test_spec_c_*.py -q
.venv/bin/python scripts/contracts/verify_no_skip_stubs.py
```

---

## 3. P1 必修项

### P1-1：修复 SPEC-B-017 mock / fixture 验收失败

#### 问题

命令：

```bash
pnpm --filter frontend test
```

当前失败：

```text
FAIL tests/unit/frontend/mocks/handlers.test.ts
expected undefined to be 'proj_001'
```

原因：handler 的 `/api/v1/projects` 返回数组，但测试期望对象字段 `project_id`。

另有多处 MSW warning：未处理 `ws://localhost:8000/ws/...`。

#### 要求

- 明确 `/api/v1/projects` 契约：列表接口返回数组，还是测试应该请求详情接口。
- 修 handler 或测试，保持与 SPEC-A API route schema / fixtures 一致。
- 覆盖 WebSocket mock，至少不在测试中产生未处理 WS 请求警告。
- 不把测试改成弱断言。

#### 验收

```bash
pnpm --filter frontend test -- tests/unit/frontend/mocks/handlers.test.ts
pnpm --filter frontend test
```

---

### P1-2：修复任务卡与验收门禁覆盖

#### 问题

当前：

```bash
.venv/bin/python scripts/lint_task_cards.py --only SPEC-A
# 35 cards, 10 findings: A-107..A-115 缺 Verification Commands

.venv/bin/python scripts/lint_task_cards.py --only SPEC-B
# B-017/B-018 缺 canonical tests/unit/infra/test_spec_b_017.py / test_spec_b_018.py
```

#### 要求

- A-107..A-115 补齐 `Verification Commands` 和可复现 Test Mapping。
- B-017/B-018 补 canonical 测试文件，或更新 lint 规则与任务卡，让验收入口一致且可复现。
- `verify_no_skip_stubs.py` 覆盖 A/B/C 全部 canonical 文件。

#### 验收

```bash
.venv/bin/python scripts/lint_task_cards.py --only SPEC-A
.venv/bin/python scripts/lint_task_cards.py --only SPEC-B
.venv/bin/python scripts/lint_task_cards.py --only SPEC-C
.venv/bin/python scripts/contracts/verify_no_skip_stubs.py
```

---

### P1-3：修复静态质量门禁

#### 问题

当前：

- `ruff` 在 A/B/C 相关路径发现 48 个问题。
- `mypy --strict` 在 A/B/C 相关源文件发现 43 个错误。
- `pnpm --filter frontend tsc` 失败，会阻断 SPEC-B CI frontend job。

#### 要求

- 修复 ruff，不用大面积 ignore 掩盖。
- 修复 mypy strict，必要时补明确类型、cast、TypedDict、Literal 校验。
- 修复 frontend tsc：如错误来自 SPEC-F 文件，也要处理到 CI 不被阻断；可补依赖、路径 alias 或调整 tsconfig，但不能降低核心类型检查标准。

#### 验收

```bash
.venv/bin/python -m ruff check src tests/unit/contracts tests/unit/infra tests/unit/backend-core scripts
.venv/bin/python -m mypy --explicit-package-bases src/shared src/backend scripts --strict
pnpm --filter frontend tsc
```

---

## 4. 最终全量验收命令

研发 AI 修复完后必须在仓库根目录执行：

```bash
# 1. 工作区状态
git status --short --branch

# 2. SPEC-A
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_*.py -q
.venv/bin/python scripts/contracts/check_schema_alignment.py chart_material audio_master sfx_layout_plan sfx_mix_segments material_manifest shot_material_bindings api_master_audio
.venv/bin/python -m pytest tests/contract/test_frontend_types_match_schemas.py -q

# 3. SPEC-B
.venv/bin/python -m pytest tests/unit/infra/test_spec_b_*.py tests/unit/infra/test_validate_fixtures.py tests/unit/infra/test_seed_dev_db.py -q
.venv/bin/python scripts/validate_fixtures.py
docker compose config --quiet

# 4. SPEC-C
.venv/bin/python -m pytest tests/unit/backend-core/test_spec_c_*.py -q
.venv/bin/python -m pytest tests/unit/backend-core/test_workflow_engine.py -q
.venv/bin/python tests/eval/eval_router.py --report

# 5. 全量 unit / contract
.venv/bin/python -m pytest tests/unit/ tests/contract/ -q

# 6. no-skip / task-card lint
.venv/bin/python scripts/contracts/verify_no_skip_stubs.py
.venv/bin/python scripts/lint_task_cards.py --only SPEC-A
.venv/bin/python scripts/lint_task_cards.py --only SPEC-B
.venv/bin/python scripts/lint_task_cards.py --only SPEC-C

# 7. frontend
pnpm --filter frontend test
pnpm --filter frontend tsc

# 8. static quality
.venv/bin/python -m ruff check src tests/unit/contracts tests/unit/infra tests/unit/backend-core scripts
.venv/bin/python -m mypy --explicit-package-bases src/shared src/backend scripts --strict
```

本地资源允许时，再执行 runtime 验收：

```bash
make dev
sleep 5
curl -sf http://localhost:8000/health
curl -sf http://localhost:3000/
make seed
make e2e
```

---

## 5. 修复完成后的交付格式

研发 AI 最终回复必须包含：

```text
Summary:
- 修复了哪些 P0/P1 项
- 关键文件改动列表

Validation:
- 每条验收命令的实际结果
- 失败/跳过数量必须如实写出

Risk:
- 仍未解决的问题
- 与 SPEC-D/E/F 的非本轮阻塞关系

Next:
- 如仍有后续工作，列出明确任务；不得把 P0/P1 阻塞包装为已完成
```

---

## 6. 当前证据快照

来自 2026-04-25 审查：

```text
SPEC-A: 252 passed, 1 failed
SPEC-B: 1 failed, 138 passed, 27 skipped
SPEC-C canonical: 80 passed, 133 skipped
backend-core full: 1 failed, 251 passed, 133 skipped
frontend test: 1 failed, 60 passed
frontend tsc: failed
ruff: 48 errors on A/B/C-related scan
mypy strict: 43 errors on A/B/C-related source scan
docker compose config: failed due missing .env
api entrypoint: src/backend/api/main.py missing
requirements.txt: missing
```
