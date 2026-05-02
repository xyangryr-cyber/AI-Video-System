# SPEC-D 状态冻结文档 实施方案交接文档

> **本文档身份**：交接给另一个 AI（实施 AI）的工作单
> **目的**：产出 `docs/SPEC-D-FREEZE-2026-04-25.md` —— 把 SPEC-D 26 张 cards 当前状态、契约边界、单测基线、已知 follow-up **冻结成一份可被 G-000 引用的快照文档**
> **创建于**：2026-04-25
> **背景作者**：上游 AI（已和许阳达成"G-000 实施前必须有 SPEC-D 静态基线"的决策）
> **优先级**：**P0**（G-000-pre 的 metadata 要引用本文档；不冻结 = G-000 实施 AI 无法判定 SPEC-D 接口是否还会变）
> **预估工时**：S（45-90 分钟，多数时间在跑测试与读 PROGRESS）
> **依赖**：`tasks/VENV-FIX-HANDOFF.md` 必须**先**完成（需要干净 baseline 数字）

---

## 0. 实施 AI 必读

### 0.1 任务边界
- **范围**：**仅产出**一份新文档 `docs/SPEC-D-FREEZE-2026-04-25.md`，commit on main。
- **不在范围**：
  - 不修任何代码、SPEC、task card 内容
  - 不"顺手"重整 PROGRESS.md
  - 不改 SPEC-D 任何 card 的状态（即便发现某 card 实际未达 DONE 标准——也仅在本冻结文档"已知缺口"区记录，**不**回头改 PROGRESS）

### 0.2 必读
1. 本文档全文
2. `HARNESS.md` §9（PROGRESS 单源真相）、§13.2（无 task ID 的 TODO 禁忌）
3. `PROGRESS.md`（取 SPEC-D 状态的真值源）
4. `tasks/SPEC-D/`（26 张 card 列表）
5. `docs/specs/SPEC-D-pipeline-phases.md`（契约真值）
6. 上一份冻结/交接：是否已有类似文档（如 `PROGRESS.md.full.backup.2026-04-25.md`）——避免重复

### 0.3 必须做
- 文档内每条事实必须**可验证**（带命令、SHA、文件路径），不允许"大概是"、"应该完成"
- 数字（passed/failed）必须是**亲自跑出来**的，不引用 PROGRESS 或他人陈述
- 用绝对日期（2026-04-25），不用"今天"、"上周"
- main 分支单 commit，prefix `[SPEC-D-FREEZE]`

### 0.4 不要做
- 不要在文档里做"建议"、"展望"、"未来工作"——本文档是**快照**，不是规划
- 不要复制 SPEC-D-pipeline-phases.md 的全文进来——用引用与 sha256 即可
- 不要追加 "Conclusion" / "Summary" / "总结" 等装饰段——快照只需要事实

---

## 1. 文档目标骨架

最终产出：`docs/SPEC-D-FREEZE-2026-04-25.md`，结构如下：

```markdown
# SPEC-D 状态冻结快照 — 2026-04-25

> Snapshot purpose: 冻结 SPEC-D 流水线状态，供 SPEC-G-000 系列子卡引用为契约基线
> Snapshot date: 2026-04-25
> Snapshot author: <实施 AI 名字 / 占位>
> Main commit: <填入主分支 HEAD SHA>
> Venv state commit: <填入 VENV-FIX-HANDOFF 产出的 SHA>

## 1. SPEC-D Cards 状态
（26 行表格，列出每张 card 的 task_id、title、status、PROGRESS commit SHA）

## 2. SPEC-D 单测基线
（pytest 命令 + 实测三元组数字）

## 3. 关键 Schema 契约 sha256
（timeline.json、claim_artifact、material_manifest 等的当前 sha256）

## 4. Agent 公共方法签名清单（6 个 phase agent）
（关键方法签名 + 文件:行号）

## 5. 已知 follow-ups / 缺口
（PROGRESS Open follow-ups + 自查发现的不一致）

## 6. 冻结契约保证
（明确说明本冻结之后，G-000 在引用哪些不变性）
```

每节详细要求见 §2-§7。

