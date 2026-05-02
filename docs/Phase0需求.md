# Phase 0: 需求定义 — 完整需求规格文档

> **来源**: PRD v3.3 §7.2 + §2.1 + §3.1 + §5.2-5.3 + §6.1-6.3 + §8.1-8.2 + v3.16-BDD §10
> **定位**: 自包含、可实现。开发人员仅凭本文档即可实现 Phase 0 全部功能。
> **日期**: 2026-04-30

---

## 目录

- [1. Phase 0 定位与概述](#1-phase-0-定位与概述)
- [2. 项目创建与 Phase 0 入口](#2-项目创建与-phase-0-入口)
- [3. RequirementsAgent（制作 Agent）](#3-requirementsagent制作-agent)
- [4. CompletenessReviewer（审核 Agent）](#4-completenessreviewer审核-agent)
- [5. Phase 0 用户交互](#5-phase-0-用户交互)
- [6. Gate 0 门禁与偏好确认](#6-gate-0-门禁与偏好确认)
- [7. 前端 UI 规格](#7-前端-ui-规格)
- [8. 数据持久化](#8-数据持久化)
- [9. 事件流](#9-事件流)
- [10. 边界条件与错误处理](#10-边界条件与错误处理)
- [11. 安全护栏](#11-安全护栏)
- [12. API 合约](#12-api-合约)
- [13. 阶段回退](#13-阶段回退)
- [14. task_ledger 初始化](#14-task_ledger-初始化)
- [15. 验收清单](#15-验收清单)

---

## 1. Phase 0 定位与概述

### 1.1 在 12 阶段流水线中的位置

```
Phase 0 需求定义  ← 当前阶段
  → Phase 1 内容主线
  → Phase 2 口播脚本(结构化)
  → ... → Phase 11 精剪交付
```

Phase 0 是用户从"我有一个想法"到"系统理解我要做什么视频"的关键入口。



## 2. 项目创建与 Phase 0 入口

### 2.1 触发条件

用户在 `/projects/new` 页面：
1. 输入标题（非空）
2. 输入自然语言描述（≥10 字）
3. 点击"提交"按钮

后端接收后初始化项目，自动进入 Phase 0。

项目初始化参数：

| 参数 | 来源 | 说明 |
|------|------|------|
| 标题 | 用户输入 | 项目名称，非空 |
| 自然语言描述 | 用户输入 | 视频内容描述，≥10 字 |
| `project_id` | 后端自动生成 | 格式 `proj_YYYYMMDD_NNN` |
| `current_phase` | 系统默认 | 初始值 `0`，Phase 0 入口 |
| `status` | 系统默认 | 初始值 `active` |（Status都有哪些？）
| `created_at` | 系统时间 | ISO 8601 时间戳 |
| `latest_reached_phase` | 系统默认 | 初始值 `0` |（取值逻辑是什么？）

以上参数在 `POST /projects` 时一次性写入 SQLite `projects` 表和 `phases` 表（phase_0 行）。

### 2.2 输入校验（前端）

| 校验项 | 规则 | 失败行为 |
|--------|------|---------|
| 标题 | 非空 | 阻止提交，显示"标题不能为空" |
| 描述 | ≥ 10 字 | 阻止提交，显示"描述不能少于 10 个字" |

校验失败时不发 API 请求。



## 3. RequirementsAgent（制作 Agent）

### 3.0 触发时机与前端状态

**触发时机**：用户提交项目创建表单（标题 + 描述）→ `POST /projects` 成功后，后端自动调用 RequirementsAgent 生成 `requirements.json`。

**前端所处页面**：用户提交后，页面立即跳转到 `/projects/{id}`（项目详情页），Phase 0 为该页面的默认视图。

**用户看到的内容**：
（为什么不是项目创建后再跳转）
1. **提交后立即呈现**：
   - 阶段导航栏：Phase 0 高亮（蓝色），其余阶段灰色
   - 任务清单（§7.3）：显示两个任务项，状态分别为 `running` 和 `pending`
   - 对话区：顶部显示用户刚提交的标题和描述作为第一条消息
   - 底部输入框可用，可输入 `revise`/`regenerate` 等指令

2. **RequirementsAgent 运行时**：
   - `generate_artifact` 任务状态变为 `running`，
   - 用户不可编辑标题和描述区域

3. **RequirementsAgent 完成后**：
   - 对话区追加 Agent 回复卡片，展示结构化需求摘要（含澄清问题，如有）
   - `generate_artifact` 任务状态变为 `succeeded`
   - 自动触发 CompletenessReviewer，`review` 任务状态变为 `running`

### 3.1 职责

将用户的自然语言描述转化为结构化视频制作需求 JSON。

### 3.2 输入

| 输入项 | 来源 | 说明 |
|--------|------|------|
| 视频标题 | 用户输入 | 项目标题 |
| 自然语言描述 | 用户输入 | 用户对视频内容的描述 |


### 3.3 核心生成逻辑

RequirementsAgent 仅从用户自然语言中**提取语义信息**（主题、观点、时长范围、平台偏好）。技术参数和分类体系均从配置文件读取，不由 LLM 推断。（提取语义消息的系统提示词是什么？）

**一期配置参数**（统一维护在 `config/platforms.json` 和 `config/categories.json`）：

平台规格表（`config/platforms.json`）：

```json
{
  "platforms": {
    "bilibili": {
      "name": "B站",
      "specs": { "resolution": "1920x1080", "bitrate": "8Mbps", "format": "H.264 MP4" }
    },
    "douyin": {
      "name": "抖音",
      "specs": { "resolution": "1080x1920", "bitrate": "4Mbps", "format": "H.264 MP4" }
    },
    "wechat": {
      "name": "视频号",
      "specs": { "resolution": "1080x1920", "bitrate": "4Mbps", "format": "H.264 MP4" }
    },
    "youtube": {
      "name": "YouTube",
      "specs": { "resolution": "1920x1080", "bitrate": "12Mbps", "format": "H.264 MP4" }
    }
  }
}
```

分类体系表（`config/categories.json`）：

```json
{
  "categories": {
    "金融财经": ["知识科普", "行业分析", "公司分析", "新闻解读", "政策解读"],
    "科技互联网": ["产品评测", "技术科普", "行业趋势", "创业故事"],
    "知识科普": ["历史人文", "科学探索", "心理学", "哲学思考"],
    "社会热点": ["时事评论", "深度调查", "人物专访"]
  }
}
```

**生成步骤**：

1. **提取关键信息**：从用户描述中提取视频主题、核心观点/内容框架、时长范围（如有）、发布平台（如有）
2. **查表补全技术参数**：
   - 根据用户指定的平台（或默认 `bilibili`）从 `config/platforms.json` 读取 specs
   - 根据内容分析匹配 `config/categories.json` 中最合适的 level1 → level2 分类
   - 如用户给出时长范围，计算目标字数范围：目标字数范围 = 目标时长 × 240 × [0.8, 1.2]（默认语速 **240 字/分钟**，在 `config/model_config.json` 中配置）
3. **缺失关键维度 → 提出澄清问题**，而非编造细节

**澄清问题的交互流程**：

1. RequirementsAgent 生成 `requirements.json`（含 `clarification_needed` 字段标记缺失维度）后，Agent 回复卡片中列出澄清问题
2. 前端在对话区渲染澄清问题列表
3. 用户在输入框中回复后，后端 Router（§5.6）将用户消息路由为 `revise` 动作
4. RequirementsAgent 以原 `requirements.json` + 用户回复为输入，执行**二次关键信息提取**：仅从用户回复中提取缺失维度的值，合并入已有结构，不改动已确认字段（如果用户明显要修改已有内容 为什么不能修改）
5. 更新后的 `requirements.json` 回到审核流程

**已确认内容的展示**：

RequirementsAgent 每次生成完成后，前端在对话区显示结构化需求摘要消息

```
┌─ 视频需求确认 ──────────────────────────────────┐
│ 标题: 2024年新能源市场回顾                        │
│ 主题: 分析2024年新能源市场的主要变化和趋势          │
│ 时长: 8-12 分钟                                   │
│ 平台: B站 (1920x1080, 8Mbps, H.264 MP4)           │
│ 分类: 金融财经 > 行业分析                           │
│ 目标字数: 1536 ~ 2880 字                           │
│                                                    │
│ ⚠ 需要你补充:                                      │
│ 1. 你具体想从哪个角度分析？（政策/技术/市场格局）     │
│    [政策角度] [技术角度] [市场格局] [自定义: ___]   │
│                                                    │
│ [修改不准确的内容] [确认无误，继续]                  │
└────────────────────────────────────────────────────┘
```


**自然语言交互过程**（完整时序）：

```
用户输入 "帮我做一个关于新能源市场的视频分析"
  → POST /projects → 后端创建项目
  → RequirementsAgent 生成初版 requirements.json
  → 前端渲染需求摘要（含澄清问题）
  → CompletenessReviewer 审核（可能有 FAIL）
  
用户回复 "从技术角度分析，8-12分钟"
  → Router 识别为 revise
  → RequirementsAgent 二次提取：合并"技术角度""8-12分钟"到已有结构
  → 前端更新需求摘要卡片 
  → 自动追加新 review 任务

用户点击 [确认无误，继续]
  → Router 识别为 request_advance
  → 引导用户点击"确认进入下一阶段"按钮
```

### 3.4 澄清逻辑

RequirementsAgent 始终生成 `requirements.json`（不因信息不完整而阻塞）。缺失的关键维度通过 `clarification_needed` 字段标记。

| 缺失维度 | `clarification_needed` 值 | 澄清优先级 | 示例问题 |
|---------|--------------------------|-----------|---------|
| 具体观点/论点 | `specific_angle` | P0 | "你具体想从哪个角度分析这个话题？" |
| 期望时长 | `duration` | P1 | "你期望视频大概多长？给出一个范围，如 8-12 分钟" |
| 目标平台 | `platform` | P1 | "视频计划发布在哪个平台？（B站/抖音/视频号等）" |
| 分类不明确 | `category` | P2 | "内容更偏向哪个领域？（金融财经/科技互联网/知识科普/社会热点）" |

`clarification_needed` 为空数组时，表示信息完整，产物可直接推进。非空时，前端渲染需求摘要卡片中的澄清问题区域（§3.3）。

### 3.5 输出 Schema

```json
{
  "project_id": "proj_YYYYMMDD_NNN",
  "title": "视频标题",
  "topic": "视频主题描述（≥5字符）",
  "user_input_content": "用户输入的核心内容/观点（非空，含至少一个可识别的观点或论点）",
  "target_duration_minutes": {
    "min": 8,
    "max": 12
  },
  "target_word_count": {
    "min": 1536,
    "max": 2880
  },
  "platform": {
    "primary": "bilibili",
    "secondary": ["douyin"],
    "specs": {
      "resolution": "1920x1080",
      "bitrate": "8Mbps",
      "format": "H.264 MP4"
    }
  },
  "category": {
    "level1": "金融财经",
    "level2": "行业分析"
  },
  "clarification_needed": ["specific_angle"],
  "created_at": "2026-04-30T10:00:00Z"
}
```

各字段取数逻辑：

| 字段 | 取数逻辑 |
|------|---------|
| `target_duration_minutes` | 从用户描述中提取时长范围。如用户说"8-12 分钟"，填 `{"min": 8, "max": 12}`；说"大概 5 分钟"，填 `{"min": 5, "max": 5}`（min == max 表示点值）；未提及则填 `{"min": null, "max": null}`，触发澄清 |
| `target_word_count` | 计算公式：`min = target_duration_minutes.min × speech_rate × 0.8`，`max = target_duration_minutes.max × speech_rate × 1.2`。`speech_rate` 默认 240 字/分钟（从 `config/model_config.json` 读取）。如 `target_duration_minutes` 为 null，word_count 也为 null |
| `platform.primary` | 从用户描述中提取。如用户提到"发B站"，填 `"bilibili"`；未提及时填默认值（`config/platforms.json` 中 `default_platform`，一期默认 `"bilibili"`） |
| `platform.secondary` | 从用户描述中提取。用户提到的非主平台列表；未提及时为空数组 |
| `platform.specs` | **不从 LLM 推断**，直接从 `config/platforms.json` 按 `primary` 查表填入 |
| `category.level1` | LLM 分析内容后从 `config/categories.json` 的 level1 列表中匹配最合适的 |
| `category.level2` | LLM 在选定的 level1 下匹配最合适的子类 |
| `clarification_needed` | 标记仍需用户补充的维度，如 `["duration", "specific_angle", "platform"]`。空数组表示信息完整 |

### 3.6 字段约束

| 字段 | 类型 | 约束 |
|------|------|------|
| `project_id` | string | 格式 `proj_YYYYMMDD_NNN`，后端自动生成 |
| `title` | string | 非空 |
| `topic` | string | 非空，长度 ≥ 5 字符 |
| `user_input_content` | string | 非空，包含至少一个可识别的观点或论点 |
| `target_duration_minutes` | object | `{min, max}`，min ≥ 0，max ≥ min；min 和 max 可同为 null（表示用户未提供时长信息） |
| `target_word_count.min` | number | ≥ 0；target_duration_minutes 为 null 时此值为 null |
| `target_word_count.max` | number | ≥ min；target_duration_minutes 为 null 时此值为 null |
| `platform.primary` | string | 在 `config/platforms.json` 的 `platforms` 键中存在 |
| `platform.secondary` | string[] | 每个值在 `config/platforms.json` 中存在，不含 primary |
| `platform.specs.resolution` | string | 非空，从 `config/platforms.json` 查表填入 |
| `platform.specs.bitrate` | string | 非空，从 `config/platforms.json` 查表填入 |
| `platform.specs.format` | string | 非空，从 `config/platforms.json` 查表填入 |
| `category.level1` | string | 在 `config/categories.json` 的顶层键中存在 |
| `category.level2` | string | 在 `config/categories.json` 的对应 level1 数组值中存在 |
| `clarification_needed` | string[] | 缺少数值维度时列出对应 key；空数组表示信息完整 |
| `created_at` | string | ISO 8601 时间戳 |

### 3.7 字数计算规则

```
target_word_count.min = target_duration_minutes.min × speech_rate × 0.8
target_word_count.max = target_duration_minutes.max × speech_rate × 1.2
```

- `speech_rate` 默认 240 字/分钟，在 `config/model_config.json` 中配置
- 当 `target_duration_minutes.min == null` 时，`target_word_count` 整体为 null，待用户补充时长信息后重新计算

### 3.8 依赖配置

RequirementsAgent 依赖以下配置/数据源：

| 配置项 | 文件路径 | 说明 |
|--------|---------|------|
| 平台规格表 | `config/platforms.json` | 系统支持平台列表及默认规格（分辨率/码率/格式） |
| 分类体系树 | `config/categories.json` | 二级分类结构（level1 → level2 映射） |
| 模型配置 | `config/model_config.json` | 含 `speech_rate: 240`（字/分钟，可配置） |

所有系统级配置参数统一在 `config/` 目录下维护，各 Agent 通过读配置文件获取，不硬编码在 Agent 代码中。

---

## 4. CompletenessReviewer（审核 Agent）
### 4.1 职责
对 RequirementsAgent 输出的 `requirements.json` 做二元判定（PASS / FAIL）。

### 4.2 输入

- `requirements.json`（RequirementsAgent 输出）

### 4.3 审核清单

| # | 检查项 | 校验规则 | FAIL 条件 |
|---|--------|---------|---------|
| 1 | 主题 | 非空，长度 ≥ 5 字符 | 空或过于模糊 |
| 2 | 用户输入内容 | 非空，包含至少一个可识别的观点或论点 | 空 |
| 3 | 目标时长 | `target_duration_minutes` 非 null 时，`min ≥ 0` 且 `max ≥ min` | min < 0 或 max < min |
| 4 | 目标字数 | 如 duration 非 null：`min > 0` 且 `max > min`；如 duration 为 null：word_count 也应为 null | 数据不一致 |
| 5 | 平台主平台 | 至少一个主平台，且在 `config/platforms.json` 中存在 | 未知平台 |
| 6 | 视频规格 | `resolution` / `bitrate` / `format` 均非空，且与 `config/platforms.json` 中该平台的定义一致 | 任一缺失或不一致 |
| 7 | 分类 | `level1` 和 `level2` 均非空，且在 `config/categories.json` 中存在 | 无效分类 |
| 8 | 澄清标记 | `clarification_needed` 数组存在，每个值在已知维度列表（`duration`/`specific_angle`/`platform`/`category`）中 | 未知维度值 |

### 4.4 输出格式

```json
{
  "verdict": "PASS | FAIL",
  "notes": ["warning 或 fail 原因列表"],
  "blocking_issues": ["仅列出导致 FAIL 的项，如 '主题为空或过于模糊'"]
}
```

### 4.5 审核触发

`generate_artifact` 任务完成后自动追加 `review` 任务。用户无需手动触发。

### 4.6 审核失败处理

**任务清单说明**：

任务清单（task_ledger）是 Phase 0 当前阶段内所有系统任务的透明展示。Phase 0 的初始任务包括：
- `generate_artifact`：RequirementsAgent 生成需求 JSON
- `review`：CompletenessReviewer 审核产物



**制作和审核期间的前端显示**：

| 时间段 | 前端显示内容 |
|--------|------------|
| 用户提交后 ~ RequirementsAgent 完成前 | 对话去发出一条消息 "正在分析你的需求..." 加载指示器；任务清单中 `generate_artifact` 状态为 🔄 running |
| RequirementsAgent 完成 ~ CompletenessReviewer 完成前 | 对话区追加需求摘要消息（含澄清问题）；任务清单中 `generate_artifact` 变为 ✅ succeeded，`review` 变为 🔄 running |
| CompletenessReviewer 完成后 | 任务清单中 `review` 更新为 ✅ succeeded（PASS）或 ❌ failed（FAIL） |

**审核失败后的处理流程**：
（审核失败 应该把为什么失败了交给制作Agent 重新制作 直到通过 最多重试3次）
- review 任务 verdict = FAIL → 任务清单中对应条目红色标注（❌ failed）
- 对话区需求摘要卡片底部显示 FAIL 原因（如"缺少具体分析角度"）
- `phase.status` 不进入 `awaiting_user`
- "确认进入下一阶段"按钮保持禁用
- 用户可直接在对话输入框中回复补充信息（触发 `revise`），或输入"重做"（触发 `regenerate`）

---

## 5. Phase 0 用户交互

### 5.1 可用动作

**Router 说明**：Router 是后端的一个轻量级意图分类模块（位于 `src/backend/engine/router.py`）。它接收用户在对话区的自然语言输入，调用一个小型 LLM（或规则匹配）判定用户意图，输出一个动作类型枚举值。Router 不执行任何操作，只负责识别和路由。

**任务可见性**：用户可以在前端项目详情页的**右侧面板——任务清单**中看到 Phase 0 的所有任务及其状态。详见 §7.3。

| 动作 | 触发方式 | Router 识别依据 | 系统行为 |
|------|---------|----------------|---------|
| `revise` | 对话输入修改意见 | 用户消息包含补充信息关键词（如"应该是""改成""补充""从X角度"等），或语义分析判定为修改意图 | 追加 `user_revision` task → RequirementsAgent 以原 JSON + 用户消息为输入重新生成 → artifact_version 自增 → 旧 review 置 `superseded` → 自动追加新 review |
| `regenerate` | 对话输入重做意愿 | 用户消息包含"重做""重新来""不满意""换个方向"等 | 追加新 `generate_artifact` task → 废弃当前 artifact → 从零重新生成 → 旧 review 置 `superseded` |
| `inject_subtask` | 对话输入调研请求 | 用户消息包含"帮我查""搜一下""调研"等 | 追加 `research` task → Dispatcher 调度 ResearchAgent（SLA 180s）→ 结果写入 `task.result_ref` |
| `request_advance` | 对话输入"下一步" | 用户消息包含"下一步""继续""好了""没问题""确认"等 | 前端高亮"确认进入下一阶段"按钮；若条件不满足，按钮禁用并显示原因 |
| `confirm_next` | 点击硬按钮 | 不经过 Router（硬按钮直接触发 API） | 触发 PreferenceExtractor → 用户确认 → GateKeeper 校验 → FSM 推进 |
| `clarify` | Router 无法识别意图 | 用户消息语义模糊，置信度 < 0.6 | 前端显示澄清问题（如"你是想修改需求，还是进入下一阶段？"），不改动账本 |

### 5.3 修改后产物版本管理

每次 `revise` / `regenerate` 完成后：

1. `artifact_version` 自增（如 v1 → v2），新版本 `requirements_v2.json` 写入文件系统
2. 旧版本 `review` 任务状态置为 `superseded`（因为它的审查对象是旧版本产物，已不再有意义）
3. 自动追加匹配新版本的 `review` 任务：
   - `type`: `review`
   - `agent`: `CompletenessReviewer`
   - `target_artifact`: `phase_0/requirements.json`（指向最新版本）
   - `target_version`: 新版本号（如 `v2`）
   - `depends_on`: 刚完成的 `user_revision` 或 `generate_artifact` 任务
   - `status`: `pending`（自动入队，由 Dispatcher 调度执行）

**为什么要自动追加 review**：每次 revise/regenerate 都可能引入新的数据质量问题（如 LLM 修改时破坏了字段约束），因此无论修改多小，都必须重新审核才能推进。这是门禁的硬性要求。

**逻辑示意**：
```
revise 完成 → 旧 review (v1) → superseded
           → 新 review (v2) 自动创建 → queued → running → succeeded/failed
```

### 5.6 `request_advance` 不自动推进

Router 的职责和识别逻辑见 §5.1。

用户在对话中说"好了，下一步"：
- Router 识别为 `request_advance`
- Agent 回复引导用户点击"确认进入下一阶段"按钮
- 系统**不自动推进**——必须用户手动点击硬按钮

---

## 6. Gate 0 门禁与偏好确认

**`preferences_confirmed_at` 说明**：`phases` 表中 phase_0 行的一个时间戳字段。初始值为 `null`。用户首次点击"确认进入下一阶段"时，系统检测到此值为 null 即触发 PreferenceExtractor。用户完成偏好确认（接受/拒绝/跳过）后写入当前时间戳。后续再次点击按钮时，此值非 null，跳过偏好提取环节。

**Phase 0 状态机**：

```
项目创建 → phase_0.status = "active"
  → generate_artifact 完成 → status = "artifact_generated"
  → review 完成 (PASS) → status = "review_passed"
  → 用户点击"确认进入下一阶段" → 触发偏好确认流程
  → 偏好确认完成 → preferences_confirmed_at = now()
  → GateKeeper 校验 → PASS → status = "done" → FSM 推进到 Phase 1
                     → FAIL → status 不变，显示失败原因
```

**GateKeeper 说明**：GateKeeper 是后端 `src/backend/engine/gatekeeper.py` 中的一个**纯函数校验模块**（非 LLM Agent）。它在 FSM 推进到下一阶段前执行门禁检查（§6.2）。所有检查项都是程序化判断（不消耗 LLM token，零成本，零延迟），任何一项不通过即返回 FAIL + 原因列表。

### 6.1 门禁流程

```
用户点击"确认进入下一阶段"（硬按钮 → POST /projects/{id}/advance）
  → 检查 preferences_confirmed_at == null ?
    → YES: API 返回 { action: "confirm_preferences" } → 前端弹出偏好确认卡片 → 用户确认 → API 再调用 POST /projects/{id}/advance
    → NO: 直接进入 GateKeeper 校验
  → GateKeeper 校验
    → PASS: FSM.transition(phase_1) → 返回 { status: "advanced", next_phase: 1 }
    → FAIL: 返回 { status: "blocked", reasons: [...] } → 前端弹窗显示失败原因
```

### 6.2 Gate 0 门禁项

**task 说明**：task 是 Phase 0 流水线中的最小工作单元，记录在 SQLite `task_ledger` 表中。每个 task 有类型（`generate_artifact`/`review`/`user_revision`/`research`）、状态（`pending` → `queued` → `running` → `succeeded`/`failed`/`skipped`/`superseded`）和所属 phase。

**Phase 0 包含的 task 类型**：

| Task 类型 | 触发方式 | 说明 |
|----------|---------|------|
| `generate_artifact` | 项目创建时自动触发 / 用户 `regenerate` | RequirementsAgent 生成 requirements.json |
| `review` | `generate_artifact` 或 `user_revision` 完成后自动触发 | CompletenessReviewer 审核产物 |
| `user_revision` | 用户 `revise` | RequirementsAgent 基于用户反馈修改产物 |
| `research` | 用户 `inject_subtask` | ResearchAgent 执行调研子任务 |

| # | 门禁项 | 检查内容 | FAIL 行为 |
|---|--------|---------|---------|
| 1 | 产物完整性 | `phase_0/requirements.json` 存在且 JSON Schema 校验通过（所有必填字段非空） | 弹窗："主产物生成失败，请手动重试或调整参数" |
| 2 | 审核通过 | CompletenessReviewer 返回 `verdict = PASS` | 弹窗："审核未通过"，列出具体阻塞项 |
| 3 | 无进行中任务 | task_ledger 所有 task 处于终态（`succeeded` / `failed` / `skipped` / `superseded`） | 弹窗："仍有任务正在执行中，请等待完成" |
| 4 | 偏好确认完成 | `phases.phase_0.preferences_confirmed_at` 非空 | 先触发偏好提取流程，而非直接报错 |

### 6.3 PreferenceExtractor（门禁内嵌，非 ledger 任务）

见 PRD §3.1，核心要点：
- **触发**: `POST /projects/{id}/advance` 首次调用，`preferences_confirmed_at == null`
- **不在 task_ledger 中**，由 API 层同步调用
- **输入**: 本阶段对话历史 + user_revision 指令 + 产物 diff + 已有偏好
- **输出**: JSON candidates（每条含 rule / scope_suggestion / evidence / confidence / conflicts_with）
- **硬约束**:
  - `evidence` 不能为空
  - `confidence < 0.6` 不进入 candidates
  - 与已有偏好冲突的必须在 `conflicts_with` 列出
  - `nothing_found: true` 时仍需用户显式点击"跳过"

**示例**：

```
场景：Phase 0 对话历史中，用户两次要求"把时长从 5 分钟改成 8-12 分钟"

PreferenceExtractor 输入：
- 对话片段 1: "太短了，改长一点，8-10 分钟吧"
- 对话片段 2: "不对，8-12 分钟比较合适"

PreferenceExtractor 输出：
{
  "candidates": [
    {
      "rule": "用户偏好中等偏长视频（8-12 分钟区间）",
      "scope_suggestion": "project",
      "evidence": "Phase 0 对话: '改长一点，8-10分钟' → '8-12分钟比较合适'",
      "confidence": 0.82,
      "conflicts_with": null
    }
  ],
  "nothing_found": false
}
```

前端以此渲染偏好确认卡片（§6.4），用户勾选后写入 SQLite `preferences` 表。

### 6.4 偏好确认卡片 UI

**前端呈现形式**：模态对话框（Modal），覆盖在项目详情页上方，背景半透明遮罩。对话框标题"本阶段学到的偏好"，内容区域为可滚动的偏好列表，底部为操作按钮。

```
┌─ 本阶段学到的偏好（请确认） ─────────────────────────────┐
│ Agent 从你本阶段的反馈中总结了 N 条偏好：                  │
│                                                         │
│ ☑ 1. 用户偏好中等偏长视频（8-12 分钟区间）                 │
│    依据: "改长一点，8-10分钟" → "8-12分钟比较合适"        │
│    保存范围: (●) 仅本项目  ( ) 所有项目                    │
│    [编辑]                                                │
│                                                         │
│ ☑ 2. 用户倾向从技术角度分析行业话题                         │
│    依据: "从技术角度分析"                                  │
│    保存范围: (●) 仅本项目  ( ) 所有项目                    │
│    [编辑]                                                │
│                                                         │
│ [全部接受]  [全部拒绝]  [保存勾选项并推进]                  │
└─────────────────────────────────────────────────────────┘
```

**前端实现逻辑**：

1. **Modal 打开**：`POST /projects/{id}/advance` 返回 `{ action: "confirm_preferences", candidates: [...] }` →
   前端渲染偏好确认 Modal。`candidates` 数组长度决定列表项数。

2. **交互规则**：
   - 默认全部勾选
   - 用户可对单条：勾选/取消勾选/编辑文字/切换 scope（项目/全局）
   - "编辑"点击后该条文字变为内联 `<input>`，保存范围 radio 变为可交互
   - "全部拒绝"→ 所有条目取消勾选，后续同"保存勾选项"

3. **"全部接受"后的处理**：
   - 所有条目保持勾选状态
   - `POST /projects/{id}/preferences/confirm`，body 含所有 candidates（含用户编辑后的文字和 scope）
   - 后端按 scope 写入 SQLite `preferences` 表：
     - `scope: "project"` → 写入 `project_preferences_md`
     - `scope: "global"` → 写入 `user_preferences_md`
   - 后端写入 `preferences_confirmed_at = now()`
   - 前端关闭 Modal，自动重新调用 `POST /projects/{id}/advance`
   - GateKeeper 校验通过 → 推进到 Phase 1

4. **"全部拒绝"后的处理**：
   - `POST /projects/{id}/preferences/confirm`，body 中 candidates 为空数组
   - 后端不写入任何偏好记录
   - 后端写入 `preferences_confirmed_at = now()`（标记偏好确认环节已完成，只是无新增偏好）
   - 前端关闭 Modal，自动重新调用 `POST /projects/{id}/advance`
   - GateKeeper 校验 → 继续推进

5. **"保存勾选项并推进"后的处理**：
   - 仅提交勾选的 candidates
   - 后续流程同"全部接受"，但只写入被勾选的条目

6. **`nothing_found` 时的处理**：
   - Modal 内容替换为："本阶段未发现新的偏好规则。"
   - 底部按钮变为：[跳过]
   - 用户点击"跳过" → `POST /projects/{id}/preferences/confirm`（空 candidates）→ `preferences_confirmed_at = now()` → 后续同"全部拒绝"

7. **Modal 关闭后的状态**：`preferences_confirmed_at` 已非 null，`phase.status = "done"`，前端阶段导航栏 Phase 0 图标 → 绿色勾，Phase 1 → 高亮。

### 6.5 Gate 0 通过后

- `phases.phase_0.status = "done"`
- FSM 推进到 Phase 1
- Phase 1 task_ledger 按 `phase_templates.json` 初始化
- 前端：Phase 0 阶段导航图标 → 绿色勾；Phase 1 → 高亮

---


### 7.3 任务清单（Phase 0 初始状态）

任务清单位于项目详情页右侧面板，实时展示当前阶段所有系统任务及其状态。数据来源：`GET /projects/{id}/state` 返回的 `task_ledger` 数组。

**初始状态**（项目刚创建，RequirementsAgent 尚未开始）：

```
┌─ Phase 0 任务清单 ───────────────────────────┐
│ ⏳ 生成需求分析       generate_artifact      │
│ ⏳ 完整性审核          review                  │
└──────────────────────────────────────────────┘
```

**运行中状态**（RequirementsAgent 执行中，review 等待触发）：

```
┌─ Phase 0 任务清单 ───────────────────────────┐
│ 🔄 生成需求分析       generate_artifact  2.3s │
│ ⏳ 完整性审核          review                  │
└──────────────────────────────────────────────┘
```

**完成后状态**（全部通过）：

```
┌─ Phase 0 任务清单 ───────────────────────────┐
│ ✅ 生成需求分析       generate_artifact  3.1s │
│ ✅ 完整性审核          review            0.8s │
└──────────────────────────────────────────────┘
```

任务状态图标：⏳ pending → 🔄 running → ✅ succeeded / ❌ failed / ⬜ skipped / ⤵ superseded。

任务状态通过 WebSocket 或轮询实时更新，无需用户手动刷新。

### 7.4 "确认进入下一阶段"按钮

- 位置：对话区底部
- 文本："确认进入下一阶段 → Phase 1"
- GateKeeper 条件全部满足时 → 高亮可点击
- 条件不满足时 → 灰色禁用，旁显示原因

---

## 8. 数据持久化

### 8.1 文件系统

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求 JSON | `data/projects/{id}/phase_0/requirements.json` | 权威产物文件 |
| 对话历史 | `data/projects/{id}/dialogue/phase_0.md` | 权威对话日志 |
| 子任务记录 | `data/projects/{id}/phase_0/subtasks/` | 子任务过程记录 |

`requirements.json` 的多版本：`requirements_v1.json`, `requirements_v2.json` 等。`artifact_ref` 指向最新版本。

### 8.2 SQLite（权威状态）

| 表 | 关键字段 | Phase 0 相关写入 |
|----|---------|-----------------|
| `projects` | `id, title, status, current_phase, latest_reached_phase, created_at, updated_at` | 项目创建时写入；Phase 0 推进时更新 |
| `phases` | `project_id, phase_number, status, artifact_ref, artifact_version, preferences_confirmed_at, task_ledger` | Phase 0 进入时初始化；推进时更新 status |
| `task_ledger` | `project_id, phase, task_id, type, params, status, created_at, updated_at` | generate_artifact / review / user_revision 等任务的 CRUD |
| `preferences` | `project_id, global_rules_md, user_preferences_md, project_preferences_md, last_candidates_json, last_confirmed_at, updated_at` | 偏好确认后写入 |
| `events` | `project_id, event_type, payload, created_at` | 所有状态变更事件 |
| `agent_call_log` | `project_id, phase, agent_name, model, tokens_input, tokens_output, duration_ms, cost_usd, created_at` | RequirementsAgent / CompletenessReviewer 调用记录 |
| `async_tasks` | `project_id, phase, ...` | Phase 0 通常无异步任务 |

### 10.2 浏览器关闭后恢复

前端重新打开时调用 `GET /projects/{id}/state`：
- API 从 SQLite 读取权威状态
- 合并 async_tasks 最新状态
- 返回完整状态给前端渲染
- 恢复时间 ≤ 10s

### 10.3 服务重启后恢复

- SQLite 是唯一可信状态源
- 所有状态在 DB 中，不在内存
- 重启后 API 从 SQLite 恢复
- 不需要 Agent 参与恢复



---

## 13. 阶段回退
用户可以在前端切换phase查看过程产物 已完成的阶段不再支持修改

---

## 14. task_ledger 初始化

### 14.1 Phase 0 模板（`phase_templates.json`）

```json
{
  "phase_0": {
    "initial_tasks": [
      {
        "type": "generate_artifact",
        "agent": "RequirementsAgent",
        "params": {
          "output_file": "phase_0/requirements.json"
        },
        "depends_on": []
      },
      {
        "type": "review",
        "agent": "CompletenessReviewer",
        "params": {
          "reviewer_type": "Completeness",
          "target_artifact": "phase_0/requirements.json"
        },
        "depends_on": ["generate_artifact"]
      }
    ]
  }
}
```

### 14.2 任务状态流转

```
generate_artifact:
  pending → queued → running → succeeded / failed

review (auto-triggered after generate_artifact succeeded):
  pending → queued → running → succeeded (PASS) / failed (FAIL)

user_revision (user triggers via revise):
  pending → queued → running → succeeded
  → old review → superseded
  → new review auto-created
```



---

> **关联文档**:
> - PRD v3.3: `docs/PRD_v3.3_Web交互式视频制作系统.md` §7.2
> - BDD 测试用例: `docs/BDD_phase_0_requirements_definition.feature.md`
> - Tech Plan: `docs/TECH_PLAN_v3.3.md`
> - SPEC-D Pipeline: `docs/specs/SPEC-D-pipeline-phases.md`
> - SPEC-A Contracts: `docs/specs/SPEC-A-contracts.md`
