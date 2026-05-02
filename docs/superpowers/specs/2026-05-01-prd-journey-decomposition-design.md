# PRD v3.3 Journey-First 拆分设计

> **Date**: 2026-05-01
> **Author**: 许阳 + Claude (brainstorming session)
> **Source**: `docs/PRD_v3.3_Web交互式视频制作系统.md` (1955 lines, 10 parts)


## 2. 拍板决议（5 题）

| # | 决议 | 含义 |
|---|---|---|
| 1 | 旧 SPEC-A..G **归档** | 移至 `docs/specs/_archive/SPEC-A..G/`，留 README 指针解释"已废弃，被 Journey-first 替代"，git 历史保留 |
| 2 | Journey 命名 **按 phase 分组** | `J-P0-001`、`J-P5-002`，跨阶段 Journey 用 `J-L-001`（L = Layered/横切）。Module 用 `M-PN-NNN` |
| 3 | AI 安全护栏 **不单独成 Journey** | §10.A AI 安全与合规作为各 LLM Module 的 prompt + 输出校验横切要求落地，不单独建 Journey；上一轮 brainstorm 中暂定的 "L-004" 命名作废，避免与本文 §4.2 的 `J-L-004`（图表闭环）冲突 |
| 4 | ~32 条 Journey **接受** | 不做激进合并，每个 phase 的 advance gate 各自一卡（规则不同） |
| 5 | 共享前端基础设施标记 **frontmatter `shared: true`** | Module 卡 frontmatter 加 `shared: true` + `first_introduced_in: J-PN-NNN`，便于 lint 脚本机器识别 |

---

## 3. 命名规范

```
J-P0-001  -- Phase 0 的第 1 条 Journey
J-P5-002  -- Phase 5 的第 2 条 Journey
J-L-001   -- 跨阶段 / 横切 Journey
M-P0-003  -- Phase 0 第 3 个 Module
M-L-001   -- 跨阶段 Module（如 useWebSocket）
```

目录结构：

```
tasks/
  SPEC-P0-JOURNEY/                 # 已存在，作为参考实现
    README.md
    J-P0-001-*.md
    modules/
      M-P0-001-*.md
  SPEC-P1-JOURNEY/                 # 新增
  ...
  SPEC-P11-JOURNEY/
  SPEC-LAYER-JOURNEY/              # 跨阶段 Journey 集中地
    J-L-001-project-list-shell.md
    J-L-002-realtime-events.md
    J-L-003-phase-replay.md
    J-L-004-chart-loop-end-to-end.md  # 来自 §10.H
    modules-shared/                # shared: true 的共享 Module
      M-L-001-use-websocket.md
      M-L-002-theme-json.md
      ...
```

---

## 4. Phase Journey 骨架（每个 phase 的 Journey 模式）

### 4.1 通用三段式

每个 phase 默认有 3 条 Journey：

```
J-PN-001  生成      入口 → 触发 → ≤Xs 看到产物预览
J-PN-002  迭代      用户输入修改意见 → Router 识别 → ≤Xs 卡片更新 + 自动 re-review
J-PN-003  推进      点击进入下一阶段 → 偏好 Modal → GateKeeper → 下一 phase 高亮
```

**例外**：

- P5 BGM、P6 SFX：以工具自动选片为主，用户介入度低 → 可能合并 002+003 为一卡。
- P10 粗剪、P11 精剪：以渲染流水线为主，可能拆为 "渲染" + "审阅" 两卡，去掉 002 迭代卡。
- 实际 Journey 数由 prd-to-spec 工具按 PRD §7.X 各 phase 的"用户交互点"小节自动判定。

### 4.2 各 Phase 预估 Journey 数

| Phase | 主题 | Journey 数 | 命名预览 |
|---|---|---|---|
| P0 | 需求定义 | 3（已存在） | J-P0-001..003 |
| P1 | 大纲 | 3 | J-P1-001..003 |
| P2 | 脚本结构化 | 3 | J-P2-001..003 |
| P3 | 脚本风格润色 | 2-3 | J-P3-001..00N（N 由 prd-to-spec 据 §7.5 用户交互点判定） |
| P4 | TTS | 2-3 | J-P4-001..00N |
| P5 | BGM | 2 | J-P5-001..002 |
| P6 | SFX | 2 | J-P6-001..002 |
| P7 | 分镜 | 3 | J-P7-001..003（含 anchor 化，§10.G） |
| P8 | 关键画面渲染 | 2-3 | J-P8-001..00N |
| P9 | B-Roll | 2 | J-P9-001..002 |
| P10 | 粗剪合成 | 2 | J-P10-001..002 |
| P11 | 精剪交付 | 2 | J-P11-001..002 |
| **小计** | | **~28** | |

**横切 Journey**：

| ID | 主题 | 来源 |
|---|---|---|
| J-L-001 | 项目列表 + 入口 + 路由壳 | PRD §5.1, §5.2 |
| J-L-002 | 实时事件流（WebSocket events 表） | PRD §8 + §10.F |
| J-L-003 | 阶段回看 / 历史只读访问 | §10.F |
| J-L-004 | 图表请求端到端闭环（用户提请求 → P8 渲染 → 看到图表） | §10.H（真正的跨阶段 Journey） |