---

## 2. 节 1：SPEC-D Cards 状态（26 行表格）

### 数据采集
```bash
ls tasks/SPEC-D/ | sort
```
得到 26 个 card 文件名，逐个解析 task_id（即文件名前缀，如 `D-001-artifact-authority-map.md` → `SPEC-D-001`）。

```bash
git log --all --oneline --grep="SPEC-D-" | head -50
```
得到每个 D card 对应的 commit SHA。

```bash
grep "SPEC-D-" PROGRESS.md
```
得到 PROGRESS 表格中的对应行，作为交叉验证。

### 输出表格格式
```markdown
| task_id | title | PROGRESS 状态 | 主要 commit SHA | 备注 |
|---------|-------|--------------|----------------|------|
| SPEC-D-001 | artifact-authority-map | DONE | <sha> | — |
| SPEC-D-013 | financial-data-service | DONE | <sha> | round-fix at 9d2e051 |
| ... | ... | ... | ... | ... |
| SPEC-D-103 | shot-split-anchor-validation | DONE | <sha> | — |
```

**强制要求**：
- 26 行，0 缺失，0 多
- 每行 SHA 来自 `git log --grep`，不来自 PROGRESS 表格（PROGRESS 是索引、可能漂移）
- 若某 card 在 PROGRESS 表格里写 DONE 但 git log 找不到对应 commit → 标"⚠ unverified"并在节 5 列出

---

## 3. 节 2：SPEC-D 单测基线

### 前置
- `VENV-FIX-HANDOFF` 已完成
- `.venv` 可用 huey/numpy/jsonschema/fastapi

### 采集命令
```bash
.venv/bin/python3 -m pytest tests/unit/pipeline tests/unit/gates tests/unit/reviewers -q --tb=no | tee /tmp/spec-d-baseline.txt | tail -3
```

（路径若 SPEC-D 测试散落更广，可加 `tests/unit/services/` 等）

### 输出格式
```markdown
## SPEC-D 单测基线

执行命令：
\```
.venv/bin/python3 -m pytest tests/unit/pipeline tests/unit/gates tests/unit/reviewers -q --tb=no
\```

执行时间：2026-04-25 HH:MM (UTC+8)

结果：
- Passed: <X>
- Failed: <Y>
- Skipped: <Z>
- Total collected: <X+Y+Z>
- Duration: <T>s

按 SPEC-D 子目录拆分（信息性）：
| 子目录 | passed | failed |
|--------|--------|--------|
| tests/unit/pipeline | <a> | <b> |
| tests/unit/gates | <c> | <d> |
| tests/unit/reviewers | <e> | <f> |

已知失败列表（如果 Y > 0）：
- <test_id>::<test_name>  ← 引用 HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md cluster N
```

---

## 4. 节 3：关键 Schema 契约 sha256

### 目标
列出 SPEC-D 流水线**外部不可破坏**的契约 schema 文件 sha256 哈希——G-000 实施 AI 需检查这些 schema 在其工作过程中**未被改动**。

### 待哈希文件清单
```bash
shasum -a 256 \
  src/shared/schemas/timeline_v3.json \
  src/shared/schemas/claim_artifact.json \
  src/shared/schemas/material_manifest.json \
  src/shared/schemas/audio_master.json \
  src/shared/schemas/sfx_layout.json \
  src/shared/schemas/chart_material.json \
  src/backend/db/migrations/001_initial.sql \
  migrations/V002__create_claim_tables.sql \
  migrations/V003__create_stage_preferences.sql \
  migrations/V004__add_latest_reached_phase.sql \
  migrations/V005__extend_task_ledger_types.sql \
  2>/dev/null
```

**注意**：列表中文件可能不存在（schemas 目录可能未全列）。**实际文件以 `ls src/shared/schemas/` 与 `ls migrations/` 为准**——把实际找到的全部 .json 与 .sql 都哈希。

