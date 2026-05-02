# 剩余任务开发计划（Wave Plan）

> 创建日期：2026-04-20
> 起点：SPEC-A 完成 + SPEC-B-001 完成（commit 9523290）
> 方法论：TDD RED→GREEN→REFACTOR（`superpowers:test-driven-development`），每张 task card 独立走完流程
> 配套 gate：`scripts/contracts/verify_no_skip_stubs.py`（每 commit 追加本 task 测试文件到 TARGET_FILES）

---

## 全局状态（2026-04-20）

| SPEC | 任务总数 | 已 Done | 剩余 | 剩余 stub | 依赖层 |
|------|---------|---------|------|----------|-------|
| A 合同        | 13 实施 + 10 未实施（a-003/005/006/008/012/100..104） | 13 | 10 | 63 | Layer 0（已完成） |
| B 基础设施    | 19 (B-001..018 + B-100) | 1 (B-001) | 18 | 105 | Layer 1 |
| C 后端核心    | 28 (C-001..022 + C-100..106) | 1 (C-106 POC) | 27 | 199 | Layer 2，依赖 B |
| D 流水线      | 26 (D-001..022 + D-100..103) | 0 | 26 | 362 | Layer 3，依赖 C |
| E 前端        | 21 (E-001..015 + E-100..105) | 8 (E-001/002/003/007/008/009/010/100) | 13 | 23 | 并行轨道 |
| F 媒体渲染    | 17 (F-001..014 + F-100..102) | 0 | 17 | 105 | Layer 4，依赖 D |
| **合计**      | **124** | **23** | **101** | **857** | — |

> 说明：stub 统计来自 `tests/` 目录下 `pytest.skip("NOT IMPLEMENTED ...")` 模式；
> E 剩余任务里只有 E-004/005/006 有 Python stub 文件（其它走 vitest/TS 测试，stub 计数偏少）。

---

## 推进顺序（按 HARNESS 依赖层级）

```
┌─ Wave 1: SPEC-B（基础设施）18 task ──┐  ← 当前位置（B-002 起）
│                                        │
├─ Wave 2: SPEC-C（后端核心）27 task ───┤  ← 需等 B 就绪
│                                        │
├─ Wave 3: SPEC-D（流水线编排）26 task ─┤  ← 需等 C 就绪
│                                        │
├─ Wave 4: SPEC-F（渲染层）17 task ─────┤  ← 需等 D 就绪
│                                        │
└─ 并行轨道: SPEC-E 剩 13 task ─────────┘  ← A 完成即可推进（已完成 8 张）
```

---

## Wave 1 · SPEC-B（基础设施，18 张）

顺序依 `depends_on` 字段粗排，细节以每张 card 为准。

| # | Task | 标题 | 测试文件 stub | 状态 |
|---|------|------|--------------|------|
| 1 | B-001 | docker-compose-three-services | 0 | ✅ Done (9523290) |
| 2 | **B-002** | persistent-write-path | 4 | 🚧 下一张 |
| 3 | B-003 | huey-worker-setup | 7 | ⏳ |
| 4 | B-004 | async-tasks-table-and-api | 6 | ⏳ |
| 5 | B-005 | worker-crash-recovery | 6 | ⏳ |
| 6 | B-006 | preferences-table-and-storage | 6 | ⏳ |
| 7 | B-007 | agent-call-log-and-cost | 5 | ⏳ |
| 8 | B-008 | sensitive-field-redaction | 5 | ⏳ |
| 9 | B-009 | preflight-and-degradation | 7 | ⏳ |
| 10 | B-010 | observability-and-alerts | 6 | ⏳ |
| 11 | B-011 | rollout-rollback-scripts | 5 | ⏳ |
| 12 | B-012 | nonfunctional-and-test-strategy | 7 | ⏳ |
| 13 | B-013 | master-audio-ref-migration | 8 | ⏳ |
| 14 | B-014 | storage-directory-layout | 11 | ⏳ |
| 15 | B-015 | huey-p7a-tasks | 9 | ⏳ |
| 16 | B-016 | keyframe-render-outbound-whitelist | 9 | ⏳ |
| 17 | B-017 | frontend-mock-and-fixtures | 测试缺失 | ⏳ 需先建测试 |
| 18 | B-018 | real-integration-dev-env | 测试缺失 | ⏳ 需先建测试 |
| 19 | B-100 | claim-verification-worker | 4 | ⏳ |