**总计**：~32 条 Journey（28 phase + 4 横切）。

---

## 5. 前端开发任务的归属

**核心原则**：**没有独立的"前端 SPEC"**。前端代码全部是某条 Journey 的 Module。

### 5.1 三种归属模式

| 模式 | 何时适用 | evidence_type | 卡片归属 |
|---|---|---|---|
| **A. 页面级 Module** | 与某条 Journey 一一对应（如 NewProject 页 = J-P0-001 的入口） | `user_observable` | Module 挂在所属 Journey 下 |
| **B. 跨 Journey 共享基础设施** | 一次实现、N 个 Journey 复用（hooks / 路由 / 设计系统 / 原子组件） | `consumer_driven` | Module 在最早需要它的 Journey 内首次落地，frontmatter `shared: true`，后续 Journey 引用而非重写 |
| **C. 纯交互/视觉 Journey** | 没有后端逻辑、纯前端可观察行为（罕见） | `user_observable` | 独立 Journey（如 J-L-001 项目列表） |

### 5.2 共享基础设施初步清单（frontmatter `shared: true`）

每个共享 Module 必须声明 `first_introduced_in: J-PN-NNN`：

| Module | 首次引入位置 | 引入理由 |
|---|---|---|
| `M-L-001` 路由壳 + AppShell layout | J-L-001 | 项目列表页是第一个需要路由的 Journey |
| `M-L-002` design system / theme.json | J-L-001 | 同上 |
| `M-L-003` PhaseNavigation 组件 | J-P0-001 | Phase 0 工作流页第一次出现阶段导航 |
| `M-L-004` useWebSocket | J-P0-001 | Phase 0 长任务进度需要 WS |
| `M-L-005` useProjectState | J-P0-001 | 项目状态读取的统一接口 |
| `M-L-006` useChat | J-P0-002 | 用户输入修改意见的 chat 输入区 |
| `M-L-007` useAdvance | J-P0-003 | advance 接口调用统一入口 |
| `M-L-008` Modal / Button / Card 原子组件 | J-L-001 | 项目列表已经需要 Modal/Button |

### 5.3 禁止反模式

- ❌ "J-FRONTEND-001 build design system" 单独 Journey（违反 vertical slicing）。
- ❌ 在某条 Journey 完成后追加一张"Refactor: 抽出共享 hook"卡（共享应该在引入时就识别）。
- ❌ Module 不挂任何 Journey（split-spec checklist 直接拒）。

### 5.4 Module 内顺序（每条 Journey 内部的 RED → GREEN）

1. 写 playwright RED 测试（Journey 卡声明的 evidence_type: user_observable 路径）
2. 后端 API + DB schema（consumer_driven Module）
3. Agent + prompt + eval set（eval_based Module）
4. 前端页面 + 引用共享 Module（user_observable Module）
5. playwright GREEN

### 5.5 Prototype 的角色

`prototype/**` 是**只读的视觉真值源**，每个前端 Module 的 acceptance criteria 必须包含"与 prototype/<对应页> 视觉对齐"。Prototype 不是单独 Journey，也不进 `src/frontend/**`。

---

## 6. v3.16-BDD §10.A-H 落点

| BDD 簇 | 落点 Journey | 说明 |
|---|---|---|
| 10.A AI 问答安全与合规 | **不单独成 Journey**（用户决议） | 作为各 LLM 节点的 prompt + 输出校验横切要求，落到各 phase 的 generate Journey 的 Module 中 |
| 10.B 数据验证面板 → Claim 工作台 | J-L-003（阶段回看） + 各 phase 的 003 advance Journey | Claim 数据是在每个 phase 推进时聚合的，工作台展示在阶段回看页 |
| 10.C 用户质疑/补充事实 | 各 phase 的 002 迭代 Journey | revise/regenerate 增强 |
| 10.D 偏好模型扩展（阶段偏好回写） | 各 phase 的 003 advance Journey | 偏好 Modal 增强 |
| 10.E 结构化插入与最小改动改稿 | J-P2-002（脚本阶段的迭代 Journey） | inject_subtask 动作仅在 P2 阶段触发 |
| 10.F 项目列表与阶段回看 | J-L-001 + J-L-003 | 列表页 + 阶段回看页 |
| 10.G 分镜精确拆解 anchor 化 | J-P7-001 / J-P7-002 | 分镜阶段的生成 + 迭代 Journey |
| 10.H 图表请求闭环 | **J-L-004**（跨阶段 Journey） | 用户在 P2 提图表请求 → P8 渲染图表 → 用户看到图表，这是真正的纵切端到端流程 |

---

## 7. 跨切关注点（cross-cutting concerns）的引入策略

不允许"为未来准备"的 SPEC。下述基础设施在第一次需要它的 Journey 中首次落地，后续 Journey 复用。