### 输出格式
```markdown
## 关键 Schema / Migration sha256

| 文件 | sha256 |
|------|--------|
| src/shared/schemas/timeline_v3.json | <hash> |
| src/shared/schemas/... | <hash> |
| src/backend/db/migrations/001_initial.sql | <hash> |
| migrations/V002__... | <hash> |

**冻结意图**：G-000 实施期间这些文件**不应被修改**。若必须改（如 G-000-pre 修 task_types.py 间接影响某 schema），必须在新 commit 的 body 显式列出"哈希变更原因"，并在本冻结文档之后另起一份新冻结。
```

---

## 5. 节 4：6 个 Phase Agent 公共方法签名清单

### 目标
固化 G-000 子卡 d 阶段调用的 agent 方法签名，避免实施 AI 中途发现 agent 改了签名。

### 采集命令
```bash
grep -nE "^    def [a-z]" src/backend/agents/tts_agent.py
grep -nE "^    def [a-z]" src/backend/agents/bgm_agent.py
grep -nE "^    def [a-z]" src/backend/agents/sfx_agent.py
grep -nE "^    def [a-z]" src/backend/agents/keyframe_render_agent.py
grep -nE "^    def [a-z]" src/backend/agents/rough_cut_agent.py
grep -nE "^    def [a-z]" src/backend/agents/final_cut_agent.py
```

### 输出格式
```markdown
## 6 个 Phase Agent 公共方法（冻结）

### TTSAgent (src/backend/agents/tts_agent.py)
- L24 `class TTSAgent`
- L39 `select_voice_candidates(*, polished_script, voice_preferences=None) -> List[Dict]`
- L<N> `build_timeline(...)`
- ...

（重复 6 个 agent；只列方法签名第一行 + 文件:行号）

**冻结意图**：G-000d 实施期间，这些方法签名（参数名、参数类型、返回类型）**不应改变**。改 = 阻塞 G-000d，必须先单独走 SPEC-D 修订流程。
```

---

## 6. 节 5：已知 follow-ups / 缺口

### 数据来源
1. PROGRESS.md "Open follow-ups" 段
2. `tasks/REMAINING-WORK-PLAN.md`（如存在）
3. 节 1 中标 ⚠ unverified 的 card
4. 节 2 中失败测试是否有未在 HISTORICAL-FAILURES 文档覆盖的

### 输出格式
```markdown
## 已知 follow-ups / 冻结缺口

### 来自 PROGRESS.md Open follow-ups
- <逐条引用，加日期>

### SPEC-D 卡片状态不一致（节 1 ⚠ 项）
- <如有>

### SPEC-D 单测中失败但本冻结之外的（节 2 中超 HISTORICAL-FAILURES 覆盖范围的）
- <如有>

### 其他自查发现
- <实施 AI 自查时发现的不一致>
```

如果都没有，写一行：`无（截至 2026-04-25 全部 SPEC-D 状态自洽）`。**禁止**为了让段落充实而硬塞内容。

---

## 7. 节 6：冻结契约保证

### 输出格式（直接抄）
```markdown
## 冻结契约保证

本冻结快照保证以下不变性，直至下一份冻结（或显式声明冻结作废）：

1. **SPEC-D 26 张 cards 列出的 task_id 与 PROGRESS commit SHA 不变**——若某 card 需 round-fix，新 commit 必须以 `(round N)` 形式追加到 PROGRESS，**不**回头改本冻结文档
2. **节 3 列出的 schema/migration 文件 sha256 不变**——若必须改，新 commit body 必须显式记录哈希变更并起新冻结
3. **节 4 列出的 6 个 phase agent 方法签名不变**——SPEC-G-000d 在此基础上路由
4. **本冻结之后引用本文档的下游 task（特指 SPEC-G-000-pre / a / b / c / d / e）可信任以上 3 条**

如本冻结发布后某不变性被破坏，下游 task 实施 AI 应停下并触发"冻结失效"流程：
- 创建 `docs/SPEC-D-FREEZE-2026-04-25-INVALIDATED.md`
- 重新走本交接，产出新日期的冻结
- 通知许阳决策是否继续推进 G-000 子卡
```

---

## 8. 实施步骤总览

1. **前置确认**：`tasks/VENV-FIX-HANDOFF.md` 已完成？
   - 若未完成 → stop，等待
