# 历史 Unit Test 失败修复交接文档

> **本文档身份**：交接给另一个 AI（修复 AI）的工作单
> **目的**：在 SPEC-G 启动前，把 23 个**与 SPEC-G 无关**的 unit test 失败清掉，让"无回归"判据能成立
> **创建于**：2026-04-25
> **背景作者**：上游 AI（已和许阳达成"启动 SPEC-G 前先清基线"的决策）
> **优先级**：P1（**不阻塞** SPEC-G-000-pre，但**强烈建议**在 G-000d 之前完成，否则后续无法分辨"我改坏了"和"本来就坏"）

---

## 0. 修复 AI 必读

### 0.1 本任务的边界
- **范围**：仅修这 23 个 unit test FAILED（部分版本基线下的）。不动 BDD test。不动集成 test。
- **不在范围**：17 个 collection-error 文件——这些由"修 venv + 加 huey/numpy 到 requirements"另一个交接处理，**不要**在本任务里碰
- **不动 SPEC**：所有 `docs/specs/SPEC-*.md` 是 read-only。如果发现某个失败的根因是 SPEC 文档要更新，**写入交接反馈**给许阳，不要自改 SPEC

### 0.2 必读
1. 本文档全文
2. `HARNESS.md` §4 TDD、§9 PROGRESS、§13 cross-cutting rules
3. `AGENTS.md` § Troubleshooting Discipline（**铁律**）
4. `~/.claude/projects/-Users-xyangryr/memory/MEMORY.md`（用户偏好与教训）

### 0.3 必须做
- 每个 cluster 修复独立 commit（带 prefix `[FIX-PRE-G-NNN]`，自定义编号 1..7）
- 每个 commit body 写明：根因（不是症状！）、修复方式、为什么这样改最小
- 修一个 cluster 后跑全量 unit test 验证不引入新红
- 若某个 cluster 修不动（根因深 / 涉及 SPEC），**停下来**反馈许阳，**不要**为了让测试绿而 mock / skip / xfail

### 0.4 不要做
- 不要 `pytest.skip` / `xfail` 任何一个失败（除非根因证明确实是不可达代码且许阳同意）
- 不要为了让测试过去**改测试**——除非测试本身写错了（这种情况要在 commit body 详细举证）
- 不要顺手做无关重构

---

## 1. 全量基线现状

执行命令：
```bash
.venv/bin/python3 -m pytest tests/unit/ --tb=no -q \
  --ignore=tests/unit/backend-core/test_spec_c_018.py \
  --ignore=tests/unit/backend-core/test_spec_c_019.py \
  --ignore=tests/unit/backend-core/test_spec_c_020.py \
  --ignore=tests/unit/contracts \
  --ignore=tests/unit/infra/test_spec_b_009.py \
  --ignore=tests/unit/reviewers/test_music_fit_reviewer_v317.py \
  --ignore=tests/unit/reviewers/test_sfx_mix_reviewer.py \
  --ignore=tests/unit/services/test_sfx_segment_mix_service.py
```

**结果**：1463 passed, **23 failed**, 2 skipped, 168s

> 注：上面 `--ignore` 列表里的 17 个文件，是 collection-error 文件（缺 numpy/jsonschema/fastapi/huey）。等修 venv + 补 requirements.txt 后再用全量命令重新基线。

---

## 2. 23 个失败的 7 个 cluster 分类

### Cluster 1：FastAPI 应用入口 (3 failures)
```
tests/unit/infra/test_api_main.py::TestAppEntrypoint::test_app_importable
tests/unit/infra/test_api_main.py::TestAppEntrypoint::test_health_endpoint_registered
tests/unit/infra/test_api_main.py::TestAppEntrypoint::test_health_returns_ok
```

**初步假设**：`src/backend/api/main.py` 不存在或健康检查 endpoint 未注册。SPEC-A SPEC-1A 应有这条端点。

**调查步骤**：
1. `find src/backend/api -name 'main.py' -o -name 'app.py'`
2. 跑 `.venv/bin/python3 -c "from src.backend.api.main import app; print(type(app))"` 看具体错误
3. 检查 SPEC-A SPEC-1A 中 `/health` 端点定义

**预估复杂度**：S（如果是文件缺失，加文件即可；如果是 fastapi 装载顺序，要排查）

---

### Cluster 2：Snapshot.md 只读检查 (2 failures，名称重复)
```
tests/unit/infra/test_preferences.py::TestAC3SnapshotMdReadonly::test_snapshot_md_readonly
tests/unit/infra/test_spec_b_006.py::TestAC3SnapshotMdReadonly::test_snapshot_md_readonly
```

**初步假设**：两个文件同名 test，可能一个是另一个的拷贝/继承。检查 snapshot.md 文件权限校验逻辑。SPEC-B-006 涉及 preferences snapshot。

