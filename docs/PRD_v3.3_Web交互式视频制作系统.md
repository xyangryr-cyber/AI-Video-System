# Web 交互式视频制作系统 — 产品需求规格说明书 (PRD v3.3)

> **版本**: v3.3（含 v3.16-BDD 行为补丁集，2026-04-17）
> **日期**: 2026-04-15（v3.16-BDD 补丁追加于 2026-04-17）
> **Changelog（相对 v3.2）**: 整合 v2 12 阶段需求定义，移除版本对比内容，使文档自包含。
> **Changelog（v3.16-BDD 补丁，2026-04-17）**: 基于 `docs/BDD_DOC_GAP_AUDIT_2026-04-17.md` 行为审计补齐 8 类用户可见行为（AI 安全问答 / 统一 Claim 生命周期 / 阶段偏好 / 结构化插入 / 分镜锚点 / 图表闭环 / 阶段回看 / 质疑后增量重验），可执行规格见 `docs/specs/SPEC_REVISION_REQ_v3.16_2026-04-17.md`，所有补丁集中在 **第十部分**。本版 PRD 主体（§1-§9）保持稳定，新增/影响章节通过内嵌交叉引用指向第十部分。
> **定位**: 以 Web 网站为前端交互层，引入"项目化工作流 + 动态任务账本 (Task Ledger)"架构，对齐行业主流 Agent 编排最佳实践（Manus / Temporal / Microsoft task-ledger pattern）。

---

## 目录