2. **采集数据**（命令见各节）
3. **写文档** `docs/SPEC-D-FREEZE-2026-04-25.md`，按 §1 骨架
4. **自查**：6 节都填，无占位符（不允许残留 `<TBD>`、`<填入>`）
5. **commit**:
   ```bash
   git add docs/SPEC-D-FREEZE-2026-04-25.md
   git commit -m "$(cat <<'EOF'
   [SPEC-D-FREEZE] freeze SPEC-D state snapshot for G-000 reference baseline

   Files Changed:
   - docs/SPEC-D-FREEZE-2026-04-25.md (new)

   Verification:
   - All 26 SPEC-D cards listed with verified commit SHA
   - SPEC-D unit baseline: <X passed / Y failed / Z skipped>
   - <N> schemas / migrations hashed
   - 6 phase agents' method signatures captured

   Decisions:
   - <若有非显然取舍>

   Artifacts:
   - docs/SPEC-D-FREEZE-2026-04-25.md

   Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```
6. PROGRESS.md "Recent commits" 表格追加 1 行
7. 给许阳交付：commit SHA + 文档路径 + 一句话总结

---

## 9. Acceptance Criteria
- [ ] AC-1: `docs/SPEC-D-FREEZE-2026-04-25.md` 存在，6 个节齐全
- [ ] AC-2: 节 1 表格 26 行（精确数）
- [ ] AC-3: 节 2 三元组数字来自实跑命令
- [ ] AC-4: 节 3 哈希至少覆盖 `src/shared/schemas/` 全部 .json 与 `migrations/`、`src/backend/db/migrations/` 全部 .sql
- [ ] AC-5: 节 4 六个 agent 全部覆盖
- [ ] AC-6: 节 5 至少明确写出 PROGRESS Open follow-ups 当前条目
- [ ] AC-7: 节 6 直接抄模板（不让节 6 变成"实施 AI 自由发挥"）
- [ ] AC-8: 单 commit, prefix `[SPEC-D-FREEZE]`
- [ ] AC-9: 文档无占位符 / TODO

---

## 10. 异常路径

| 情况 | 实施 AI 应做 |
|------|------------|
| 节 1 发现 PROGRESS 写 DONE 但 git log 无对应 commit | 节 5 ⚠ 列出，**不**回头改 PROGRESS |
| 节 2 跑出 SPEC-D 单测大批新红（远超 HISTORICAL-FAILURES 覆盖） | stop，反馈许阳，可能 venv-fix 引入了行为变化 |
| 节 3 某关键 schema 文件不存在（如 timeline_v3.json） | 节 5 ⚠ 列出，标"contract gap" |
| 节 4 某 agent 公共方法少于 G-000-DECOMPOSITION 文档列出的 | 节 5 ⚠ 列出，可能 G-000d 子卡本身需要修订 |
| 实施 AI 中途想加新节（如"Layer 4 性能基线"） | **不要**，本文档是固定骨架，**改骨架要回头修本交接** |

---

## 11. 完成判据
- [ ] AC-1..AC-9 全过
- [ ] commit SHA 已记录
- [ ] PROGRESS.md 有 1 行新增
- [ ] 实施 AI 给许阳交付：
  - commit SHA
  - 文档路径
  - 一句话总结：`SPEC-D 状态已冻结于 SHA=<x>, baseline = <X/Y/Z>, <N> 个不一致已记录`

---

## 12. 与下游任务的协同

```
VENV-FIX-HANDOFF
   │
   └─→ 本交接（SPEC-D-FREEZE-HANDOFF）
          │
          └─→ 解锁 SPEC-G-000-pre 引用本冻结文档
                   │
                   └─→ G-000a..e 顺序推进
```

下游 G-000-pre 在 metadata 加：
```yaml
freeze_ref: docs/SPEC-D-FREEZE-2026-04-25.md (commit <sha>)
```

---

*文档版本：v1.0*
*创建：2026-04-25*
*关联文档：`tasks/VENV-FIX-HANDOFF.md`、`tasks/SPEC-G/G-000-DECOMPOSITION-HANDOFF.md`、`tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md`*