**Wave 1 合计剩余 stub：105**

---

## Wave 2 · SPEC-C（后端核心，27 张）

依赖：B-001/B-003/B-004 就绪后启动。建议顺序分组：

- **工作流框架组**：C-001..005（引擎、状态机、调度、版本）
- **Intent Router 组**：C-006/007/008/101
- **Agent 体系组**：C-009/010/011/012/013
- **业务 Agent 组**：C-014/015/016/017/018/019/020/102/103/104
- **P7A 专项**：C-021/022/105
- **安全与编排**：C-100
- POC 已 done：C-106

**Wave 2 合计剩余 stub：199**

---

## Wave 3 · SPEC-D（流水线编排，26 张）

依赖：SPEC-C 的 producer/reviewer/gate 框架就绪。建议按阶段推进：

- **P0-P11 阶段**：D-002..009（每张 ~20+ stub，重点工作量）
- **Reviewer 与 Gate 框架**：D-010/011/012
- **材料与数据服务**：D-013/014
- **跨阶段审计**：D-001/015
- **观众体验与故障恢复**：D-016/017
- **Gate 系列**：D-018/019/020/021/022
- **Claim 生命周期**：D-100/101/102/103

**Wave 3 合计剩余 stub：362**（最大量）

---

## Wave 4 · SPEC-F（媒体渲染，17 张）

依赖：SPEC-D 的 shot / material / keyframe 产物就绪。

- **ECharts 模板**：F-001/002/003/004/100/101
- **React 模板**：F-005/006/013
- **Remotion 编排**：F-007/014/102
- **TTS 与字幕**：F-008/009/010
- **封面与预览**：F-011/012

**Wave 4 合计剩余 stub：105**

---

## 并行轨道 · SPEC-E（前端，剩 13 张）

不阻塞 B/C/D/F，可与任一 Wave 并行推进（8 张已 Done）。

| Task | 标题 | 备注 |
|------|------|------|
| E-004 | settings-page | 7 stub |
| E-005 | phase-preview-components | 6 stub |
| E-006 | data-verification-panel | 10 stub |
| E-011 | p4-master-player | 需 D-004 产物 |
| E-012 | p5-mix-preview-and-master | 需 D-005 产物 |
| E-013 | p6-annotation-and-final-audio | 需 D-005 产物 |
| E-014 | p7a-shot-material-matrix | 需 D-006 + C-021 |
| E-015 | frontend-types | 纯类型契约 |
| E-101 | phase-detail-drawer | |
| E-102 | claim-workbench | 需 C-103 |
| E-103 | storyboard-editor-anchor-split | 需 D-103 |
| E-104 | chart-confirm-dialog | 需 C-105 |
| E-105 | preference-safety-cards | 需 C-014/100 |

---

## 单张 task 执行模板

每张 task card 严格走同一流程（以 B-001 为样本，已验证可行）：

1. **读 task card** `tasks/SPEC-X/X-NNN-*.md`
   - allowed_files / acceptance_criteria / verification_commands / test_mapping
2. **RED**：打开 `tests/unit/<layer>/test_spec_x_NNN.py`，按 AC 逐个
   - 删除 `pytest.skip("NOT IMPLEMENTED ...")`
   - 写真实断言（复用 SPEC-A REDO plan §10-pattern）
   - `pytest tests/unit/<layer>/test_spec_x_NNN.py -v` → 确认所有新断言 fail，且失败原因符合预期（不是语法错）
3. **GREEN**：按 allowed_files 写最小实现，直到测试全绿
4. **REFACTOR**：保持绿灯整理
5. **扩展 gate**：
   - 打开 `scripts/contracts/verify_no_skip_stubs.py`
   - 把 `tests/unit/<layer>/test_spec_x_NNN.py` 追加到 `TARGET_FILES`
   - `.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py` → exit 0