**调查步骤**：
1. `diff` 这两个测试函数（很可能内容相同，文件路径不同导致实际跑两次）
2. 跑 `.venv/bin/python3 -m pytest tests/unit/infra/test_spec_b_006.py::TestAC3SnapshotMdReadonly::test_snapshot_md_readonly -v` 看断言失败
3. 检查 `src/backend/services/preferences_snapshot.py`（或类似）的只读实现

**预估复杂度**：S

---

### Cluster 3：Pre-flight 健康检查 (7 failures)
```
tests/unit/infra/test_preflight.py::TestAC1CriticalChecksInSystemStatus::test_critical_checks_in_system_status
tests/unit/infra/test_preflight.py::TestAC2CriticalFailureBlocksProjectCreation::test_critical_failure_blocks_project_creation
tests/unit/infra/test_preflight.py::TestAC3DegradedServicesListed::test_degraded_services_listed
tests/unit/infra/test_preflight.py::TestAC4DegradedDoesNotBlockCreation::test_degraded_does_not_block_creation
tests/unit/infra/test_preflight.py::TestAC5ValidUntil24h::test_valid_until_24h
tests/unit/infra/test_preflight.py::TestAC6FullPreflightOnStartup::test_full_preflight_on_startup
tests/unit/infra/test_preflight.py::TestAC7CriticalSubsetOnProjectCreate::test_critical_subset_on_project_create
```

**初步假设**：所有 7 个测试同一文件，**统一根因极可能**——pre-flight 模块本身没接好或某个共享 fixture 失败。SPEC-B-001 / SPEC-B-002 涉及。

**调查步骤**：
1. 跑 `.venv/bin/python3 -m pytest tests/unit/infra/test_preflight.py::TestAC1CriticalChecksInSystemStatus -v` 看具体错误
2. 检查 `src/backend/services/preflight.py`（或类似）是否存在
3. 检查 `tests/unit/infra/test_preflight.py` 的 fixture 是否依赖某个未启动的服务
4. **重点**：7 个失败的 traceback 高度类似 → 一处修复可能解所有

**预估复杂度**：M（如果共享根因，单点修复；否则可能要逐个看）

---

### Cluster 4：SPEC-B-004 任务 API (2 failures)
```
tests/unit/infra/test_spec_b_004.py::TestAC4GetProjectTasksApi::test_endpoint_returns_project_scoped_task_list
tests/unit/infra/test_spec_b_004.py::TestAC5QueuedTaskShowsPosition::test_position_counts_earlier_queued_or_running
```

**初步假设**：`/projects/{id}/tasks` 端点行为不符 SPEC-B SPEC-1A。可能是 task_ledger schema 改动后 API 未跟上。

**调查步骤**：
1. 跑两个测试看具体断言
2. 检查 `src/backend/api/projects.py`（或 routes）实现
3. 关联 PROGRESS.md 的 `9d2e051 SPEC-D-013/D-018 fix fetch() signature` ——可能是 fetch 改动后 API 漏了

**预估复杂度**：M

---

### Cluster 5：SPEC-B-005 重连刷新 (1 failure)
```
tests/unit/infra/test_spec_b_005.py::TestAC6ProgressCorrectAfterReconnect::test_task_api_reads_fresh_state_on_every_call
```

**初步假设**：API 缓存 / sqlite 连接复用导致读不到最新状态。SPEC-B-005 涉及 WebSocket 重连。

**调查步骤**：
1. 看测试实现，理解期望行为
2. 检查 task API 实现是否有缓存层

**预估复杂度**：S-M

---

### Cluster 6：Fixture validation (4 failures，2 文件几乎同名)
```
tests/unit/infra/test_spec_b_017.py::TestAC3ValidFixtures::test_valid_fixtures_pass
tests/unit/infra/test_spec_b_017.py::TestAC3InvalidFixtureFails::test_invalid_fixture_fails
tests/unit/infra/test_validate_fixtures.py::test_valid_fixtures_pass
tests/unit/infra/test_validate_fixtures.py::test_invalid_fixture_fails
```

**初步假设**：和 PROGRESS.md "Open follow-ups" 提到的 `test_validate_fixtures.py::test_valid_fixtures_pass` 是同一个问题。可能 fixture 校验脚本（`scripts/validate_fixtures.py`?）路径或 schema 漂移。

**调查步骤**：
1. 两个文件 diff，确认是不是同一测试
2. 跑测试看具体哪个 fixture 文件不通过
3. 关联 PROGRESS.md "Open follow-ups #4" 的备注

**预估复杂度**：S

---

### Cluster 7：SFX Layout Reviewer (4 failures)
```
tests/unit/reviewers/test_sfx_layout_reviewer.py::TestAC1ScriptCoverage::test_script_coverage_pass_fail
tests/unit/reviewers/test_sfx_layout_reviewer.py::TestAC1KeywordAnchor::test_keyword_anchor_overlap
tests/unit/reviewers/test_sfx_layout_reviewer.py::TestAC1ExplanationCompleteness::test_explanation_completeness
tests/unit/reviewers/test_sfx_layout_reviewer.py::TestAC1Sparsity::test_sparsity
```