- [第一部分：系统定位](#第一部分系统定位)
- [第二部分：阶段流转与业务规则](#第二部分阶段流转与业务规则)
- [第三部分：偏好提取与确认](#第三部分偏好提取与确认)
- [第四部分：项目与状态持久化（业务视角）](#第四部分项目与状态持久化业务视角)
- [第五部分：前端产品形态](#第五部分前端产品形态)
- [第六部分：意图识别与动作集](#第六部分意图识别与动作集)
- [第七部分：12 阶段工作流](#第七部分12-阶段工作流)
- [第八部分：事件流与过程透明化](#第八部分事件流与过程透明化)
- [第九部分：非功能需求](#第九部分非功能需求)
- [第十部分：v3.16-BDD 行为补丁集（2026-04-17）](#第十部分v316-bdd-行为补丁集2026-04-17)
- [附录：技术设计索引](#附录技术设计索引)

---

# 第一部分：系统定位

## 1.1 系统定位

为具备金融内容专业能力但不具备视频制作能力的内容创作者，提供一套"只需用自然语言描述需求，由 AI Agent 全权负责视频制作全流程"的 Web 工具。

用户在浏览器中打开系统首页，看到自己的项目列表，可以新建项目或打开已有项目。每个视频制作任务对应一个项目，每个项目走固定的 12 阶段工作流。每个阶段内，用户通过自然语言与 Agent 交互，Agent 识别意图并执行对应任务；阶段内所有任务完成后，用户确认进入下一阶段，由 Agent 主动引导下一步。

### 1.1.1 目标用户画像（v3.2 推定，V1.5 基于真实访谈修订）

- **角色**：金融行业自媒体创作者 / 投研内容输出者
- **经验**：3-10 年投研经验，日均阅读财报/研报 ≥ 2 份
- **当前视频产出频率**：0-1 次/周（受限于剪辑能力，而非内容能力）
- **技术水平**：熟练使用 Markdown、飞书、Notion；不会剪辑软件
- **使用环境**：桌面浏览器（Chrome/Edge），单次创作预期 30-60 分钟
- **核心痛点**：有输出欲望和专业内容，但被"把内容转成视频"这一步卡住
- **备注**：本画像为产品团队推定，V1 上线后基于真实使用数据在 V1.5 迭代

### 1.1.2 V1 交付标准（可量化）

| 指标 | 目标 |
|---|---|
| 交付成功率 | 90% 项目能产出可发布 MP4（时长 3-10 分钟） |
| 单项目耗时 | P50 ≤ 45 分钟，P90 ≤ 60 分钟（用户纯操作时间，不含 async 任务等待） |
| 单项目 LLM 成本 | P50 ≤ $8，P90 ≤ $15 |
| 首帧加载 | ≤ 3s |
| Router 意图识别准确率 | 在 100 条人工标注测试集上 ≥ 85% |
| Router P95 延迟 | ≤ 3s |

### 1.1.3 现阶段证据边界（v3.3）

- 本版 **不附录用户访谈摘要**；附录 A 延后到 V1.5，与真实使用日志一起补齐。
- 因此，§1.1.1 画像属于**产品团队推定画像**，仅用于 V1 收敛设计，不作为长期定论。
- V1 的目标不是证明"所有金融创作者都需要 12 阶段编排"，而是验证：**目标画像用户是否愿意把专业内容交给 Web 工作流转成可发布视频**。
- 若上线后连续 20 个项目中，< 30% 用户使用 `inject_subtask` 或 < 20% 用户接受 PreferenceExtractor 提取结果，则 V1.5 必须下调相关能力范围。

## 1.2 核心设计原则

| 编号 | 原则 | 说明 |
|---|---|---|
| P1 | 确定性骨架 + LLM 填充 | 12 阶段流转、门禁、任务调度由代码实现；LLM 只负责意图识别和内容生成 |
| P2 | Agent 完全无状态 | Router 和 Producer/Reviewer 每次调用都重建上下文，不依赖 LLM 记忆 |
| P3 | 状态外置于代码 | 所有项目状态存在 SQLite + 文件系统只读快照中，任何时候崩溃或新会话都能从权威状态恢复 |
| P4 | 过程透明化 | 前端必须能实时看到当前是哪个 Agent 在做什么任务，耗时多少，处于哪个阶段 |
| P5 | 阶段门禁强制 | 每个阶段推进必须通过产物完整性校验 + 用户显式确认 |
| P6 | 动态任务账本 | 阶段内的任务列表是动态可编辑的，支持用户插入子任务 |
| P7 | 项目隔离 | 不同项目的状态、产物、对话完全隔离在各自目录 |

---

# 第二部分：阶段流转与业务规则

> **技术实现索引**：系统分层架构、服务进程划分、存储选型等工程决策见 [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md)。Agent 编排模型（三层架构、Task Ledger 数据结构与生命周期、上下文注入规则、通用子任务 Agent 类型）的技术细节亦在 TECH_PLAN 中定义。

---

## 2.1 12 阶段流程

```
Phase 0 需求定义
  → Phase 1 内容主线
  → Phase 2 口播脚本(结构化)
  → Phase 3 口播脚本(润色)
  → Phase 4 人声旁白
  → Phase 5 背景音乐
  → Phase 6 音效设计
  → Phase 7 分镜脚本
  → Phase 8 关键画面渲染
  → Phase 9 B-Roll 素材准备
  → Phase 10 粗剪合成
  → Phase 11 精剪交付
```

**阶段转移规则**：
- **推进**：当前阶段 `task_ledger` 所有任务状态为 `done` + GateKeeper 校验通过 + 用户点击"确认进入下一阶段"按钮。
- **回退**：用户点击左侧阶段导航中任一已完成阶段 → 弹窗警告"回退到 Phase X 将使 Phase X+1 至当前阶段的产物变为 `invalidated` 状态（文件保留，DB 引用断开，可审计）并需要重做" → 用户确认 → FSM 将后续阶段 `phase.status = "invalidated"`、保留旧 `task_ledger` 快照到 `phase.history[]` 供审计、进入目标阶段。**目标阶段的 task_ledger 重新按 `phase_templates.json` 初始化（不恢复旧快照）**，`artifact_version` 从 0 重新自增；旧文件不删除。
- **跳过**：某些阶段（P5 BGM、P6 SFX 等）可被用户主动 `skip_phase`。跳过时 `phases[X].status = "skipped"`，**不初始化 task_ledger**（保持空），不产生主产物，GateKeeper 只校验"无进行中任务"和"偏好确认完成"两项后放行，最终产物元数据中标注被跳过的阶段。
- **跨阶段对话 turn 历史清空，但偏好层累积**：进入新阶段时，Router 的对话 turn 历史从空开始。但以下三层偏好始终注入 Router prompt：
  - `preferences.global_rules_md`（全局制作规范）
  - `preferences.user_preferences_md`（跨项目长期偏好）
  - `preferences.project_preferences_md`（当前项目滚动偏好，由 PreferenceExtractor 在每次过门禁时写入，见 §3.1）

### 阶段内任务概念

每个阶段包含一组动态可编辑的任务列表。任务类型包括：生成产物（`generate_artifact`）、局部修改（`user_revision` / `regenerate_section`）、审核（`review`）、调研/验证/交叉对比（`research` / `verify` / `cross_check`）。用户可通过对话插入子任务（见第六部分）。

任务状态流转和调度细节见 [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) 及 [`docs/specs/SPEC-D-pipeline-phases.md`](specs/SPEC-D-pipeline-phases.md)。

---

# 第三部分：偏好提取与确认

## 3.1 偏好提取与确认（Phase Gate PreferenceExtractor）

每次用户点击"确认进入下一阶段"时，在 GateKeeper 校验之前必须完成一次偏好提取与用户确认循环。这是门禁的一部分，跳过此步骤无法推进。

**非 ledger 任务**：PreferenceExtractor 不进入 `task_ledger`，而是由 API 层在 `POST /projects/{id}/advance` 处理器中同步调用一次，状态追踪在 `phases[current].preferences_confirmed_at` 字段。其 token 消耗计入**当前 phase** 的成本记录；调用记录写入 `agent_call_log` 表，`agent_name = "PreferenceExtractor"`；事件流（§8.1）发 `preference_extraction_started` / `preference_candidates_ready` / `preference_confirmed` 三种事件。V1 只做成本记录，不做成本熔断。

### 3.1.1 目标

从本阶段的用户对话、`user_revision` 任务指令、`regenerate` 原因中，显式抽取可复用的偏好规则（如"开头要直白不要学术腔""数据必须给出原始来源""不要使用背景音乐"），持久化到合适的层级：
- **项目内复用**：`preferences.project_preferences_md`
- **跨项目复用**：`preferences.user_preferences_md`
- **全局规范注入**：`preferences.global_rules_md`（部署方维护，PreferenceExtractor 只读）

**关键约束**：提取结果必须对用户可见、可编辑、可拒绝。未经用户确认的提取不写入 `preferences` 三字段；`snapshot.md` 仅在确认后由 DB 导出刷新。

### 3.1.2 触发与输入

触发：`POST /projects/{id}/advance` 第一次被调用时，如果本阶段还没完成过偏好确认（`phases[current].preferences_confirmed_at == null`），则先走此流程而非立即走 GateKeeper。

输入给 PreferenceExtractor Agent：
- 本阶段对话历史全文（`dialogue/phase_X.md`）
- 本阶段所有 `user_revision` 与 `regenerate` task 的指令和理由
- 本阶段起止时的产物 diff（`artifact_v1` vs `artifact_vN`）
- 当前已存在的 `preferences.user_preferences_md` 与 `preferences.project_preferences_md`（避免重复提取）

### 3.1.3 输出格式（严格 JSON）

```json
{
  "candidates": [
    {
      "id": "pref_001",
      "rule": "开头第一段不要引用学术论文，用身边故事代入",
      "scope_suggestion": "project",
      "evidence": [
        {"source": "dialogue/phase_2.md:L42", "quote": "这段太像论文了，换成咱小区大爷买金条那种"}
      ],
      "confidence": 0.9,
      "conflicts_with": []
    }
  ],
  "nothing_found": false,
  "summary_for_user": "我从本阶段的修改意见里提炼出 2 条偏好，请您确认是否保存。"
}
```

**硬约束**：
- `evidence` 字段不能为空，每条规则必须能溯源到具体对话或 task 指令。
- `confidence < 0.6` 的规则不允许出现在 candidates 中。
- 与现有 `preferences.user_preferences_md` / `preferences.project_preferences_md` 冲突的规则必须在 `conflicts_with` 中列出冲突条目并给出合并建议。
- 若无可提取偏好，输出 `nothing_found: true` 并给出空 candidates，**用户仍需点击一次"跳过"以完成门禁**（避免门禁被 Agent 偷偷放行）。

### 3.1.4 用户确认 UI

前端在对话区弹出"偏好确认卡片"（非模态，但阻塞 `confirm_next`）：

```
┌─ 本阶段学到的偏好（请确认） ─────────────────────┐
│ Agent 从你本阶段的反馈中总结了 2 条偏好：          │
│                                                 │
│ ☑ 1. 开头第一段不要引用学术论文，用身边故事代入    │
│    依据: "这段太像论文了..."                     │
│    保存范围: ( ) 仅本项目  ( ) 所有项目           │
│    [编辑]                                       │
│                                                 │
│ ☑ 2. 所有财经数据必须标注来源和统计口径           │
│    依据: "这组数据哪来的？..." (+1 条)           │
│    保存范围: ( ) 仅本项目  (•) 所有项目          │
│    [编辑]                                       │
│                                                 │
│ [全部接受]  [全部拒绝]  [保存勾选项并推进]        │
└─────────────────────────────────────────────┘
```

交互规则：
- 默认全部勾选，`scope` 按 Agent 建议预选
- 用户可对单条勾选 / 取消勾选 / 编辑文字 / 改变 scope
- "编辑"打开内联文本框，保存后覆盖 rule 字段
- "全部拒绝"直接完成确认动作（记录到 DB 但不落盘到偏好文件），不阻塞门禁
- "保存勾选项并推进"→ 勾选项按 scope 写入 SQLite `preferences` 表的对应字段块，并刷新只读 `snapshot.md` → `phases[current].preferences_confirmed_at = now()` → 释放 GateKeeper

### 3.1.5 持久化与复用

**DB `preferences` 表字段（V1 收敛版）**：
```
project_id | global_rules_md | user_preferences_md | project_preferences_md |
last_candidates_json | last_confirmed_at | updated_at
```

**只读快照文件**：
- 每次确认后，API 从 SQLite 生成 `data/projects/{id}/snapshot.md`
- `snapshot.md` 固定包含三段：全局规范 / 跨项目偏好 / 本项目偏好
- 文件只读，不支持手工回写 DB

**复用时机**：
- Router 每次调用时，按 `global_rules_md + user_preferences_md + project_preferences_md` 顺序注入
- 制作 Agent 的 `{user_preferences}` 槽位同样注入这三段合并结果
- 新建项目时，`global_rules_md` 与 `user_preferences_md` 自动继承；`project_preferences_md` 从空开始

### 3.1.6 可撤销与审计

- 用户在设置页可查看 `snapshot.md` 的最近 20 次导出版本，支持回滚到上一版 DB 内容
- SQLite `preferences` 表保留最近一次候选集与最后确认时间；完整历史进入 `agent_call_log` 与事件流
- 支持在后续阶段"追溯拒绝"：即使一条偏好之前被接受，也可在新阶段的确认卡片上看到并选择撤销

---

# 第四部分：项目与状态持久化（业务视角）

> **技术实现索引**：目录结构、`project_state.json` 完整 Schema、SQLite 表 DDL 见 [`docs/specs/SPEC-A-contracts.md`](specs/SPEC-A-contracts.md)。存储分层（SQLite 权威 / 文件系统 / 只读导出）的技术细节见 [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md)。

## 4.1 存储分层

| 数据 | 存储 | 权威性 | 理由 |
|---|---|---|---|
| 项目列表、项目元数据 | SQLite `projects` | **权威** | 支持查询、筛选、排序 |
| 阶段状态与 task_ledger | SQLite `phases`、`task_ledger` | **权威** | 消除双写歧义；V1 不做多 tab 并发写入 |
| async_tasks 队列和索引 | SQLite `async_tasks` | **权威** | 支持单 worker 顺序调度 |
| 事件流归档 | SQLite `events`（单表） | **权威** | 支持按项目/时间查询；V1 不做分区 |
| Agent 调用审计 | SQLite `agent_call_log` | **权威** | 审计、成本分析、回放；敏感字段脱敏后入库（见 §11） |
| 偏好闭环状态 | SQLite `preferences` 表 | **权威** | 三字段承载全局规范/跨项目偏好/项目偏好；`snapshot.md` 只读导出 |
| 媒体产物（脚本 md / 音频 / 图片 / 视频 / 渲染中间文件） | 文件系统 `data/projects/{id}/phase_X/` | **权威**（DB 仅存相对路径 `artifact_ref`） | 大文件不适合入库；路径抽象层便于未来迁移对象存储 |
| 对话历史（按阶段分文件） | 文件系统 md | 权威（纯文本日志） | 便于调试和审计 |
| `snapshot.md` / `project_state.json` | 文件系统 | **只读导出**（非权威） | 由 API 按需从 SQLite 生成；不参与写路径 |
| **全局 API Key 与敏感配置** | `.env`（Docker Compose 注入） | 权威 | 符合运维惯例、便于轮换、不进 git |
| 非敏感模型配置（模型名/endpoint/超时/重试） | `data/config/model_config.json` | 权威 | 全局共享、可版本化 |
| 应用日志 | `data/logs/{api,worker}/YYYY-MM-DD.log` | 权威 | 便于 grep 和工单排障 |

**写路径**：所有结构化状态只写 SQLite。媒体产物按"先写文件 → 再提交 `artifact_ref`"的顺序；提交失败时清理孤儿文件。V1 不支持文件反向写回 DB。

**读路径**：前端查询走 SQLite。`project_state.json` 与 `snapshot.md` 由 API 导出，调试/离线场景使用，不进入热路径。

**字段权威源表（消除歧义）**：
- `phases[].status` / `phases[].task_ledger` / `async_tasks` / `preferences` / `events`：**SQLite 权威**
- 媒体产物文件 / 对话 md：**文件权威**
- `snapshot.md` / `project_state.json`：**导出视图，非权威**
- 两侧不存在同一字段双写。

**恢复策略**：SQLite 是唯一可信状态源。DB 文件异常时从 `data/db/app.sqlite3.bak` 恢复；不从 `project_state.json` 或 `snapshot.md` 反向恢复。

**API 配置全局化**：私有化部署场景下，API Key 本质属于部署方资源，所有项目共享同一份全局配置，通过 `.env` + `model_config.json` 两文件管理（敏感 / 非敏感分离）。

**并发控制**：V1 约定单项目单 tab 编辑。前端检测到同项目第二个编辑页时，显示"请回到原 tab 继续创作"；不实现乐观锁冲突重试。

**成本记录**：`agent_call_log` 按 `project_id` 和 `phase` 聚合 token 成本，默认展示项目累计成本、阶段累计成本和单次调用成本；V1 不做自动熔断，只做记录与告警。

**Worker 调度**：V1 单 worker 顺序执行 async_task，出队顺序为 `created_at ASC`；同一时刻只运行 1 个长任务，避免 SQLite 锁争用。V1.5 再评估是否扩为 worker 池。

**敏感字段脱敏**：`agent_call_log.prompt` / `response` 入库前由中间件扫描并脱敏 `sk-*` / `API_KEY=*` / `Bearer *` 等常见密钥 pattern；长文本超过 8KB 摘要化存储（保留首尾 2KB + MD5 hash）。

## 4.2 状态恢复流程

**触发场景**：浏览器关闭后重开 / 服务重启 / Worker 崩溃重启。

```
前端请求 GET /projects/{id}/state
  │
  ▼
API 读取 SQLite 权威状态
  │
  ▼
从 SQLite 合并 async_tasks 最新状态
  │
  ▼
返回完整状态给前端
  │
  ▼
前端渲染:
  - 阶段导航高亮到 current_phase
  - 产物预览区加载 phases[current].artifact_ref
  - 任务清单面板渲染 task_ledger.tasks
  - Agent 活动流订阅 WebSocket 增量事件
  - 对话区加载 dialogue/phase_X.md
```

**不需要 Agent 参与恢复**——所有状态都在 SQLite 里。

---

# 第五部分：前端产品形态

## 5.1 页面结构

| 路由 | 页面 | 功能 |
|---|---|---|
| `/` | 项目列表页 | 显示所有项目，入口"+ 新建项目" |
| `/projects/new` | 新建项目向导 | 极简单页表单（标题 + 自然语言描述主题），提交后创建项目并跳转到工作流 |
| `/projects/{id}` | 项目工作流页 | 双栏布局，阶段导航 + 产物 + 对话 + 任务清单 + Agent 活动流 |
| `/settings` | 设置页 | API 配置、用户画像查看/编辑、全局规范 |

## 5.2 项目列表页

### 5.2.1 布局

```
┌──────────────────────────────────────────────────────────────┐
│ 视频制作系统                          [+ 新建项目]  [设置]     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 标题              │分类      │阶段      │进度│状态│更新时间│ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │ 黄金价格走势分析    │行业分析   │Phase 2  │██░░│进行中│10分钟前│ │
│ │ 十五五规划解读      │政策解读   │Phase 1  │█░░░│等用户│2小时前 │ │
│ │ 美联储加息影响      │时事解读   │Phase 11 │████│完成  │昨天   │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 5.2.2 字段

| 字段 | 说明 |
|---|---|
| 标题 | 项目标题，点击进入工作流页 |
| 分类 | 二层分类名 |
| 当前阶段 | Phase 0 ~ Phase 11 |
| 进度条 | 已完成阶段数 / 12 的可视化 |
| 状态 | 进行中 / 等待用户 / 已完成 / 失败 |
| 创建时间 | - |
| 最后更新时间 | 相对时间（"10 分钟前"） |

### 5.2.3 交互

- **点击行** → 进入 `/projects/{id}`
- **+ 新建项目** → 进入 `/projects/new`，输入标题和描述后后端立即初始化项目，跳转工作流 Phase 0

不提供筛选、搜索、分组、项目模板、克隆功能。

## 5.3 项目工作流页（双栏布局）

### 5.3.1 整体布局

```
┌────────┬─────────────────────────────────┬─────────────────┐
│阶段导航 │      当前阶段产物预览区          │ 右侧信息栏       │
│        │                                 │                 │
│  P0    │  ┌─ [脚本文本 / 音频 / 图片 /   │ ┌─项目元信息─┐  │
│  P1    │  │   视频 / JSON 视图]        │ │ 标题        │  │
│  P2    │  │                             │ │ 分类        │  │
│  P3    │  │                             │ │ 时长/平台   │  │
│  P4    │  └─────────────────────────────┘ │ └───────────┘  │
│  P5    │                                 │                 │
│  P6    ├─────────────────────────────────┤ ┌─任务清单─────┐ │
│  P7    │  ┌─ 当前阶段任务清单 ──────────┐ │ │             │ │
│  P8    │  │ [x] 生成脚本初版            │ │ │ (task_ledger)│ │
│  P9    │  │ [x] 事实核查 PASS           │ │ └───────────┘  │
│  P10   │  │ [ ] 用户修改:"更口语化"     │ │                 │
│  P11   │  │ [...] 调研:黄金ETF资金流    │ │ ┌─Agent 活动流┐ │
│        │  └─────────────────────────────┘ │ │ [实时事件]  │ │
│        │  ┌─ Agent 对话区 ──────────────┐ │ │             │ │
│        │  │ Agent: 脚本第一版已生成...  │ │ └───────────┘  │
│        │  │ User: 更口语化              │ │                 │
│        │  │ Agent: 已修改...            │ │                 │
│        │  │ [输入框]                    │ │                 │
│        │  │ [确认进入下一阶段 -> PhaseN]│ │                 │
│        │  └─────────────────────────────┘ │                 │
└────────┴─────────────────────────────────┴─────────────────┘
```

### 5.3.2 左侧阶段导航

- 12 个阶段固定列表
- 图标规则：已完成 / 当前进行中 / 未开始
- 点击已完成阶段 → 弹窗警告 → 确认后回退
- 点击未开始阶段 → 不响应（禁用）

### 5.3.3 中间上半：当前阶段产物预览区

根据阶段产物类型动态渲染组件：

| 阶段 | 产物类型 | 预览组件 |
|---|---|---|
| P0 需求 | JSON | 结构化表单视图 |
| P1 大纲 | Markdown | 富文本渲染 |
| P2 脚本结构化 | Markdown + 段落表 | 分段可折叠视图 |
| P3 脚本润色 | Markdown | 富文本渲染 |
| P4 人声旁白 | 音频 .mp3 | 分段音频播放器，每段可单独播放 |
| P5 BGM | 音频 .mp3 | 波形 + 播放器 |
| P6 音效 | 音频 .mp3 | 按触发点列表播放 |
| P7 分镜 | JSON | 分镜卡片画廊 |
| P8 关键帧 | 图片 PNG | 网格画廊 + 点击放大 |
| P9 B-Roll | 图片/视频片段 | 缩略图画廊 |
| P10 粗剪 | 视频 mp4 | 内嵌播放器 |
| P11 精剪 | 视频 mp4 + 封面 | 内嵌播放器 + 下载按钮 |

### 5.3.4 中间下半：任务清单 + 对话区

- **任务清单**：实时渲染 `task_ledger.tasks`，每项显示状态图标 + 名称 + 进度（长任务显示百分比）
- **对话区**：流式显示 Agent 回复（打字机效果）
- **输入框**：自然语言输入，回车提交
- **确认按钮**：固定在对话区底部，显示"确认进入下一阶段 → Phase N+1"；点击触发 GateKeeper 校验，通过则推进，失败则弹窗提示失败原因

### 5.3.5 右侧信息栏

三个区块从上到下：
1. **项目元信息**：标题、分类、目标时长、发布平台、当前参数（只读）
2. **任务清单副本**：重复显示 task_ledger，方便中间区域被产物占满时仍可见
3. **Agent 活动流**：实时推送的事件流，每条事件一行：`[时间] [Agent名] [动作] [结果/进度]`

### 5.3.6 长任务进度展示

当 task_ledger 中出现 `async_job_id` 的任务（TTS / 渲染 / 合成）时：
- 任务清单项显示进度条（如 40%）
- Agent 活动流实时更新进度事件
- 用户关闭浏览器后，worker 继续执行，重新打开时自动从 SQLite 状态恢复最新进度

### 5.3.7 数据验证面板

> **v3.16-BDD 升级（2026-04-17）**：本面板在 v3.16 升级为「Claim 工作台」（详见 §10.B）。Claim 来源不再仅限 P2 ScriptAgent，新增 P7 / P8 / P9 / 用户补充；新增筛选维度（来源阶段 / 验证状态 / 阻断级别 / claim 类型）和操作（质疑 / 补充关联 / 查看证据 / 接受人工覆盖）；未验证 hard claim 阻断 P8 渲染、P10 合成、P11 终审。本节描述的字段与状态定义保持兼容（`key_data_point.data_point_id` → `claim_id`）。

工作流页右侧信息栏（或中间产物区 tab）增加"数据验证"面板，展示当前脚本中所有可验证数据点（`key_data_points`）的全生命周期状态：

- **展示内容**：每条数据点显示：数据声明（claim）| 数据值（value + unit）| 来源（source）| 信任等级（trust_level）| 验证状态（pending / verified / failed / stale）| 核查时间
- **状态含义**：
  - `verified`（绿）：trust_level 为 user_verified 或 source_verified，且对应脚本段落未变更
  - `pending`（黄）：trust_level 为 llm_generated，尚未验证
  - `failed`（红）：DataVerifyAgent 返回 verdict=refuted
  - `stale`（灰）：数据点对应的脚本段落已更新（user_revision / regenerate），原验证结果失效
- **用户操作**：
  - 点击 [验证] → 触发 verify 子任务（DataVerifyAgent）
  - 点击 [手动确认] → 用户标记为 user_verified（适用于用户自身能确认的数据）
  - 点击数据行 → 展开核查详情（来源 URL、比对结论、验证时间）
- **与门禁的关系**：面板状态不直接阻塞门禁，但 Gate-P2 中 FactChecker 的 trust_level=llm_generated 未确认数据点仍按原有规则阻塞
│   └── model_config.json           # 全局非敏感模型配置（模型名/endpoint/timeout）
│
├── users/
│   └── user_default/
│       └── (保留目录，占位；V1 偏好权威已迁入 SQLite)
│
├── projects/
│   └── proj_20260415_001/
│       ├── project_state.json      # 只读物化视图（按需导出，非权威）
│       ├── snapshot.md             # 偏好三字段只读快照
│       ├── dialogue/
│       │   ├── phase_0.md
│       │   └── ...
│       ├── phase_0/
│       │   ├── requirements.json
│       │   └── subtasks/           # 子任务过程记录
│       ├── phase_1/
│       │   ├── outline_v1.md
│       │   └── outline_v2.md
│       ├── phase_2/
│       │   ├── script_v1.md
│       │   └── script_v2.md
│       ├── phase_4/narration_seg_01.mp3
│       ├── phase_8/keyframe_01.png
│       ├── phase_10/rough_cut.mp4
│       └── phase_11/final.mp4
│
├── logs/
│   ├── api/2026-04-15.log
│   └── worker/2026-04-15.log
│
# 第六部分：意图识别与动作集

## 6.1 动作集

| 动作 | 触发方式 | 由谁识别 | 后续行为 |
|---|---|---|---|
| `revise` | 用户对话 | IntentRouter | 追加 `user_revision` task 到账本 |
| `regenerate` | 用户对话 | IntentRouter | 追加 `regenerate_section` 或 `generate_artifact` task |
| `inject_subtask` | 用户对话 | IntentRouter | 追加 `research` / `verify` / `cross_check` task |
| `request_advance` | 用户对话（如"好了，下一步"） | IntentRouter | 前端高亮"确认进入下一阶段"按钮；若当前阶段仍有未完成主产物或未确认偏好，按钮保持禁用态并显示原因 |
| `skip_phase` | 用户对话（如"跳过这一阶段"）或硬按钮 | IntentRouter 或前端 | 标记 `phases[X].status = skipped`，仍走 GateKeeper 的跳过分支 |
| `confirm_next` | 硬按钮 | 前端直接调 API | 触发 PreferenceExtractor → 用户确认 → GateKeeper → 推进 Phase（见 §3.1 + §6.3） |

额外辅助动作：
- `clarify`：Router 无法识别意图时输出，前端显示澄清问题，不改动账本；若同一用户输入连续 2 轮都落入 `clarify`，前端必须展示 4 个候选动作按钮（`revise` / `regenerate` / `inject_subtask` / `skip_phase`）

> **v3.16-BDD 扩展（2026-04-17）**：本动作集新增 6 类 BDD 驱动动作，详见 §10.E：
> - `challenge_claim`：用户对某条 claim 提出质疑（→ §10.B + §10.C）
> - `supplement_claim`：用户补充新事实/数据（→ §10.B + §10.C）
> - `request_chart`：用户请求生成图表，进入 5 步状态机（→ §10.H）
> - `view_phase_detail`：打开任一已完成阶段的完整快照（→ §10.F）
> - `save_stage_preference`：保存阶段级偏好（含生成后回写）（→ §10.D）
> - `insert_section`：在已有产物中局部插入新段落，最小改动（→ §10.E）
>
> SafetyGuard 在 IntentRouter **之前**硬拦截：命中政治敏感 / 违法 / 隐私 / 版权 / 未验证投资建议时，直接返回模板话术并写审计日志，**不进入** action 路由（详见 §10.A）。

## 6.2 动作示例

### revise

```
用户: "把开头改得更直白一点"
Router 输出:
{
  "action": "revise",
  "params": {
    "target": "opening",
    "instruction": "开头改得更直白"
  },
  "reply_to_user": "好的，我让脚本生成 Agent 把开头段改得更直白，稍等。"
}
→ WorkflowEngine 追加:
  { id: t_000123, type: "user_revision", params: {...}, status: "pending" }
→ Dispatcher 调度对应 Producer Agent 执行
```

### regenerate

```
用户: "这版大纲不对，整体重做"
Router 输出:
{
  "action": "regenerate",
  "params": {"scope": "full"},
  "reply_to_user": "明白，我重新生成一版大纲。"
}
→ 废弃当前 artifact，追加新的 generate_artifact task
```

### inject_subtask

```
用户: "先帮我调研一下 2025 Q4 黄金 ETF 的资金流向数据"
Router 输出:
{
  "action": "inject_subtask",
  "params": {
    "subtask_type": "research",
    "query": "2025 Q4 黄金 ETF 全球资金流向数据，包含 SPDR、iShares 等主要基金"
  },
  "reply_to_user": "好的，已创建 research 子任务；SLA 为 180 秒，若超时会提示重试。"
}
→ WorkflowEngine 追加 research task → Dispatcher 调度 ResearchAgent
→ 完成后结果写入 task.result_ref，在下一轮 Router 调用时注入上下文
```

### confirm_next

```
用户点击"确认进入 Phase 3"按钮
→ 前端直接调 POST /projects/{id}/advance
→ API 层: GateKeeper.check(current_phase)
  ├─ 通过 → FSM.transition(phase_3) → 初始化 phase_3 task_ledger → 返回新状态
  └─ 失败 → 返回失败原因列表 → 前端弹窗显示
```

## 6.3 门禁 GateKeeper 规则

每个阶段的推进必须通过以下校验。**本阶段被 `skip_phase` 跳过时，只校验「无进行中任务」和「偏好确认完成」两项**。

| 校验项 | 规则 |
|---|---|
| 主产物存在 | `phases[current].artifact_ref` 指向的文件存在且非空。若所有 `generate_artifact` 重试均失败导致 artifact_ref 为空，门禁直接阻塞，前端显示"主产物生成失败，请手动重试或调整参数" |
| 主产物与最新 review 版本一致 | `artifact_version == latest_review.target_version` 且该 review `status=succeeded`。任何 `generate_artifact` / `regenerate_section` / `user_revision` 完成后会让 `artifact_version` 自增，并自动追加匹配新版本的 `review` task，旧 review 置 `superseded` |
| 主产物审核通过 | 最后一个 `review` task 的 `verdict = PASS`。V1 只保留二元 verdict：`PASS` / `FAIL`；warning 进入 `review.notes[]`，但不单独形成第三态 |
| 无进行中任务 | task_ledger 中所有 task 状态为 `succeeded` / `failed` / `skipped` / `superseded`；若存在 `pending` / `queued` / `running` / `timeout` 则阻塞 |
| 无进行中异步任务 | `async_tasks` 中无 `status == "running"` 的项 |
| **偏好提取与确认完成** | 本次推进前必须完成一次 PreferenceExtractor，且用户已对提取结果做出确认动作（接受/修改/放弃），见 §3.1 |
| 成本已记录 | 当前 `phase` 和 `project` 的 token 成本已成功写入 `agent_call_log`；不作为阻塞条件 |

### 6.3.1 Reviewer 二元 verdict 判定清单（V1）

| Reviewer 类别 | PASS 条件 | FAIL 条件 |
|---|---|---|
| Completeness / Structure | 必填字段齐全；阻塞问题数 = 0 | 缺少任一必填字段，或阻塞问题数 >= 1 |
| FactChecker / DataVerify | 未核实关键事实数 = 0；来源缺失数 = 0 | 任一关键事实未核实，或任一核心数据缺少来源 |
| Style / MusicFit / SFX | 禁止项命中数 = 0 | 命中任一禁止项（如风格跑偏、侵入式 BGM、音效遮挡口播） |
| AudioQuality | 文案错字数 = 0；削波段数 = 0；峰值超限段数 = 0 | 任一项 > 0 |
| Visual / Storyboard / BRollFit | 遮挡关键信息帧数 = 0；错图数 = 0；版权阻塞素材数 = 0 | 任一项 > 0 |
| AVSync / Final | 口播画面错位 > 12 帧的片段数 = 0；导出失败次数 = 0 | 任一项 > 0 |

> `review.notes[]` 允许记录 warning，但 warning 不改变 verdict；V1 门禁只看 PASS / FAIL。


---

# 第七部分：12 阶段工作流

**每个阶段共享的门禁流程**（不在各节重复列出）：每次 `confirm_next` 在 GateKeeper 之前都会调用一次 **PreferenceExtractor**，提取结果经用户确认后写入 `preferences` 表，并刷新 `snapshot.md`（详见 §3.1）。

**Phase 模板权威来源**：所有阶段的 `initial_tasks` 定义统一放在 `data/config/phase_templates.json`（schema 见 [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md)），本节表格中的"默认账本初始任务"只是摘要说明，实现以该 JSON 文件为准。

**通用制作 Agent 系统提示词模板**：

```
你是视频制作团队的 {role_name}。你的任务是：
{task_description}

输入材料：
{input_artifacts}

输出要求（严格 JSON Schema）：
{output_schema}

用户偏好规则：
{user_preferences}

质量标准：
{quality_criteria}

禁止事项：
- 不要与用户直接交互
- 不要修改上一阶段已锁定的内容
- 不要编造数据或来源
```

**通用审核 Agent 系统提示词模板**：

```
你是视频制作质量审核专家（{reviewer_role}）。你的任务是：
根据以下审核清单，对输入产物做二元判定：PASS 或 FAIL。

审核清单：
{review_checklist}

输入产物：
{artifact}

输出格式（严格 JSON）：
{
  "verdict": "PASS" | "FAIL",
  "notes": ["warning 或 fail 原因列表"],
  "blocking_issues": ["仅列出导致 FAIL 的项"]
}
```

## 7.1 总览

> **v3.17-AudioMaster + P7A 增强（2026-04-17）**：在 12 阶段之间以"子阶段"形式插入 P7A，不做全局重编号。P4/P5/P6 交付升级为"分段 + 主音频"双层产物（见 §7.6 / §7.7 / §7.8）。

| 阶段 | 名称 | Producer | Reviewer | 默认账本初始任务 |
|---|---|---|---|---|
| P0 | 需求定义 | RequirementsAgent | CompletenessReviewer | generate_artifact → review |
| P1 | 内容主线 | OutlineAgent | StructureReviewer | generate_artifact → review |
| P2 | 口播脚本（结构化） | ScriptAgent | FactChecker + StructureReviewer | generate_artifact → review |
| P3 | 口播脚本（润色） | PolishAgent | StyleReviewer | generate_artifact → review |
| P4 | 人声旁白（分段 + `narration_master`） | TTSAgent（异步） + NarrationMasterAssembler | AudioQualityReviewer | generate_artifact (async) → assemble_master → review |
| P5 | 背景音乐（候选 BGM + 混音预览 + `bgm_mix_master`） | BGMAgent + AudioMixPreviewService + BgmMixRenderer | MusicFitReviewer（+ 全局和谐度） | generate_artifact → mix_preview → review |
| P6 | 音效设计（全文布局 + 编号片段 + `final_audio_with_bgm_sfx`） | SFXAgent（双步） + SfxSegmentMixService + FinalAudioAssembler | SfxLayoutReviewer + SfxMixReviewer | plan_layout → user_confirm → mix_segments → assemble_final → review |
| P7 | 分镜脚本 | StoryboardAgent | StoryboardReviewer | generate_artifact → review |
| **P7A** | **分镜脚本物料补充（v3.17 新增）** | StoryboardAssetPlanner + MaterialFetcher + MaterialVerifier | MaterialReadinessReviewer | plan_manifest → fetch → verify → bind → review |
| P8 | 关键画面渲染 | KeyframeRenderAgent（异步，严格消费 P7A） | VisualReviewer | material_readiness_check → generate_artifact (async) → review |
| P9 | B-Roll 素材准备 | BRollAgent | BRollFitReviewer | generate_artifact → review |
| P10 | 粗剪合成 | RoughCutAgent（异步） | AVSyncReviewer | generate_artifact (async) → review |
| P11 | 精剪交付 | FinalCutAgent（异步） | FinalReviewer | generate_artifact (async) → review |

### 7.1.1 核心阶段场景卡片

| 阶段 | 触发条件 | 前置条件 | 用户动作 | 期望结果 | 失败路径 / 边界处理 |
|---|---|---|---|---|---|
| P0 需求定义 | 新建项目 | 标题 + ≥300 字描述已提交 | 用户创建项目 | 产出 `requirements.json` | 描述 <300 字 → 要求补充；连续 5 次 revise 仍不满意 → 提示改写输入而非继续 regenerate |
| P1 内容主线 | P0 PASS | `requirements.json` 存在 | 用户确认进入 P1 | 产出主线大纲 | 连续 5 次 regenerate 不满意 → 建议回到 P0 改需求，不允许无限重试 |
| P2 结构化脚本 | P1 PASS | 主线大纲存在 | 用户修改/重生脚本 | 产出结构化脚本 | 关键事实缺来源 → FAIL；研究子任务失败可重试 1 次，否则提示人工补充来源 |
| P3 润色脚本 | P2 PASS | 结构化脚本 PASS | 用户要求更口语/更简洁 | 产出润色稿 | 连续 5 次润色不满意 → 建议冻结版本并进入人工编辑模式 |
| P4 人声旁白 | P3 PASS | 润色稿锁定 | 用户发起 TTS + 通听完整旁白 | 产出分段 + `narration_master.mp3` 完整可下载旁白 | TTS 失败/削波 / 主文件拼接校验失败 → FAIL；关浏览器后次日回来需在 10s 内恢复进度，否则标红重试 |
| P5 背景音乐 | P4 PASS 或 skip | `narration_master` 存在或显式跳过 | 用户在"人声 + BGM"混音预览上接受/跳过 | 产出 `bgm_mix_master.mp3` 完整混音或 skip | 若命中版权阻塞音乐 → 自动换源 1 次；仍失败则建议 skip；全局和谐度 FAIL → 重选 |
| P6 音效设计 | P5 PASS 或 skip | 主音频基线锁定（`bgm_mix_master` 或 `narration_master`） | 先确认全文音效布局，再逐段试听加工结果 | 产出 `final_audio_with_bgm_sfx.mp3` 完整最终音频或 skip | 布局不合规 → Layout FAIL；加工后片段遮挡口播 → Mix FAIL；连续 3 次失败后建议 skip |
| P7 分镜脚本 | P6 PASS/skip | 脚本、最终音频已锁定 | 用户确认分镜 | 产出分镜稿 | 关键镜头与脚本不对应 → FAIL；回退到 P2 时 P3-P7 全部 invalidated |
| **P7A 分镜物料补充（新增）** | P7 PASS | 分镜稿存在 | 用户审核物料清单、时间范围、axis_spec | 产出 `material_manifest.json` + `shot_material_bindings.json` + `chart_materials/` | 必需物料验证失败 → 阻塞 P8；图表时间范围不合理 → 回炉重抓 |
| P8 关键画面渲染 | **P7A PASS** | 分镜稿 + verified 物料绑定 | 用户启动渲染 | 产出关键帧 | `material_missing` / `material_unverified` → 事实阻塞回跳 P7A；`render_failed` → 工程降级不阻塞 |
| P9 B-Roll 素材准备 | P8 PASS | 关键帧存在 | 用户补素材 | 产出素材清单 | 素材版权阻塞 → 自动换源 1 次；仍失败则列出缺口并允许继续但最终 Reviewer 必须 FAIL |
| P10 粗剪合成 | P9 PASS | 音视频素材齐备 | 用户启动粗剪 | 产出 rough cut | 任一关键素材缺失或损坏 → FAIL；断线重连后 5s 内恢复进度 |
| P11 精剪交付 | P10 PASS | rough cut PASS | 用户发起最终导出 | 产出可发布 MP4 | 导出失败 2 次后停止自动重试；若回退到 P2，则 P3-P11 全部 invalidated 且弹窗显示预计需重做 30-45 分钟 |

---

## 7.2 Phase 0: 需求定义

### 7.2.1 目标与交付物

产出结构化需求 JSON，写入 `project_state.json` 的 `phases.phase_0.artifact_ref`，具体文件路径为 `phase_0/requirements.json`。

### 7.2.2 触发条件与输入

用户在 `/projects/new` 输入标题和自然语言描述（≥10 字）后提交，系统初始化项目并进入 Phase 0。

### 7.2.3 制作 Agent 职责（RequirementsAgent）
将用户输入的标题、用户自然语言描述注入系统提示词

**制作 Agent 系统提示词**：

```
你是视频制作团队的制作Agent。你的任务是：
**核心生成逻辑**：
- 将用户的自然语言描述转化为结构化视频制作需求
- 从用户描述中提取：视频主题、核心观点/内容框架、时长偏好（short/medium/long）、发布平台
- 自动补全技术参数：根据平台推断分辨率/码率/格式；根据内容分析确定视频分类（二级分类）；根据时长偏好和语速计算目标字数范围（默认语速 240 字/分钟）；根据分类匹配叙事结构模板

以下是具体内容：
视频标题：（将用户输入的视频标题注入）
视频框架：（将用户输入的自然语言描述注入）

用户偏好规则：
（从用户偏好配置文件中获取后注入）

输出要求：

**输出 Schema 核心字段**：
```json
{
  "project_id": "proj_YYYYMMDD_NNN",
  "title": "视频标题",
  "topic": "视频主题描述",
  "user_input_content": "用户输入的核心内容/观点",
  "duration_class": "short|medium|long",
  "target_duration_minutes": 10,
  "target_word_count": {"min": 1920, "max": 2880},
  "platform": {
    "primary": "bilibili",
    "secondary": ["douyin"],
    "specs": {"resolution": "1920x1080", "bitrate": "8Mbps", "format": "H.264 MP4"}
  },
  "category": {"level1": "金融财经", "level2": "行业分析"},
  "narrative_template": "NR-002-市场分析",
  "created_at": "..."
}
```

制作完成后触发审核Agent的审核
### 7.2.4 审核 Agent 职责（CompletenessReviewer）

| 检查项 | 校验规则 | FAIL 条件 |
|--------|---------|---------|
| 主题 | 非空，长度 ≥ 5 字符 | 空或过于模糊 |
| 用户输入内容 | 非空，包含至少一个可识别的观点或论点 | 空 |
| 时长分类 | 为 short/medium/long 之一 | 无效值 |
| 目标字数 | min > 0 且 max > min 且 max ≤ 100000 | 范围异常 |
| 平台 | 至少一个主平台，且在支持列表中 | 未知平台 |
| 视频规格 | resolution/bitrate/format 均非空 | 缺失 |
| 分类 | level1 和 level2 均非空，且在分类体系中存在 | 无效分类 |
| 叙事模板 | 在叙事结构库中存在 | 模板不存在 |

### 7.2.5 用户交互点

生成完成后，Agent 在对话区以自然语言呈现结构化需求摘要（含视频主题、核心内容、目标时长、发布平台、视频类型、叙事结构、技术参数），请用户确认。

- `revise`：修改任何字段（如"把目标时长改成 15 分钟"）→ 追加 `user_revision` task → RequirementsAgent 重新生成
- `regenerate`：整体重新生成需求分析
- `inject_subtask`：可插入 research 子任务（通常不常用于 P0）
- `confirm_next`：用户确认需求无误，触发 PreferenceExtractor + GateKeeper

### 7.2.6 Gate 0 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | `phase_0/requirements.json` 存在且 JSON Schema 校验通过（所有必填字段非空） |
| 审核通过 | CompletenessReviewer 返回 `verdict = PASS` |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_0.preferences_confirmed_at` 非空 |






## 7.3 Phase 1: 内容主线（大纲生成）

### 7.3.1 目标与交付物

产出选定的内容大纲（含 2-3 个版本供用户选择，最终选定 1 个），写入 `phase_1/outline_vN.md`，`artifact_ref` 指向选中版本。

### 7.3.2 触发条件与输入

Gate 0 通过后自动进入。输入：`phase_0/requirements.json`（结构化需求）+ preferences 三字段 + 叙事结构模板。

### 7.3.3 制作 Agent 职责（OutlineAgent）

**核心生成逻辑**：
1. 论证分析：评估用户核心观点是否足以支撑主题，识别逻辑链缺口并建议补充观点
2. 大纲生成：生成 2-3 个不同结构风格的大纲版本，每个版本包含：开头设计（类型 + 具体做法 + 预期时长占比）、主体观点列表（每观点含标题/核心论据/支撑数据/时长占比/过渡说明）、结尾设计、吸引力设计说明
3. 版本差异维度：版本 A 时间线/逻辑线正序；版本 B 反直觉/悬念倒叙；版本 C 用户痛点切入

**关键约束**：
- 不同版本在开头类型或主体编排上必须有实质差异
- 所有版本 duration_ratio 之和 = 1.0（±0.05）
- 每个观点至少有 1 条 supporting_data
- estimated_word_count 在目标字数范围内

### 7.3.4 审核 Agent 职责（StructureReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 版本数量 | 2-3 个版本 |
| 结构完整性 | 每版本都有 opening + body(≥2节) + closing |
| 时长占比 | 所有 section 的 duration_ratio 之和 = 1.0 (±0.05) |
| 需求覆盖 | Phase 0 用户输入的所有核心观点在至少一个版本中被覆盖 |
| 逻辑连贯 | 每个 section 有 transition_to_next（最后一个除外） |
| 版本差异 | 不同版本在开头类型或主体编排上有实质差异 |

### 7.3.5 用户交互点

Agent 在前端产物预览区展示 2-3 个大纲版本（分段展开视图），每版本含版本名称、结构预览和预计字数/风格说明。

- `revise`：对某版本提出修改意见
- `regenerate`：要求重新生成某版本或全部版本
- `inject_subtask`：插入 research 子任务，结果注入下一轮生成
- 选择版本：用户明确选择一个版本（通过对话或点击按钮）
- `confirm_next`：选定版本后推进

### 7.3.6 Gate 1 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | 选中的大纲文件存在，JSON 结构完整 |
| 审核通过 | StructureReviewer 对选中版本返回 PASS |
| 用户确认版本 | `artifact_ref` 指向用户明确选中的版本文件 |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_1.preferences_confirmed_at` 非空 |

---

## 7.4 Phase 2: 口播脚本（结构化生成）

### 7.4.1 目标与交付物

产出结构化口播脚本（按段落独立存储，支持单段修改），写入 `phase_2/script_vN.md`。

### 7.4.2 触发条件与输入

Gate 1 通过后自动进入。输入：选中的大纲 + preferences 三字段 + 全局规范 + 目标字数范围。

### 7.4.3 制作 Agent 职责（ScriptAgent）

**核心生成逻辑**：
- 按大纲段落顺序生成口播文字，总字数严格控制在目标范围内（目标时长 × 语速 × 80%~120%）
- 每个段落独立为 segment，含 segment_id、section_title、outline_section_ref、content、word_count
- 每个数据/事实点必须标注来源（`key_data_points[].source`），禁止编造数据
- 每个段落含 emotion_tone 和 transition_note
- 脚本不引入大纲中不存在的新论点，不遗漏大纲中任何观点
- **脚本更新自动重抽取**：每次脚本发生 `user_revision` 或 `regenerate` 后，ScriptAgent 必须重新扫描全文提取 `key_data_points[]`，与上一版做 diff，新增或修改的数据点 `trust_level` 初始化为 `llm_generated`，已删除的数据点从列表移除，未变更的数据点保留原有验证状态

**输出 Schema 核心结构**：
```json
{
  "metadata": {
    "total_word_count": 2400,
    "target_range": "1920-2880",
    "estimated_duration_minutes": 10
  },
  "segments": [
    {
      "segment_id": "seg_01",
      "section_title": "开头-点题",
      "content": "...",
      "word_count": 120,
      "key_data_points": [
        {"claim": "...", "source": "世界黄金协会 2025Q1 报告", "verified": false}
      ],
      "emotion_tone": "好奇/引导",
      "transition_note": "..."
    }
  ]
}
```

### 7.4.4 审核 Agent 职责（FactChecker + StructureReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 字数范围 | total_word_count 在 target_range 内 |
| 段落完整性 | 大纲中每个 section 至少对应一个 segment |
| 观点一致性 | 脚本观点和顺序严格符合大纲，无新增、无遗漏 |
| 数据溯源 | 每个 key_data_point 有非空 source 字段 |
| 数据可验证性 | 提到的数据能支撑其对应观点 |
| 段落衔接 | 每个段落有 transition_note |

### 7.4.5 用户交互点

产物预览区展示分段可折叠视图，每段显示内容 + 字数 + 数据标注。

- `revise`：修改某段（如"把第二段改得更口语化"）
- `regenerate`：重新生成某段或整体脚本
- `inject_subtask`：针对某条数据插入 `verify` 或 `research` 子任务
- `confirm_next`：确认结构化脚本，推进到 P3

### 7.4.6 Gate 2 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | 结构化脚本所有段落字段非空 |
| 审核通过 | FactChecker 和 StructureReviewer 均返回 PASS |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_2.preferences_confirmed_at` 非空 |

---

## 7.5 Phase 3: 口播脚本（风格润色）

### 7.5.1 目标与交付物

产出风格化口播文稿（完整连贯文本 + 分段版本），写入 `phase_3/polished_script_vN.md`。

### 7.5.2 触发条件与输入

Gate 2 通过后自动进入。输入：`phase_2` 结构化脚本 + preferences 中的用户风格配置 + 风格库。

**风格配置获取逻辑**：
- 若 `user_preferences_md` 中已有风格配置 → 直接使用，润色完成后让用户确认是否需要调整
- 若无风格配置 → Agent 先向用户呈现风格选项（专业严谨型 / 亲切科普型 / 犀利评论型 / 自定义），用户选择后写入 `preferences`，再执行润色

### 7.5.3 制作 Agent 职责（PolishAgent）

**核心生成逻辑**：
- 保持观点和数据与结构化脚本完全一致，不增不减
- 将书面语转化为口语化表达，按用户风格配置注入风格特征
- 添加口语连接词、语气词，使朗读流畅自然
- 注意段落间的自然过渡
- 字数与结构化脚本保持一致（±5%）
- 润色不修改数据值和来源，须保留 `key_data_points[]` 的完整引用关系（每个 segment 的 `key_data_points[].data_point_id` 与 P2 一致）
- 输出含：完整口播文本（full_text）+ 分段版本（每段含 polished_text + style_notes）+ 风格应用摘要（style_applied）

**风格学习触发点**：润色完成后，若用户对脚本做了修改，PreferenceExtractor 在 Gate 3 时会分析修改内容提取风格偏好（例如："把'黄金价格上涨了30%'改成'黄金直接飙了30%'" → 提取"偏好更口语化、有力度的表达"）。

### 7.5.4 审核 Agent 职责（StyleReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 风格一致性 | 脚本整体风格与用户配置的风格一致 |
| 观点保真 | 口播脚本的观点和顺序与 Phase 2 结构化脚本严格一致 |
| 数据保真 | 所有客观事实和数据未被修改或遗漏 |
| 字数合规 | 总字数在目标范围内（±5%） |
| 口语化程度 | 无明显书面语残留（如"综上所述""鉴于"等） |
| 来源可溯 | Phase 2 中的数据来源在润色后仍可追溯 |

### 7.5.5 用户交互点

产物预览区展示完整口播文稿，可切换"整体视图"和"对比视图"（润色前后对比）。

- `revise`：修改某段风格（如"这段太生硬，更口语一点"）
- `regenerate`：重新润色某段或整体
- `confirm_next`：确认最终口播脚本，推进到 P4

### 7.5.6 Gate 3 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | 口播文稿 full_text 非空，所有段落均有 polished_text |
| 审核通过 | StyleReviewer 返回 PASS |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_3.preferences_confirmed_at` 非空 |

---

## 7.6 Phase 4: 人声旁白

> **v3.17-AudioMaster 增强（2026-04-17，PRD-DELTA-01）**：P4 交付物升级为「分段 + 完整音频」双层产物。完成定义不再是"能逐段听"，而是"用户已拿到可试听、可下载的完整旁白音频"。

### 7.6.1 目标与交付物

同时产出两层音频产物：

1. **分段层**：人声音频分段文件（`phase_4/narration_seg_XX.mp3`）及音频元信息 JSON，用于逐段精修。
2. **主文件层（v3.17 新增）**：完整可播放、可下载的旁白主音频文件 `phase_4/narration_master.mp3`，由所有分段按 canonical timeline 拼接得到，包含段间自然停顿。主文件元数据写入 `phase_4/narration_master.json`（含 `file_path`、`based_on_phase=4`、`derived_from_segments=[seg_01,...]`、`total_duration_seconds`、`checksum`、`version`）。

`artifact_ref` 同时指向分段元信息 JSON 与完整主音频元数据文件。

### 7.6.2 触发条件与输入

Gate 3 通过后自动进入。输入：最终口播脚本（分段）+ preferences 中的语音配置（音色 `voice_id`、语速 `words_per_minute`、情绪风格 `emotion_style`、TTS 提供商）。

### 7.6.3 制作 Agent 职责（TTSAgent，async）

**执行流程**：
1. 文本预处理：按段落切分为 TTS 片段，插入 SSML 标记（停顿/重音/语速变化），数据密集段适当降速，情绪激昂段适当提速
2. TTS 合成：调用 TTS API 按段生成音频，每段独立文件（`seg_XX.mp3`）
3. 拼接：按段落顺序拼接，段间插入自然停顿（0.3-0.8s）
4. 音频质检：检测静音段（>2s）、爆音/削波、采样率

**输出 Schema 核心字段**：
```json
{
  "audio_metadata": {
    "total_duration_seconds": 612,
    "total_segments": 8,
    "voice_id": "...",
    "sample_rate": 44100
  },
  "segments": [
    {
      "segment_id": "seg_01",
      "file_path": "phase_4/narration_seg_01.mp3",
      "duration_seconds": 45.2,
      "start_time": 0.0,
      "end_time": 45.2,
      "actual_cps": 4.0
    }
  ],
  "quality_check": {
    "silent_segments": [],
    "clipping_segments": [],
    "speed_deviation_pct": 3.2
  }
}
```

**exec_mode = async**：TTS 为长作业，提交到 AsyncTaskManager 后台执行，关闭浏览器不中断。

### 7.6.4 审核 Agent 职责（AudioQualityReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 文本完整性 | 旁白文本与口播脚本完全一致，无丢失、无新增 |
| 语速合规 | 整体 CPS 在 3.0-5.0 范围内 |
| 音频质量 | 无静音段(>2s)、无爆音/削波、采样率正确 |
| 段落完整 | 所有段落都有对应音频文件且可播放 |
| 时长合理 | 总时长与目标时长偏差 ≤ 20% |

### 7.6.5 用户交互点

**v3.17-AudioMaster（PRD-DELTA-01）**：产物预览区采用"主播放器 + 辅助分段精修"双视图。

- **主视图（新增）**：完整旁白播放器（`narration_master.mp3`） + 下载按钮，用户首屏即可通听整条旁白。
- **辅助视图**：分段播放器列表，用于逐段对比与定位重录。

可用动作：

- `revise`（整体加快/减慢语速）→ 更新项目级语速参数并重新生成整段 + 拼接主文件
- `regenerate`（更换音色）→ 提供音色预览，选择后重新生成整段 + 拼接主文件
- 指定某段重录 → 只重新生成该段 → 自动重拼主文件（主文件版本号递增）
- 下载完整旁白 → 直接下载 `narration_master.mp3`
- `confirm_next`：确认人声，推进到 P5

### 7.6.6 Gate 4 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 分段产物完整性 | 所有段落音频文件存在且可播放 |
| **完整音频产物（v3.17 新增）** | `narration_master.mp3` 存在、可播放、时长 ≈ Σ(segments) + 段间停顿 |
| **拼接校验（v3.17 新增）** | 主文件 checksum 与分段派生关系（`derived_from_segments`）匹配，且版本号与最新一次重录一致 |
| 审核通过 | AudioQualityReviewer 返回 PASS（新增对主文件的可播放性与拼接完整性校验） |
| 无进行中异步任务 | TTS async_task status = done |
| 偏好确认完成 | `phases.phase_4.preferences_confirmed_at` 非空 |

---

## 7.7 Phase 5: 背景音乐

> **v3.17-AudioMaster 增强（2026-04-17，PRD-DELTA-02 / 03）**：P5 的主决策对象从"选哪首 BGM 素材"升级为"确认人声 + BGM 的完整混音听感"。完成定义是"用户确认混入 BGM 后的完整音频符合预期"，不是"选定了一首 BGM"。P5 输出的完整混音主文件是 P6 的默认输入。

### 7.7.1 目标与交付物

产出三类产物：

1. **BGM 方案层**：BGM 方案 JSON（含情绪曲线 + BGM 候选选型 + 音量包络），候选 BGM 文件存入 `phase_5/bgm_candidates/bgm_XX.mp3`（保留为辅助轨道）。
2. **混音预览层（v3.17 新增 · PRD-DELTA-02）**：对每个候选 BGM 预先混入 P4 人声主文件生成混音预览 `phase_5/bgm_mix_preview_XX.mp3`，作为默认试听对象。
3. **混音主文件层（v3.17 新增 · PRD-DELTA-03）**：用户确认后的完整混音音频 `phase_5/bgm_mix_master.mp3`，元数据写入 `phase_5/bgm_mix_master.json`（`based_on_phase=5`、`source_narration_master`、`selected_bgm_id`、`envelope_version`、`total_duration_seconds`、`checksum`、`version`）。此文件作为 P5 PASS 后新的"主音频基线"，供 P6 默认消费。

可被 `skip_phase` 跳过；跳过时 P6 回退使用 P4 `narration_master.mp3` 作为主音频基线。

### 7.7.2 触发条件与输入

Gate 4 通过后进入。输入：P4 `narration_master.mp3`（主音频） + 口播脚本（分段） + Phase 4 音频时间轴 + preferences 中的视觉/音乐偏好。

### 7.7.3 制作 Agent 职责（BGMAgent）

**核心生成逻辑**：
1. 情绪分析：分析每个段落的情绪基调（紧张/平静/激昂/深沉/温暖等），生成情绪曲线，标注情绪转折点
2. BGM 推荐：根据情绪曲线推荐 BGM 风格（ambient_corporate/calm_corporate 等）和能量级别
3. 音量包络设计：定义各段 BGM 音量（Hook 阶段 -12dB；正文段 -20dB；转场 -14dB），正文段 BGM 不掩盖人声（≤ -18dB）
4. 素材搜索：调用 BGM API 搜索符合风格的版权免费曲目，标记版权来源（CC0/CC-BY 或自有）

### 7.7.4 审核 Agent 职责（MusicFitReviewer）

**v3.17-AudioMaster（PRD-DELTA-02）**：Reviewer 审核对象从"BGM 素材本身"升级为"混音预览/混音主文件"，补入三项全局听感检查。

| 检查项 | PASS 条件 |
|--------|---------|
| 情绪匹配 | BGM 风格与对应段落的情绪基调一致 |
| 覆盖完整 | BGM 覆盖整个视频时长 |
| 音量合理 | 正文段 BGM ≤ -18dB |
| 版权合规 | BGM 来源标记为 CC0/CC-BY 或自有 |
| **全局和谐度（新增）** | 全程混音中人声 + BGM 无冲突色、情绪曲线连续 |
| **转折衔接自然度（新增）** | 情绪转折点处 BGM 过渡不突兀（无 abrupt transition） |
| **全程人声可懂度（新增）** | 混音后任一段落人声 speech intelligibility 不低于基线（不被 BGM 掩盖） |

### 7.7.5 用户交互点

**v3.17-AudioMaster（PRD-DELTA-02）**：默认试听对象从"BGM 素材"改为"人声 + BGM 的混音预览"。

- **主视图（新增）**：候选 BGM 对应的 **混音预览播放器**（`bgm_mix_preview_XX.mp3`），用户在完整人声语境下判断 BGM 是否合适。
- **辅助视图**：情绪曲线图 + 单独 BGM 试听（辅助轨道，非主决策对象）。
- 用户确认后：系统生成并展示 **确认版完整混音音频播放器**（`bgm_mix_master.mp3`） + 下载按钮。

可用动作：

- `revise`：调整某段 BGM 风格或音量 → 重新生成对应候选的混音预览
- `regenerate`：重新搜索 BGM 素材并生成新混音预览
- `skip_phase`：跳过此阶段（最终产物中标注 BGM 已跳过；P6 主音频基线回退至 `narration_master.mp3`）
- 下载完整混音 → 直接下载 `bgm_mix_master.mp3`
- `confirm_next`：确认混音结果，产出 `bgm_mix_master.mp3`，推进到 P6

### 7.7.6 Gate 5 通过标准

**v3.17-AudioMaster（PRD-DELTA-02 / 03）**：新增"完整混音预览/主文件存在"与"P6 主音频基线切换"两项。

| 门禁项 | 检查内容 |
|--------|---------|
| BGM 方案完整性（未跳过时） | BGM 方案 JSON 存在，候选 BGM 文件存在且可播放 |
| **混音预览完整性（未跳过时，新增）** | 每个参与决策的候选 BGM 均有对应 `bgm_mix_preview_XX.mp3`，可播放 |
| **混音主文件完整性（未跳过时，新增）** | `bgm_mix_master.mp3` 存在、可播放；元数据 `source_narration_master` 指向 P4 主文件；校验和 / 版本号与选定 BGM 一致 |
| 审核通过（未跳过时） | MusicFitReviewer 返回 PASS（含新增三项全局听感检查） |
| **主音频基线切换（新增）** | P5 PASS 后 `project_state.master_audio_ref` 更新为 `bgm_mix_master.mp3`；若 skipped 则保持指向 `narration_master.mp3` |
| 跳过分支 | `phases.phase_5.status = skipped`，无进行中任务 |
| 偏好确认完成 | `phases.phase_5.preferences_confirmed_at` 非空 |

---

## 7.8 Phase 6: 音效设计

> **v3.17-AudioMaster 增强（2026-04-17，PRD-DELTA-04 / 05）**：P6 从"一个音效列表"升级为"全局布局 + 局部试听"的双视图闭环。用户先在全文脚本标注视图确认全局音效布局，再对加工后的编号片段逐段试听。完成后交付"混入 BGM + 音效"的完整可下载最终音频，作为后续阶段默认主音频权威源。

### 7.8.1 目标与交付物

产出三层产物：

1. **全文音效布局层（v3.17 新增 · PRD-DELTA-04）**：`phase_6/sfx_plan.json`，对全文脚本的关键词/句子/叙事节点给出音效布局计划。每条 plan 至少含：`trigger_id`、`script_anchor`（脚本锚点）、`keyword_span`（关键词范围）、`planned_time_sec`、`sfx_type`、`rationale`（为什么加）、`narrative_role`（服务于哪段叙事目的）。
2. **加工分段层（v3.17 新增 · PRD-DELTA-04）**：按编号生成加工后的可试听分段 `phase_6/sfx_applied_segments/seg_XX.mp3`，底轨基于 P5 `bgm_mix_master.mp3`（若 P5 skipped 则基于 `narration_master.mp3`）。
3. **最终音频主文件层（v3.17 新增 · PRD-DELTA-05）**：`phase_6/final_audio_with_bgm_sfx.mp3`，元数据写入 `phase_6/final_audio_master.json`（`based_on_phase=6`、`source_mix_master`、`applied_sfx_plan_version`、`total_duration_seconds`、`checksum`、`version`）。该文件作为后续阶段（P7/P7A/P10/P11）默认主音频权威源。

原 `phase_6/sfx_XX.mp3` 作为单独音效素材文件保留。可被 `skip_phase` 跳过；跳过时主音频基线保持 P5 输出（或退回 P4）。

### 7.8.2 触发条件与输入

Gate 5 通过（或 skip）后进入。输入：

- **主音频基线（v3.17 新增）**：P5 `bgm_mix_master.mp3`（若 P5 skipped → 回退 P4 `narration_master.mp3`）
- 口播脚本（分段，带 script_anchor/span 元数据） + Phase 3 最终脚本
- Phase 4 音频时间轴（canonical timeline）
- Phase 5 情绪曲线（若存在）

### 7.8.3 制作 Agent 职责（SFXAgent）

**v3.17-AudioMaster（PRD-DELTA-04）**：拆成"全局规划 → 局部加工"两步。

**Step 1：全文规划**
- 通读全文脚本，识别关键词/句子/叙事节点
- 为每个提议的音效说明：为什么要加、加什么类型、服务于什么叙事目的（`rationale` + `narrative_role`）
- 输出 `sfx_plan.json`，交由前端做全文标注展示与用户确认

**Step 2：用户确认布局后的局部混音执行**
- 按 `sfx_plan.json` 在"主音频基线"上叠加每条音效
- 按编号切出 `sfx_applied_segments/seg_XX.mp3` 供逐段试听
- 所有分段试听确认后，合成完整最终音频 `final_audio_with_bgm_sfx.mp3`

**核心设计原则（保留）**：
- 音效类型：boom / whoosh / ding / rise / warm_pad 等
- 平均间隔 ≥ 15 秒，关键节点才加
- 与 BGM 转折点不重叠（±2s）
- 使用至少 3 种不同类型

**输出格式**：`sfx_plan.json` 每条含 trigger_id、script_anchor、keyword_span、planned_time_sec、sfx_type、rationale、narrative_role、volume_db、duration_seconds。

### 7.8.4 审核 Agent 职责（SFXReviewer）

**v3.17-AudioMaster（PRD-DELTA-04，对齐 TECH-DELTA-04）**：Reviewer 拆成两层：

**Layer A · SfxLayoutReviewer（审核布局质量）**

| 检查项 | PASS 条件 |
|--------|---------|
| 脚本覆盖 | 重要叙事节点均有布局条目或被明确跳过 |
| 关键词选择 | `keyword_span` 命中脚本中的强语义锚点而非任意位置 |
| 解释性 | 每条条目 `rationale` + `narrative_role` 非空且与脚本一致 |
| 稀疏性 | 平均间隔 ≥ 15 秒，连续密集段被收敛 |

**Layer B · SfxMixReviewer（审核混音听感）**

| 检查项 | PASS 条件 |
|--------|---------|
| 片段听感 | 每个 `sfx_applied_segments/seg_XX.mp3` 无爆音/削波/错位 |
| 不遮挡口播 | 音效 + BGM 不超过人声 -6dB |
| 与 BGM 协同 | 音效与底层 BGM 不出现节拍/色彩冲突 |
| 类型多样 | 使用至少 3 种不同类型的音效 |

### 7.8.5 用户交互点

**v3.17-AudioMaster（PRD-DELTA-04 / 05）**：产物预览区采用两段式交互，结束后展示最终完整音频。

**第一段：全文音效布局确认**
- 全文脚本视图 + 音效标注层（标注每条音效在脚本中的位置、类型、rationale）
- 用户可对布局条目做 `layout_feedback`：增/删/改类型/改锚点
- 用户确认后才触发 Step 2 混音执行

**第二段：编号分段试听**
- 按编号列表展示 `sfx_applied_segments/seg_XX.mp3`，逐段试听
- 用户可对单段做 `mix_feedback`（重新混音该段），不触发全量重做

**第三段：最终完整音频（新增）**
- 完整音频播放器（`final_audio_with_bgm_sfx.mp3`） + 下载按钮
- 用户通听后决定是否 `confirm_next`

可用动作：
- `revise` / `layout_feedback`：修改布局计划
- `revise` / `mix_feedback`：只重新混音某段
- `regenerate`：重新生成全部布局
- `skip_phase`：跳过音效设计（最终主音频基线回退至 P5 或 P4）
- 下载完整最终音频 → 下载 `final_audio_with_bgm_sfx.mp3`
- `confirm_next`：确认最终音频，推进到 P7

### 7.8.6 Gate 6 通过标准

**v3.17-AudioMaster（PRD-DELTA-04 / 05）**：新增"全文布局、加工分段、完整最终音频"三项强制校验。

| 门禁项 | 检查内容 |
|--------|---------|
| **全文布局完整性（未跳过时，新增）** | `sfx_plan.json` 存在，所有条目含 rationale/narrative_role，且经过 SfxLayoutReviewer PASS |
| **加工分段完整性（未跳过时，新增）** | 每个布局触发点在 `sfx_applied_segments/` 有对应可播放片段，且经过 SfxMixReviewer PASS |
| **最终音频完整性（未跳过时，新增）** | `final_audio_with_bgm_sfx.mp3` 存在、可播放；元数据 `source_mix_master` 指向 P5（或 P4 回退源）；version 与最新一次布局/混音一致 |
| 单体素材完整性（未跳过时） | `sfx_XX.mp3` 素材文件存在且可播放 |
| 审核通过（未跳过时） | Layout + Mix 双层 Reviewer 均 PASS |
| **主音频基线切换（新增）** | P6 PASS 后 `project_state.master_audio_ref` 更新为 `final_audio_with_bgm_sfx.mp3` |
| 跳过分支 | `phases.phase_6.status = skipped`（主音频基线保持 P5/P4） |
| 偏好确认完成 | `phases.phase_6.preferences_confirmed_at` 非空 |

---

## 7.9 Phase 7: 分镜脚本

> **v3.16-BDD 增强（2026-04-17）**：在 v3.15 shot 独立存储基础上，本阶段强制每个 shot 含 `anchor_text` + `script_span_id` 锚点字段，支持精确拆解与下游绑定；引入「预览态（P7）/ 生产态（P10+）」切换契约。详见 §10.G。

### 7.9.1 目标与交付物

产出完整分镜脚本 JSON（每个 shot 的时间范围、画面类型、内容参数），写入 `phase_7/storyboard_vN.json`。

### 7.9.2 触发条件与输入

Gate 6 通过（或 skip）后进入。输入：口播脚本（分段）+ Phase 4 音频时间轴 + Phase 3 最终脚本 + 视频规格 + preferences 中的视觉偏好。

### 7.9.3 制作 Agent 职责（StoryboardAgent）

**画面类型定义**：
- `template`（动态画面）：Remotion/FFmpeg 渲染的动态内容，包括数据图表（折线图/柱状图）、数据卡片、文字动效、新闻截图嵌入、时间线、对比图
- `broll`（实景素材）：用于氛围渲染、场景过渡的实景视频片段

**核心设计原则**：
- 每 20-30 秒必须切换画面类型或内容
- 动态模板和 B-Roll 交替使用，避免视觉疲劳
- 数据密集段使用图表/数据卡，叙事段使用 B-Roll
- 关键数据点必须有对应的视觉呈现
- 单个画面时长 3s-30s

**输出格式**：每个 shot 包含 shot_id、time_range（start/end_seconds）、type（template/broll）、template_type 或 search_keywords、content（图表数据或场景描述）、narration_text（对应口播片段）。

### 7.9.4 审核 Agent 职责（StoryboardReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 时间覆盖 | 所有 shot 的时间范围连续覆盖整段音频，无空白 |
| 画面切换频率 | 连续同类型画面不超过 2 个 |
| 数据画面覆盖 | 脚本中每个关键数据至少有一个对应图表/数据卡 |
| 时长合理 | 单个画面时长 3s-30s |
| 叙事对齐 | 每个 shot 的 narration_text 与时间轴对齐 |

### 7.9.5 用户交互点

产物预览区展示分镜卡片画廊（每张卡片显示时间戳、画面类型、内容描述、对应口播文字）。

- `revise`：修改某个 shot 的画面类型或内容
- `regenerate`：重新生成分镜脚本
- `inject_subtask`：插入 research 子任务补充背景素材关键词
- `confirm_next`：确认分镜，推进到 P8

### 7.9.6 Gate 7 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | storyboard JSON 存在，所有 shot 字段完整 |
| 审核通过 | StoryboardReviewer 返回 PASS |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_7.preferences_confirmed_at` 非空 |

---

## 7.9A Phase 7A: 分镜脚本物料补充

> **v3.17-P7A 增强（2026-04-17，PRD-DELTA-06 / 07）**：在 P7 分镜与 P8 关键画面渲染之间新增显式阶段，统一完成"讲到 XX 时展示 XX"所需的原始物料补齐与核实，避免 P8 边渲染边搜资料。最小改动策略：本轮不做全局 phase 重编号，以 `7.9A` / `P7A` 方式插入，后续 API/UI/Schema/埋点沿用既有 P7/P8 命名。

### 7.9A.1 目标与交付物

对分镜中涉及的事实、新闻、信息、图标、图表等缺失原始物料做 LLM 任务编排 → 获取 → 核实 → 入库 → Shot 级绑定。

交付物：

1. **`phase_7a/material_manifest.json`**：物料清单。每条含 `material_id`、`shot_id`、`material_type`（fact/news/figure/icon/chart/image/video/quote）、`required`（hard/soft）、`verification_status`（pending/verified/rejected/missing）、`source`、`fetched_at`、`verified_at`、`rationale`。
2. **`phase_7a/shot_material_bindings.json`**：Shot 级绑定。每个 shot 列出其依赖的 material_id 列表，区分"必需 required"与"可选 optional"。
3. **`phase_7a/verified_materials/`**：经核实的物料文件目录（图片、新闻截图、数据文件等）。
4. **`phase_7a/chart_materials/`**：图表类物料的结构化 chart_material JSON（字段见 §7.9A.3 · 图表子流程）。

### 7.9A.2 触发条件与输入

Gate 7 通过后自动进入。输入：

- P7 `storyboard_vN.json`（全部 shot，含 anchor_text / script_span_id）
- P3 最终口播脚本（事实溯源）
- preferences 中的视觉/数据偏好
- 可调用外部能力：DataService、B-Roll 搜索、新闻抓取、FactChecker

### 7.9A.3 制作 Agent 职责（三角色编排，对齐 TECH-DELTA-05 / 06）

- **StoryboardAssetPlanner**：读取 P7 分镜，为每个 shot 识别需要的原始物料，生成 `material_manifest.json` 骨架（任务列表）。
- **MaterialFetcher**：按 manifest 调用对应外部能力（API / 爬取 / 图库 / DataService）获取原始物料，落盘到 `verified_materials/`。
- **MaterialVerifier**：对每个物料做真实性/准确性核实（FactChecker L2、数据源一致性比对），更新 `verification_status`。

#### 图表类子流程（PRD-DELTA-07）

对 shot.type = chart 的条目，必须按以下标准子流程收敛：

1. **识别图表需求**：metric_name、类型（line/bar/pie）、叙事目的
2. **确认时间范围/统计口径**：`date_range`、`granularity`（day/week/month）、数据源 `source`
3. **获取数据**：调用 DataService（如 FinancialDataService）
4. **验证数据**：FactChecker 核对数值、趋势、异常点
5. **生成 chart_spec / axis_spec**：
   - `axis_spec.x_axis`：type（category/time/value）、labels、range
   - `axis_spec.y_axis`：unit、min、max、scale_mode（linear/log）
6. **绑定到 shot_id**：写入 `shot_material_bindings.json`

每条 `chart_material` 至少含：`chart_id`、`shot_id`、`metric_name`、`date_range`、`granularity`、`source`、`verification_status`、`chart_spec`、`axis_spec`。

### 7.9A.4 审核 Agent 职责（MaterialReadinessReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 清单覆盖 | 每个 P7 shot 在 `shot_material_bindings.json` 中均有条目（含"无需补料"标注） |
| 必需物料齐备 | 所有 `required=hard` 的 material 均 `verification_status=verified` |
| 真实性核实 | 所有 fact/news/figure/quote 类 material 经过 FactChecker 核验并留存证据 |
| 图表就绪 | 所有 chart shot 具备已验证的 `chart_material`，含完整 `chart_spec` + `axis_spec` |
| 版权合规 | 所有外部物料标明授权来源 |
| 无 pending 物料 | 不存在 `verification_status=pending` 的 required material |

### 7.9A.5 用户交互点

产物预览区按"Shot × 物料"矩阵展示：

- Shot 卡片展开可见绑定的 material 列表、验证状态、来源链接、证据摘要
- 图表类 shot 可见"时间范围 / 坐标轴方案"确认卡（用户可修改 `date_range` / `axis_spec` 再重新抓数验证）
- 缺失或未验证的 material 以警告色标注，点击可追加获取子任务

可用动作：
- `revise`：修改某条 material 的来源或参数（如时间范围）
- `inject_subtask`：补充获取新物料（扩充 manifest）
- `regenerate`：重建 manifest（慎用，会重新获取）
- `confirm_next`：确认物料就绪，推进到 P8

### 7.9A.6 Gate 7A 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | `material_manifest.json` + `shot_material_bindings.json` 均存在且无缺失字段 |
| 必需物料完整 | 所有 `required=hard` material `verification_status=verified` |
| 图表物料完整 | 所有 chart shot 已产出可验证 chart_material（若缺失 → 阻塞 P8） |
| 审核通过 | MaterialReadinessReviewer 返回 PASS |
| 无 pending | 无未完成的外部抓取/验证任务 |
| 偏好确认完成 | `phases.phase_7a.preferences_confirmed_at` 非空 |

> **完成定义**：P8 的前置条件不再只是"有分镜稿"，而是"有分镜稿 + 有经过核实的 Shot 级物料绑定"。

---

## 7.10 Phase 8: 关键画面渲染

> **v3.17-P7A 增强（2026-04-17，PRD-DELTA-08）**：P8 改为"工程执行阶段"，严格消费 P7A 输出，禁止临时向外部搜索素材，禁止对缺失物料做推测性生成。降级规则区分"工程可降级"与"事实不可降级"。

### 7.10.1 目标与交付物

产出所有 `type=template` / `type=chart` 的 shot 对应的渲染视频片段（`phase_8/keyframe_XX.mp4`）及预览帧（PNG），渲染结果 JSON 写入 `phase_8/render_results.json`。

### 7.10.2 触发条件与输入

**Gate 7A 通过后进入**（v3.17 新增前置）。输入：

- Phase 7 分镜脚本（仅需渲染的 shot）
- **Phase 7A `material_manifest.json` + `shot_material_bindings.json` + `verified_materials/` + `chart_materials/`**（v3.17 新增，必需）
- 配色方案 `theme.json`
- 渲染配置（分辨率/帧率）

渲染输入以 P7A 输出为权威源：模板优先吃 `chart_material` 结构化对象，而不是自由文本 content。

### 7.10.3 制作 Agent 职责（KeyframeRenderAgent，async）

**v3.17-P7A（PRD-DELTA-08）执行前置**：`MaterialReadinessCheck`——渲染启动前校验每个目标 shot 的 bound material 均已 `verified`，否则阻塞该 shot 进入"事实阻塞"态。

**执行流程**：
1. `MaterialReadinessCheck` 全量校验（新增）
2. 遍历需渲染的 shot
3. 根据 template_type 选择渲染引擎（Remotion/FFmpeg/Pillow）
4. 从 P7A `chart_material` / `verified_materials/` 注入数据与参数；配色从 `theme.json` 读取
5. 逐个渲染为视频片段（shot_XX.mp4），生成预览帧（首帧/中帧/末帧）
6. 渲染失败的 shot 按"工程降级规则"处理

**v3.17 强约束（新增）**：
- **禁止临时搜索**：渲染阶段不得向外部发起新的资料检索（对应 TECH-DELTA-07）
- **禁止推测性生成替代正式资料**：缺失 `verified` 物料的 shot 必须阻塞，不得以 LLM 臆造内容填充
- **事实不可降级**：数据不齐 / 物料未核实 → `material_missing` / `material_unverified` 错误，阻塞该 shot

**降级规则拆分（v3.17 新增）**：

| 错误码 | 触发条件 | 处理方式 |
|--------|---------|---------|
| `render_failed` | 引擎渲染异常、动画崩溃 | 工程降级 → 替换为默认文字卡 / 静态图，不阻塞流程 |
| `material_missing` | P7A 绑定 material 文件缺失 | 事实阻塞 → 回跳 P7A 补料，不得 fallback |
| `material_unverified` | P7A 物料存在但 `verification_status ≠ verified` | 事实阻塞 → 回跳 P7A 完成核实，不得 fallback |

**关键约束（保留 + 更新）**：
- 所有画面使用同一配色方案（`theme.json`）
- 图表中的数据必须等于 P7A `chart_material` 中已验证数据（不再引用自由文本）
- 输出分辨率与目标规格一致

**exec_mode = async**：批量渲染为长作业，后台执行。

### 7.10.4 审核 Agent 职责（VisualReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 渲染成功率 | ≥ 90% 的 shot 渲染成功（未超过 10% 工程降级） |
| **物料一致性（v3.17 新增）** | 每个成功 shot 的 bound material 均 `verification_status=verified`，无 `material_missing` / `material_unverified` 遗留 |
| 文件完整性 | 每个成功的 shot 有对应 mp4 文件且可播放 |
| 配色一致 | 所有画面使用同一配色方案 |
| 数据正确 | 图表中的数据与 P7A `chart_material` 一致 |
| 分辨率正确 | 输出分辨率与目标一致 |

### 7.10.5 用户交互点

产物预览区展示网格画廊，每帧显示 shot_id、时间范围、预览图，点击可放大。失败/降级的 shot 以警告色标注。

- `revise`（指定某个 Shot 修改参数）→ 追加 `regenerate_section` task，只重渲染该 shot
- `regenerate`（全部重渲染）
- `confirm_next`：确认关键帧，推进到 P9

### 7.10.6 Gate 8 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | render_results.json 存在，成功渲染 shot 占比 ≥ 90% |
| 审核通过 | VisualReviewer 返回 PASS（已降级 shot 不阻塞） |
| 无进行中异步任务 | 渲染 async_task status = done |
| 偏好确认完成 | `phases.phase_8.preferences_confirmed_at` 非空 |

---

## 7.11 Phase 9: B-Roll 素材准备

### 7.11.1 目标与交付物

产出 B-Roll 素材分配 JSON（每个 broll shot 对应已下载素材），素材文件存入 `phase_9/broll_shot_XX.mp4`。

### 7.11.2 触发条件与输入

Gate 8 通过后进入。输入：Phase 7 分镜脚本中 type=broll 的所有 shot（含 search_keywords 和 time_range）。

### 7.11.3 制作 Agent 职责（BRollAgent）

**执行流程**：
1. 遍历所有 B-Roll shot，提取搜索关键词
2. 调用素材搜索 API（Pexels 等免版权素材库）
3. 按语义相关性、分辨率、时长排序，为每个 shot 选择最佳素材
4. 下载并裁剪到目标时长
5. 无法匹配的 shot 降级为动态背景替代，记录为覆盖缺口

**关键约束**：
- 素材分辨率 ≥ 目标分辨率
- 素材时长 ≥ shot 所需时长
- 素材来源为免版权或已授权
- 若版权阻塞：自动换源 1 次；仍失败则列入缺口记录，不阻塞流程但 BRollFitReviewer 必须 FAIL

### 7.11.4 审核 Agent 职责（BRollFitReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 语义相关 | 素材内容与对应口播段落主题相关 |
| 分辨率达标 | 素材分辨率 ≥ 目标分辨率 |
| 时长足够 | 素材时长 ≥ shot 所需时长 |
| 版权合规 | 素材来源为免版权或已授权 |
| B-Roll 覆盖率 | B-Roll 覆盖率 ≥ 30%（低于不阻塞但降级记录） |
| 无版权阻塞 | 所有已选素材无版权阻塞项 |

### 7.11.5 用户交互点

产物预览区展示缩略图画廊，每个素材可点击预览，显示来源和时长。

- `revise`（替换某个 shot 的素材）→ 重新搜索
- 手动补充素材 URL
- `confirm_next`：确认素材清单，推进到 P10

### 7.11.6 Gate 9 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | broll_assignments JSON 存在，已下载素材文件存在 |
| 审核通过 | BRollFitReviewer 返回 PASS（B-Roll 覆盖率未达标记录为降级项但不阻塞） |
| 无进行中任务 | task_ledger 所有 task 处于终态 |
| 偏好确认完成 | `phases.phase_9.preferences_confirmed_at` 非空 |

---

## 7.12 Phase 10: 粗剪合成

### 7.12.1 目标与交付物

产出粗剪视频（`phase_10/rough_cut_v1.mp4`）及合成元信息 JSON。

### 7.12.2 触发条件与输入

Gate 9 通过后进入。输入：Phase 4 人声音频（分段）+ Phase 5 BGM（若存在）+ Phase 6 SFX（若存在）+ Phase 8 渲染画面 + Phase 9 B-Roll 素材 + Phase 7 分镜时间轴。

### 7.12.3 制作 Agent 职责（RoughCutAgent，async）

**执行流程**：
1. 按分镜时间轴拼接视觉轨（template 画面 + B-Roll，按 shot_id 顺序）
2. 混合音频轨：人声为主轨 + BGM 按包络混入（若存在）+ SFX 按时间点叠加（若存在）
3. 叠加字幕轨（从口播脚本分段生成 SRT 字幕）
4. 添加转场效果：段落间 crossfade；章节间硬切 + 章节卡
5. 导出粗剪视频（H.264，目标码率）

**exec_mode = async**：视频合成为长作业。

### 7.12.4 审核 Agent 职责（AVSyncReviewer）

| 检查项 | PASS 条件 |
|--------|---------|
| 音画同步 | AV 同步偏移 ≤ 100ms |
| 无空白帧 | 无纯黑/纯白空白帧（允许设计性纯色帧） |
| 音频完整 | 无静音段（>2s 非设计性静默） |
| 字幕对齐 | 字幕与语音时间对齐率 ≥ 80% |
| 段落连续 | 所有分镜 shot 按顺序出现，无遗漏 |
| 时长正确 | 粗剪总时长与音频总时长偏差 ≤ 1s |
| 分辨率正确 | 输出分辨率与目标一致 |

### 7.12.5 用户交互点

产物预览区展示内嵌视频播放器（粗剪全片）。

- `revise`：针对某段提出修改（如"第 3 段画面换成 B-Roll"、"这段 BGM 太响了"）
- `regenerate`：重新合成（重置参数后重跑）
- `confirm_next`：确认粗剪，推进到 P11

### 7.12.6 Gate 10 通过标准

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | rough_cut mp4 文件存在且可播放，文件大小 > 0 |
| 审核通过 | AVSyncReviewer 返回 PASS |
| 无进行中异步任务 | 合成 async_task status = done |
| 偏好确认完成 | `phases.phase_10.preferences_confirmed_at` 非空 |

---

## 7.13 Phase 11: 精剪交付

### 7.13.1 目标与交付物

产出各平台最终视频文件（`phase_11/final_<platform>.mp4`）、封面图（`phase_11/cover_XX.png`）、字幕文件（`phase_11/subtitle.srt`）。项目状态变为 "completed"。

### 7.13.2 触发条件与输入

Gate 10 通过后进入。输入：Phase 10 粗剪视频 + 用户对粗剪的修改反馈 + Phase 0 平台规格信息。

### 7.13.3 制作 Agent 职责（FinalCutAgent，async）

**执行子任务**：

**精剪调整**：根据用户对粗剪的反馈进行：局部画面替换、音量微调、字幕修正、转场效果调整、片头/片尾添加。

**封面生成**：生成 3 个封面方案（character_dominant/title_focused/data_highlight 等风格），每个封面含主题文字 + 品牌元素 + 关键数据，尺寸按平台规格（bilibili: 1146x717）。

**多平台适配**：根据 Phase 0 的平台规格，生成不同版本：
```json
{
  "platform_outputs": [
    {
      "platform": "bilibili",
      "file_path": "phase_11/final_bilibili_1080p.mp4",
      "resolution": "1920x1080",
      "bitrate": "8Mbps"
    },
    {
      "platform": "douyin",
      "file_path": "phase_11/final_douyin_vertical.mp4",
      "resolution": "1080x1920",
      "bitrate": "6Mbps"
    }
  ]
}
```

**exec_mode = async**：精剪导出为长作业。

### 7.13.4 审核 Agent 职责（FinalReviewer，汇总所有前序审核项）

| 检查项 | PASS 条件 |
|--------|---------|
| 音画同步 | 终版 AV 偏移 ≤ 50ms |
| 视频完整性 | 片头/正文/片尾完整，无截断 |
| 音频完整性 | BGM/SFX/人声均正常混合（若对应阶段未跳过） |
| 字幕完整性 | 字幕覆盖全部口播内容 |
| 分辨率正确 | 每个平台版本的分辨率符合 Phase 0 规格 |
| 封面质量 | 封面尺寸正确、文字清晰、至少 3 个方案 |
| 文件可播放 | 所有输出文件可正常播放 |
| 导出次数 | 导出失败次数 = 0（连续失败 2 次后停止自动重试） |

### 7.13.5 用户交互点

产物预览区展示内嵌播放器（最终版）+ 封面方案画廊 + 各平台下载按钮。

交付摘要示例：

```
视频制作完成！

《黄金价格走势分析与投资展望》

视频信息：
- 时长：10分25秒
- 分辨率：1920x1080
- 总段落：8段，28个画面

交付文件：
- B站版本：[bilibili_1080p.mp4]（可下载）
- 抖音版本：[douyin_vertical.mp4]（可下载）
- 封面（3选1）：[封面1] [封面2] [封面3]
- 字幕文件：[subtitle.srt]

项目状态：已完成，所有产物已归档。
```

用户可选择封面、下载文件，也可 `revise` 要求微调后重新导出。

### 7.13.6 Gate 11 通过标准（最终门禁）

| 门禁项 | 检查内容 |
|--------|---------|
| 产物完整性 | 所有平台版本 mp4 文件存在且可播放；封面文件存在；字幕文件存在 |
| 审核通过 | FinalReviewer 返回 PASS |
| 无进行中异步任务 | 导出 async_task status = done |
| 偏好确认完成 | `phases.phase_11.preferences_confirmed_at` 非空 |

Gate 11 通过后：`project.status = "completed"`，`project.completed_at = now()`，前端切换为只读模式（仍可下载产物，不可修改）。


---

# 第八部分：事件流与过程透明化

> **技术实现索引**：异步任务管理（AsyncTaskManager、worker 调度、崩溃恢复）见 [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) 及 [`docs/specs/SPEC-B-infra-deploy.md`](specs/SPEC-B-infra-deploy.md)。

## 8.1 事件类型

所有后端动作产生事件，广播到 WebSocket，前端 Agent 活动流面板实时渲染。

| 事件类型 | Payload |
|---|---|
| `phase.entered` | `{phase, task_ledger_initial}` |
| `phase.advanced` | `{from_phase, to_phase}` |
| `phase.rolled_back` | `{from_phase, to_phase, invalidated_phases[]}` |
| `ledger.task_added` | `{task_id, type, trigger}` |
| `ledger.task_started` | `{task_id, agent_name}` |
| `ledger.task_progress` | `{task_id, progress}` |
| `ledger.task_completed` | `{task_id, result_summary}` |
| `ledger.task_failed` | `{task_id, error}` |
| `agent.llm_call_started` | `{agent_name, task_id, model}` |
| `agent.llm_call_completed` | `{agent_name, task_id, tokens, duration_ms}` |
| `async.task_progress` | `{async_task_id, progress}` |
| `gatekeeper.check_failed` | `{phase, reasons[]}` |
| `router.intent_recognized` | `{action, user_input_excerpt}` |
| `router.clarification_needed` | `{question}` |
| `preference_extraction_started` | `{phase}` |
| `preference_candidates_ready` | `{count}` |
| `preference_confirmed` | `{accepted_count, rejected_count}` |

## 8.2 前端渲染

Agent 活动流面板展示最近 50 条事件，滚动加载历史。每条一行：

```
10:23:01  FSM            -> 进入 Phase 2 口播脚本
10:23:01  ScriptAgent    -> 开始生成脚本 (task t_000001)
10:23:45  ScriptAgent    -> 完成 (耗时 44s, 2560 tokens)
10:23:46  FactChecker    -> 开始审核
10:24:10  FactChecker    -> PASS
10:24:12  User           -> "更口语化" (通过 Router)
10:24:12  IntentRouter   -> 识别为 revise
10:24:13  ScriptAgent    -> 修改开头段
...
```

---

# 第九部分：非功能需求

| 维度 | 要求 |
|---|---|
| 并发 | 单用户可同时推进多个项目，但单项目仅支持单 tab 编辑 |
| 可用性 | 浏览器关闭不影响后台任务；任务失败有明确错误信息和重试入口；连续 5 次 regenerate 后必须进入人工兜底分支 |
| 持久化 | 结构化状态单一写入 SQLite（权威源），媒体产物存文件系统；`snapshot.md` 与 `project_state.json` 仅为只读导出 |
| 可观测性 | 所有 Agent 调用、LLM token 消耗、耗时写入 `agent_call_log` 表；敏感字段脱敏；异步进度刷新周期 ≤ 5s |
| 成本控制 | 记录 per-phase / per-project token 成本并告警，不做自动熔断；P50 ≤ $8，P90 ≤ $15 |
| 可恢复性 | 服务重启或用户次日重开后 10 秒内所有项目状态恢复可用；损坏产物必须被显式标红，不允许静默丢失 |
| 性能 | Router 调用 P95 ≤ 3s，P99 ≤ 5s；首帧加载 ≤ 3s；长任务不阻塞 API 主进程 |
| 安全 | 私有化部署，不暴露公网；API Key 存在 .env，不进 git，不上传 |
| 国际化 | 暂不支持，仅中文 |

> **技术实现索引**：部署形态、Docker Compose 配置、Pre-flight 检查清单详见 [`docs/specs/SPEC-B-infra-deploy.md`](specs/SPEC-B-infra-deploy.md)。

---

# 第十部分：v3.16-BDD 行为补丁集（2026-04-17）

> **触发**：`docs/BDD_DOC_GAP_AUDIT_2026-04-17.md`（基线 = 30 BDD Feature / 100 Scenario）。
> **可执行规格**：`docs/specs/SPEC_REVISION_REQ_v3.16_2026-04-17.md`（26 项 P0）。
> **BDD↔文档反向映射**：`docs/specs/BDD_DOC_MAPPING_v3.16_2026-04-17.md`。
> **去重铁律**：与 v3.15 重叠的字段（`key_data_points` / shot 独立存储 / TTSAgent 偏好确认 / script 自动重抽取）一律引用既有章节，不重新定义。
> **范围**：本部分定义产品级行为（用户可见行为 + 交互细节 + 验收口径），机制与状态机详见 TECH_PLAN 附录；接口/Schema/AC 详见 SPEC-A..F-BDD-* 章节。

## 10.0 v3.16-BDD 八类能力簇总览

| 节 | 能力簇 | BDD Feature 名（节选） | 影响章节 | 对应 SPEC |
|---|---|---|---|---|
| 10.A | AI 问答安全与合规响应 | `AI 问答安全校验` | §6.1 / §8 | SPEC-C C-BDD-1 |
| 10.B | 数据验证面板 → Claim 工作台 | `可验证信息清单与独立验证界面` / `事实与数据的自动溯源验证触发` | §5.3.7 | SPEC-A A-BDD-1 / SPEC-E E-BDD-3 |
| 10.C | 用户质疑 / 补充事实 | `用户对数据和事件提出质疑或补充时的动作执行` | §6.1 / §7 各阶段 | SPEC-D D-BDD-2 |
| 10.D | 偏好模型扩展（阶段偏好 + 回写） | `偏好提取的全局与阶段作用域` / `音频参数的全局调整、局部微调与偏好回写` | §3.1 / §6.1 | SPEC-A A-BDD-2 / SPEC-C C-BDD-3 |
| 10.E | 结构化插入与最小改动改稿 | `在已有脚本中增插新对比环节` | §6.1 / §7.4-§7.5 | SPEC-C C-BDD-5 |
| 10.F | 项目列表与阶段回看 | `项目列表与阶段回看` | §5.1 / §5.3 | SPEC-A A-BDD-3 / SPEC-E E-BDD-1/E-BDD-2 |
| 10.G | 分镜精确拆解 anchor 化 | `分镜脚本阶段的可视化预览与精确拆解` | §7.9 | SPEC-D D-BDD-4 / SPEC-E E-BDD-4 |
| 10.H | 图表请求闭环 | `用户提出绘制黄金价格折线图时的确认、取数与验证` / `关键画面图表样式的可定制化` | §6.1 / §7.10-§7.11 | SPEC-C C-BDD-6 / SPEC-E E-BDD-5 |

---

## 10.A AI 问答安全与合规响应（PRD-01 → SPEC-C C-BDD-1）

**背景**：v3.15 之前系统未明确定义"什么样的用户输入应当拒答 / 受限 / 澄清"，存在 LLM 即兴回答政治敏感、违法操作、未验证投资建议的风险。本节定义系统级安全护栏。

**用户可见行为**：

1. 用户输入命中安全分类后，对话区显示 `SafetyResponseCard`（不显示原始用户输入；仅显示分类标签、模板话术、可选"为什么这个回复"折叠说明）。
2. 安全决策共五档：
   - `正常回答`：不拦截，进入 IntentRouter
   - `安全澄清`：在下游 prompt 注入约束（如"请勿提供具体投资标的，仅做信息汇总"）+ 提供替代帮助选项
   - `限制回答`：返回模板话术，禁止生成原创内容
   - `标准拒答`：返回拒答模板，不进入 IntentRouter
   - `转人工`：超出 V1 范围，返回引导话术
3. 拒答/受限响应**不阻断**当前项目其他动作（如继续编辑脚本不受影响）。

**最小覆盖类别（V1）**：政治敏感、违法操作、个人隐私、版权侵权、未验证投资建议、正常问答。

**配置**：标准话术存于 `config/safety_templates.yaml`，热更新；禁止 LLM 即兴回答（命中后纯模板返回，不调用 LLM）。

**审计**：refuse / restrict 命中写入 `events` 表（`event_type=safety.blocked`，含 category / template_id / user_input_hash，不存原文）。

**验收口径**：测试集 ≥ 50 条/类，目标误杀率 < 5%、漏放率 < 1%。

---

## 10.B 数据验证面板升级为 Claim 工作台（PRD-02 → SPEC-A A-BDD-1 + SPEC-E E-BDD-3）

**背景**：v3.15 §5.3.7 数据验证面板仅展示 P2 ScriptAgent 抽取的 `key_data_points`，无法承载跨阶段（P7 分镜事实 / P8 图表数据 / P9 B-Roll 元数据）和跨类型（fact / data / event / citation / image_backed）的 claim。本节将面板升级为「Claim 工作台」，并把 claim 提升为系统级一等对象。

**用户可见行为**：

1. **视图**：表格 / 卡片切换；列含 `claim_id / 类型 / 文本 / 来源阶段 / 验证状态 / 阻断级别 / 操作`。
2. **筛选维度（4 项）**：来源阶段（P2/P7/P8/P9/user_input）、验证状态（pending / verifying / verified / failed / stale / superseded / user_disputed）、阻断级别（hard / soft / none）、claim 类型。
3. **行级操作**：质疑（→ 10.C）、补充关联事实、查看证据（含来源 URL / 验证时间 / verifier 类型）、接受人工覆盖。
4. **顶部统计条**：pending / verified / failed / disputed 数量。
5. **阻断徽章**：当 hard blocking unverified > 0 时，工作流右上角显示红色徽章 + 跳转工作台入口。

**与 v3.15 兼容**：`key_data_point.data_point_id` 作为 `Claim.claim_id` 初始来源；P3 润色保留 `claim_id` 引用关系不变；既有"脚本更新自动重抽取"流程保留。

**生产门禁联动**：未验证 hard claim 阻断 P8 渲染（仅跳过该 shot）、P10 合成、P11 终审（详见 SPEC-D D-BDD-1）。

---

## 10.C 用户质疑 / 补充事实后的产品行为（PRD-03 → SPEC-D D-BDD-2）

**背景**：v3.15 用户对数据/事实的质疑只能通过通用 `revise` 表达，缺少专门的语义动作和下游影响传播。本节定义两个新动作及其产品层行为。

**质疑（`challenge_claim`）**：
- 触发：用户在 Claim 工作台行级菜单点击"质疑"
- 输入：`claim_id` + 理由（必填）+ 证据 URL（可选）
- 系统行为：原 claim 状态 → `user_disputed`；自动入队高优先级复验；引用该 claim 的下游 artifacts 标 `damaged`（不删除）
- UI 反馈：claim 工作台对应行变红 + 倒计时提示"复验进行中"；下游产物显示 damaged 徽章
- 复验结果不一致时：保留两版 verification_record，等用户裁决

**补充（`supplement_claim`）**：
- 触发：编辑器选中文字后右键"补充事实"，或对话框输入
- 输入：text + claim_type + source_span（指向当前编辑产物）
- 系统行为：ClaimExtractor 创建新 claim（pending）→ 入 `claim_verification` 队列
- 阻断：在新 claim 验证通过前，引用该 claim 的下游阶段（P8/P10/P11 hard blocking）阻塞

**UI 区分**：质疑卡片展示"原 claim vs 用户证据"对比；补充卡片展示新 claim 草案 + 推荐 source_phase。

---

## 10.D 偏好模型扩展（阶段偏好 + 生成后回写）（PRD-04 → SPEC-A A-BDD-2 + SPEC-C C-BDD-3）

**背景**：v3.15 偏好仅有 `global_rules_md / user_preferences_md / project_preferences_md` 三层，无法表达"仅 P5 BGM 阶段适用"等阶段限定偏好；TTSAgent 已实现单点回写但未上提为通用能力。本节扩展偏好作用域并统一生成后回写流程。

**作用域四层**：`global → cross_project → project → stage`，优先级从低到高（`stage > project > cross_project > user > global`，系统约束不可被运行时绕过）。

**阶段偏好示例**：
- `tts.rate_multiplier=0.95`（仅 P4 消费）
- `bgm.target_db=-22`（仅 P5）
- `sfx.intensity_cap=0.6`（仅 P6）
- `storyboard.shot_max_duration_s=15`（仅 P7）
- `chart.line_width=3`（仅 P8）
- `broll.preferred_source=Pexels`（仅 P9）

**注入矩阵**：阶段偏好通过 `STAGE_INJECTION_MATRIX` 常量注入对应阶段的 prompt / 参数；阶段偏好**不得污染**其他阶段（系统校验）。

**生成后回写交互**：
- 触发：阶段完成后调用 `POST /preferences/writeback-suggestions` 返回非空建议时
- UI：`PreferenceWritebackCard` 三栏对比 `当前设置 vs 历史偏好 vs 推荐操作`（keep / update / add_stage_override）
- 用户操作：勾选项 → POST `save_stage_preference`

**v3.15 TTSAgent 流程**：保留行为，底层切换为调用通用 `POST /preferences/writeback-suggestions` 接口（重构，对用户无感）。

---

## 10.E 结构化插入与最小改动改稿（PRD-05 → SPEC-C C-BDD-5）

**背景**：v3.15 ScriptAgent 支持 segment 级修改（A-REV-3）但仅覆盖"重做单段"；BDD `在已有脚本中增插新对比环节` 要求"在已有结构中插入新段落而非整体重写"。本节引入 PatchPlan + DiffAuditor 模型。

**用户可见行为**：

1. **意图表达**：用户对话"在『美国地方债』之后插入『中国地方债』对比段"或类似表述
2. **位置推荐**：未指定具体位置时，系统给出 1-3 个候选 `(after_segment_id, 推荐理由)`，用户从候选中选择
3. **生成范围契约**：仅生成新插入段落，**不重写**其他段落；`max_unrelated_change_ratio ≤ 5%`，超出阻断 commit 并回退到 PatchPlan 阶段
4. **新段落事实**：自动入 ClaimExtractor → Verification Orchestrator；验证通过前阻塞下游 P8/P10/P11
5. **失败兜底**：DiffAuditor FAIL → 保留旧 polished_script，UI 显示具体偏离段落与差异比例

**与 `regenerate_section` 区别**：
- `regenerate_section`：重新生成已存在段落（id 不变，内容全新）
- `insert_section`：新建段落并锚定到 anchor 位置（产生新 segment_id；周边段落仅微调过渡句，受 5% 约束保护）

---

## 10.F 项目列表与阶段回看（PRD-06 → SPEC-A A-BDD-3 + SPEC-E E-BDD-1/E-BDD-2）

**背景**：v3.15 ProjectState 仅有 `current_phase`，用户回到项目后无法快速定位到"曾经到达的最高阶段"，也无法完整回看已完成阶段的所有信息（产物 / Reviewer / Gate / Claim / 偏好 / 历史）。本节扩字段并新增聚合视图。

**用户可见行为**：

1. **项目列表**：每张项目卡片显示 `latest_reached_phase` 与 `current_phase`，若有差异（用户回退后未推进），用角标标识；点击卡片直接跳转到 `latest_reached_phase` 对应阶段
2. **历史阶段回看**：在工作流页点击任一已完成阶段 → 弹出 `PhaseDetailDrawer`（或独立页），展示 7 个分块：
   - 产物列表（artifact_path + version + 下载/预览）
   - Reviewer 结果（每条 verdict + notes）
   - Gate 结果（每条 check pass/fail）
   - Claim 快照（claim_id + 状态 + blocking_level）
   - 偏好快照（scope + key + value）
   - 与上一版本 diff（增/删/改清单）
   - 操作历史时间线（task_ledger 子集 + user_action）
3. **只读 vs 编辑**：历史阶段默认 `read_only=true`，所有编辑入口禁用；显式按"从此阶段继续修改"按钮 → 二次确认 → POST `/revert` → 切换为编辑模式（current_phase 回退）

---

## 10.G 分镜精确拆解 anchor 化（PRD-07 → SPEC-D D-BDD-4 + SPEC-E E-BDD-4）

**背景**：v3.15 D-REV-2 实现了 shot 独立存储与 `regenerate_shot` 动作，但未约束 shot 与口播段落的对齐关系，存在拆分后"画面与口播脱节"的风险。本节强制锚点字段并定义预览态/生产态切换。

**强制字段（每个 shot.json 必须含）**：
- `anchor_text`：shot 对应的口播原文片段（≤ 200 字）
- `script_span_id`：引用 `polished_script.segments[].segment_id`
- `start_char` / `end_char`：在 polished_script 全文中的字符偏移
- `split_from_shot_id?`：拆分自哪个父 shot
- `downstream_bindings`：`{p8_template_shot_id?, p9_broll_shot_id?, p10_track_ref?}`

**拆分约束**：父 shot 的 `[start_char, end_char]` = 所有子 shot 区间并集；子 shot 之间不得字符重叠；子 shot 时长之和 = 父 shot 时长（容差 ≤ 100ms）。违反任一项 StoryboardReviewer FAIL。

**编辑器 UI**：
- 双栏：左侧 polished_script（含 anchor 高亮），右侧 shot 卡片画廊
- 选中 shot → 左侧自动高亮对应 anchor_text 区间
- 拖拽分隔线在 anchor_text 区间内"切一刀"创建子 shot（产生 2 个新 shot.json）
- shot 卡片显示 scene_type 徽章 + 时长 + claim 数量 + 占位预览 + 「预览态 / 生产态」chip

**预览态 vs 生产态**：
- 预览态（P7 阶段）：480p、跳过动画、无 SFX/BGM、单帧 ≤ 500ms
- 生产态（P10+）：1080p、完整动画、走 P10 合成
- 两态共享 data + axis_spec + style_overrides，禁止偏离

---

## 10.H 图表请求闭环（PRD-08 → SPEC-C C-BDD-6 + SPEC-E E-BDD-5）

**背景**：v3.15 无图表请求专用流程，用户说"画一张黄金价格折线图"只能落到 `inject_subtask` 通道，缺少澄清/取数/验证/样式确认的状态机。本节引入 ChartRequest 五步闭环。

**状态机**：`awaiting_clarification → fetching → awaiting_verification → awaiting_confirmation → rendering → completed`（含 `cancelled` / `failed` 终态）。

**用户可见行为**：

1. **澄清阶段**（`awaiting_clarification`）：缺失字段时 `ChartConfirmDialog` 显示问题列表，每次最多问 2 项；优先级：`time_range / granularity > entity > unit / comparison_targets`
2. **抓取阶段**（`fetching`）：调用金融数据服务 → 抓到的每条数据序列写入 `Claim{type='data'}` → 入 `claim_verification` 队列
3. **确认阶段**（`awaiting_confirmation`）：
   - 数据预览（折线图缩略 + 时间范围 + 频率 + 单位 + 来源）
   - 来源徽章：已验证（绿）/ 未验证（红，**禁止确认**）
   - 坐标轴编辑：`x_axis / y_axis` 可调（min/max/zero_based/label/unit）；自动生成算法见 SPEC-F F-BDD-2
   - 样式编辑：`line_width / line_color (palette 选择器) / smooth / background_color / grid_visible / show_source_label / animation_duration_ms`
   - 颜色选择限制在 `style_lock.color_palette` 内
   - 底部按钮：上一步澄清 / 取消 / 确认渲染
4. **渲染阶段**（`rendering`）：进入 Remotion 渲染（详见 TECH_PLAN §18.x）
5. **失败/降级**：数据源不可用 → 转人工或允许"占位预览"（带显著标记），但**禁止进入 P10 生产**

---

## 10.9 v3.16-BDD 验收门禁（产品视角）

| 验收 | 门禁 | 阻塞级别 |
|---|---|---|
| 安全分类误杀率 < 5%、漏放率 < 1% | 10.A | hard |
| Claim 工作台所有 hard unverified 数为 0 | 10.B / 10.C | 阻塞 P8/P10/P11 推进 |
| 阶段偏好不污染其他阶段（单测 + 集成测试覆盖） | 10.D | hard |
| insert_section 后 DiffAuditor PASS | 10.E | 阻塞 commit |
| 项目卡片点击 100% 跳转到 `latest_reached_phase` | 10.F | hard |
| 每个含数据/事实的 shot 有非空 `claim_refs` | 10.G | 阻塞 Gate-P7 |
| ChartRequest 完成时所有 chart-bound claims 已 verified | 10.H | 阻塞 rendering |

---

**PRD v3.3 + v3.16-BDD 第十部分 结束。**

---

# 附录：技术设计索引

以下内容在 V3.3 PRD 中原已存在，但因属于技术实现/工程架构/运维部署范畴，已从本需求文档中移除以保持 PRD 的业务聚焦。各项内容的权威位置如下：

| 原 PRD 章节 | 内容 | 现位置 |
|---|---|---|
| 第二部分：整体架构 | 系统分层图、服务进程划分（Docker Compose 3 服务）、存储选型 | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) |
| 第三部分 §3.1：三层编排架构 | Agent 编排模型、三层架构（FSM / Router / Producer-Reviewer） | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) |
| 第三部分 §3.3：Task Ledger | 数据结构、字段清单、Task 类型表、生命周期主循环、Phase 模板格式 | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) |
| 第三部分 §3.4：上下文注入规则 | IntentRouter prompt 模板、token 预算、注入规则 | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) |
| 第三部分 §3.5：通用子任务 Agent | ResearchAgent / DataVerifyAgent / CrossCheckAgent 输入输出定义 | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) |
| 第四部分 §4.2：目录结构 | `data/` 目录树、`.env` 文件清单 | [`docs/specs/SPEC-B-infra-deploy.md`](specs/SPEC-B-infra-deploy.md) |
| 第四部分 §4.3：project_state.json | 完整 JSON Schema | [`docs/specs/SPEC-A-contracts.md`](specs/SPEC-A-contracts.md) |
| 第八部分：异步任务与长作业 | AsyncTaskManager 架构、`async_tasks` 表结构、崩溃恢复 | [`docs/TECH_PLAN_v3.3.md`](TECH_PLAN_v3.3.md) / [`docs/specs/SPEC-B-infra-deploy.md`](specs/SPEC-B-infra-deploy.md) |
| 第九部分 §9.3：事件归档 | events 表持久化 | [`docs/specs/SPEC-A-contracts.md`](specs/SPEC-A-contracts.md) |
| 第十部分：部署与运维 | Docker Compose 配置、`.env` 示例、Pre-flight 检查清单 | [`docs/specs/SPEC-B-infra-deploy.md`](specs/SPEC-B-infra-deploy.md) |

**TPRM 交叉引用**：
- 技术方案决策记录：`docs/TECH_PLAN_v3.3.md`
- 所有 SPEC 文档索引：`docs/specs/`
- Agent 行为规格：`docs/specs/SPEC_REVISION_REQ_v3.16_2026-04-17.md`
- BDD↔文档反向映射：`docs/specs/BDD_DOC_MAPPING_v3.16_2026-04-17.md`
- 开发导航：`CLAUDE.md`