6. **commit**（用 `.claude/scripts/commit-task.sh` 或手写 HEREDOC）
   - title：`[SPEC-X-NNN] <imperative title>`
   - body：HARNESS §9.3（Files Changed / Verification / Decisions / Artifacts）
7. **PROGRESS.md** 追加一行（SHA / task / title / date）+ Status snapshot 加 task ID
8. **pick 下一张**

---

## Verification（每张 task 完成时）

```bash
# 测试通过
.venv/bin/python3 -m pytest tests/unit/<layer>/test_spec_x_NNN.py -v

# Gate 通过（无 stub 遗留）
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py

# task card 的 verification_commands 全部执行
# commit 落盘 + PROGRESS 更新
git log --oneline -1 && tail -1 PROGRESS.md
```

**完成判据**：
- [ ] task card 所有 acceptance_criteria 对应真实断言（非 stub）
- [ ] 测试通过 mutation sanity check（改实现应让测试红）
- [ ] 测试实际 pass
- [ ] `verify_no_skip_stubs.py` exit 0
- [ ] commit 已落、PROGRESS 已更新
- [ ] gate TARGET_FILES 已扩展

---

## 收尾事项（随时择机处理，不阻塞推进）

1. **Py3.9 `Type | None` 语法兼容** — `src/backend/startup/ensure_user_dir.py:6`，当前 `.venv` pin 3.11 不影响；若后续支持 Py3.9 需改为 `Optional[...]`
2. **`check_schema_alignment.py` 缺失** — SPEC-B 领地，A-013..A-017 Verification Commands 曾引用；AC-2 跨语言契约由 `test_pydantic_ts_alignment_*` 覆盖
3. **`verify_no_skip_stubs.py` 改名** — 当前位于 `scripts/contracts/`，名称偏合同专用；Wave 1 结束前视情况改名为 `scripts/contracts/verify_done_tasks_no_stub.py` 或挪到 `scripts/verify_done_tasks_no_stub.py`
4. **4 个合同测试失败** — `test_artifact_schemas.py` / `test_candidate_project_state.py` / `test_error_codes.py` 里的预先失败用例，与 B-001 无关，后续定位

---

## 风险与预案

| 风险 | 预案 |
|------|------|
| Docker 相关测试需真实环境 | 单元层断言 YAML 配置正确 + 集成层 `@pytest.mark.integration` 真启容器；分层处理 |
| task card depends_on 复杂 | 每张 card 开工前读 depends_on，必要时跳过后补 |
| SPEC 仍在变动（如 v3.17 新增） | 先做稳定部分，再做新增；每周核对一次 SPEC 变更 |
| Wave 3 单张 task 20+ AC | D-002..009 可能单张 1 天以上；若卡住 > 4h，拆子 task |
| 前后端协作 | SPEC-E 与 B/C/D 并行时，先对齐 API 契约（SPEC-A 已提供） |

---

## 关键文件索引

| 文件 | 作用 |
|------|------|
| `HARNESS.md` §4 TDD / §9.3 commit body / §12 task card | 流程规范（必读） |
| `tasks/SPEC-A/REDO-real-tests-plan.md` | 可复用的 10 种断言 pattern |
| `scripts/contracts/verify_no_skip_stubs.py` | Skip-stub gate（每 commit 扩展） |
| `scripts/contracts/run_contract_tests.sh` | SPEC-A 测试 runner（可复用） |
| `.claude/scripts/commit-task.sh` + `AUTO_COMMIT.md` | HARNESS §9.3 commit 辅助 |
| `PROGRESS.md` | 进度索引（每 commit 一行） |
| `tests/unit/infra/test_spec_b_001.py` | B-001 样本（19 断言 / 7 AC / 已 GREEN） |

---

## 变更记录

- **2026-04-20 创建** — SPEC-A REDO 完成、SPEC-B-001 落地后整理；Wave 1 B-002 为下一张。