**初步假设**：4 个全是 `TestAC1` 子类，单一 reviewer SUT 实现问题。SPEC-D 的 SFX 链路（D-005/D-014/D-103）。

**调查步骤**：
1. 跑 `test_sfx_layout_reviewer.py -v` 看 4 个具体断言
2. 检查 `src/backend/reviewers/sfx_layout_reviewer.py`（或类似）的实现状态
3. 关联 SPEC-D-103（shot-split-anchor）是否影响 reviewer

**预估复杂度**：M（4 个测试可能共享根因，也可能各自独立）

---

## 3. 修复 AI 推荐执行顺序

按"先简单后复杂、先共享根因后散点"原则：

| 顺序 | Cluster | 理由 |
|------|---------|------|
| 1 | C2 (Snapshot.md) | 2 个测试同名，预期共享根因，最快 win |
| 2 | C6 (Fixture validation) | 4 个测试 2 对，预期共享根因 |
| 3 | C5 (SPEC-B-005 重连) | 单点 |
| 4 | C7 (SFX Layout Reviewer) | 4 测试同 reviewer |
| 5 | C3 (Preflight 7 个) | **大概率**单点根因 |
| 6 | C4 (SPEC-B-004 任务 API) | 中等复杂 |
| 7 | C1 (FastAPI 应用入口) | **可能与 venv 修复有交叉**，最后做 |

**强约束**：每个 cluster 修完后，跑全量 unit test 验证不引入回归（命令同 §1）。**任何一次让通过数下降 = 立即回滚 commit**。

---

## 4. 每个 Cluster 的完成标准

每个 cluster 修复后，必须满足：
- [ ] 该 cluster 内 100% 测试 PASS（不允许 skip/xfail 兜底）
- [ ] 全量 unit test 通过数 ≥ 修复前通过数 + 该 cluster 失败数（即不能为了修这个引入别的红）
- [ ] commit body 写明根因（What was actually wrong）+ 修复方式（What was changed）+ 最小化论证（Why this and not bigger refactor）
- [ ] PROGRESS.md 追加 1 行（HARNESS §9.2）

---

## 5. 整体完成判据

- [ ] 7 个 cluster 全部修复（23 个 FAILED → 0）
- [ ] 全量 unit test：1463 + 23 = **1486 passed**, 0 failed, 2 skipped（部分版本，不含 17 个 collection error 文件）
- [ ] 至少 7 个 commit（每 cluster 1 个）
- [ ] PROGRESS.md 追加 7 行
- [ ] 把最终 baseline 数字写入 `docs/SPEC-D-FREEZE-2026-04-25.md`（与"修 venv 交接"协同——venv 修好后跑全量基线一次）
- [ ] 修复 AI 在交接结束时给许阳一份汇总：每 cluster 的根因 + 修复 1 句话 + commit SHA

---

## 6. 异常路径

| 情况 | 修复 AI 应做 |
|------|------------|
| 某 cluster 根因是 SPEC 文档错（不是代码错） | 停止，写入反馈，**不**自改 SPEC |
| 某 cluster 根因是其他 SPEC card 未完成的依赖 | 停止，标注被阻塞的具体 task_id（如 SPEC-D-103），上报许阳决策 |
| 修一个 cluster 引入了别的红 | 立即 `git revert` 该 commit，重新调查 |
| 某 test 经检查确实**应该**用 `xfail`（如 SPEC 故意未实现的 future-feature） | 用 `xfail` 但 **必须** 在 commit body 引用具体 SPEC 段落 |
| 23 个失败的总体根因被发现是单一 commit 引入（如 9d2e051 round 修复） | 上报许阳，可能整体回滚比逐 cluster 修更优 |

---

## 7. 与 SPEC-G-000 拆解的协同关系

```
共同前置：修 venv + requirements.txt 加 huey/numpy
   │
   ├─→ 本交接：修 23 个 unit test 失败（不阻塞 G-000-pre/a/b/c）
   │      │
   │      └─→ 完成后取得干净基线
   │
   └─→ G-000-pre / a / b / c（可与本交接并行）
          │
          └─→ G-000d / e（**强烈建议**等本交接完成后再开始）
```

**理由**：G-000d 改动量大（~250 行）+ 涉及 6 phase 路由，若此时基线还有 23 个红，回归判据失效，G-000d 实施 AI 会陷入"是不是我改坏了"的反复怀疑。

---

*文档版本：v1.0*
*创建：2026-04-25*
*关联文档：`tasks/SPEC-G/G-000-DECOMPOSITION-HANDOFF.md`、`docs/BDD_ANALYSIS_AND_REMEDIATION_PLAN.md`*