| Concern | 首次引入 Journey | 形态 |
|---|---|---|
| `task_ledger` 表 | J-P0-001 | M-P0-001 后端 infra Module |
| `events` 表 + WS broadcast | J-P0-001 | M-P0-002（与 useWebSocket 配对） |
| GateKeeper 校验框架 | J-P0-003 | M-P0-010（advance endpoint） |
| Intent Router | J-P0-002 | M-P0-005 |
| Reviewer 框架（L1 + L2 双层） | J-P0-001（CompletenessReviewer） | M-P0-006 |
| 阶段偏好持久化 | J-P0-003 | M-P0-009 |
| Artifact 版本化 | J-P0-002 | M-P0-007 |

后续 Journey（J-P1-001 起）中需要这些 concern 时，**引用**已有 Module，不重新定义；如果需要扩展（例如 P7 GateKeeper 规则不同），写新 Module 继承。

---

## 8. evidence_type 边界判定

防止"什么都塞 user_observable"或"什么都用 consumer_driven 蒙混过关"：

- **Journey 卡**默认 `user_observable`（除非该 Journey 完全无 UI 介入，如 P6 SFX 自动选片，可能 `consumer_driven`）。
- **Module 卡**：
  - 后端 API endpoint + DB → `consumer_driven`（消费者 = playwright 经 API 触发的下游调用）
  - LLM Agent + prompt → `eval_based`（必须有 eval set + 阈值 + 基线）
  - 前端页面/组件 → `user_observable`（被父 Journey 的 playwright 触达）
  - 既是 LLM 又是数据（如 RequirementsAgent 既出 schema 又跑 LLM） → 同时声明 `eval_based` + `consumer_driven`，两种验证都跑

---

## 9. 迁移计划（实际操作步骤）

1. **归档旧 SPEC**（`[SPEC-ARCHIVE]` commit）
   - `git mv docs/specs/SPEC-{A..G}*.md docs/specs/_archive/`
   - 写 `docs/specs/_archive/README.md` 解释废弃原因 + 指向本设计文档
2. **保留并参考 SPEC-P0-JOURNEY**（已是 Journey-first 形态，作为模板）
3. **跑 prd-to-spec 工具**（自动化拆卡，#36 split-spec 方法论的执行层）
   - 输入：PRD v3.3 + Phase0需求.md（已有）+ §10.A-H BDD 段落
   - 输出：`tasks/SPEC-P1-JOURNEY/` ... `tasks/SPEC-P11-JOURNEY/` + `tasks/SPEC-LAYER-JOURNEY/`
4. **手工补全跨阶段 Journey**（J-L-001..004）— prd-to-spec 不一定能识别跨阶段闭环
5. **lint 脚本** `scripts/lint_task_cards.py`（split-spec 项目侧脚手架）
   - 检查 frontmatter `delivery_kind` / `evidence_type` / `parent_journey`
   - 检查 `shared: true` Module 必须有 `first_introduced_in`
6. **逐 Journey 实现**：每条 Journey 单独走 `superpowers:writing-plans` → `subagent-driven-development`

---

## 10. Definition of Done（本设计文档）

- [x] 所有 12 phases 都有 Journey 数预估
- [x] §10.A-H 8 个 BDD 簇都有落点
- [x] 前端代码归属规则明确（A/B/C 三模式）
- [x] 共享前端基础设施清单初稿
- [x] 跨切关注点引入策略明确
- [x] evidence_type 边界判定明确
- [x] 迁移步骤可执行
- [ ] **用户审阅本文档** ← 当前状态
- [ ] 用户批准 → 进入 prd-to-spec 自动拆卡阶段

---

## 11. 已知风险与开放问题

1. **prd-to-spec 工具是否支持 §10 BDD 段落作为补充输入？** 设计文档假设支持，需确认或手工补卡。
2. **Phase 5/6（BGM/SFX）的 Journey 数仍待 PRD 复读确认** — 当前估 2 卡，可能因"用户交互点"少而合并为 1。
3. **J-L-004 图表闭环跨阶段**会增加测试复杂度（playwright 需要驱动 P2 → P8 全链路）。可能需要 mock 中间阶段，仅断言端到端可观察结果。
4. **task_ledger 表是 P0 引入的 Module，但 P1+ 也用** — 需要在 lint 中允许"跨 Journey 引用"机制；现 split-spec 模板无此字段。
5. **§10.A 安全合规作为横切落地，不单独成 Journey** 的执行风险：需要在每个 LLM Module 的 acceptance 模板里强制嵌入"安全输出检查"项；漏一个就破窗。

---

## 12. 参考

- `~/Desktop/硅基员工/工作技能/拆分SPEC/SKILL.md` — 方法论
- `~/Desktop/硅基员工/工作技能/拆分SPEC/checklist.md` — 硬 checklist
- `~/Desktop/硅基员工/工作技能/prd-to-spec/SKILL.md` — 自动化执行层
- `tasks/SPEC-P0-JOURNEY/README.md` — 已存在的参考实现
- `docs/PRD_v3.3_Web交互式视频制作系统.md` — 拆分源
- `docs/Phase0需求.md` — Phase 0 详细规格（J-P0-* 的展开来源）
