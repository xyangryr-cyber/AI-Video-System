# Web 交互式视频制作系统 — 技术方案 (v3.12 精简版)

> 完整版（含代码示例、参数数据表、变更叙事）见 git history 中本文件的上一版本，或 `TECH_PLAN_v3.3_full.md` 备份。
> 配套文档: [PRD v3.3](./PRD_v3.3_Web交互式视频制作系统.md)、[SPEC v3.11](./SPEC_v3.3.md)
> 本文档仅保留**架构决策、技术选型理由、技术方案定义**。代码块、参数表、详细 schema、验收清单等数据内容已移除，以章节索引指向原文档。

---

## 0. 设计哲学

1. **流程是死的、内容是活的** — 12 阶段 FSM 由确定性代码控制；LLM 只负责在每一格填内容
2. **状态全放在数据库里** — SQLite 为单一权威状态源；Agent 每次调用都是"新员工上岗"
3. **过程全程直播** — WebSocket 实时推送 Agent 活动、耗时、成本
4. **数据必须可追溯** — 每个数据点有信任等级标记(user_verified/source_verified/llm_generated)
5. **精确数据程序化获取** — 历史行情等批量数据通过金融 API 获取，不让 LLM 猜测

**一条红线**: 凡是决定"下一步做什么"的逻辑，必须写在代码里；LLM 只决定"这一步的内容长什么样"。

**V1 规模**: 单机私有化部署，3 个 Docker 容器（前端 / API / 后台 Worker），单用户，单项目单 tab 编辑。

---

## 1. 架构决策表

| 抉择 | 选了什么 | 为什么不选另一种 |
|---|---|---|
| Agent 编排模型 | **确定性 FSM 骨架 + 无状态 LLM 填充**（对齐 Manus / Temporal / MS task-ledger 模式） | 纯 Agent 自主决策（如 AutoGPT 模式）在生产里不稳定、无法审计、容易打转 |
| 状态存储 | **SQLite 单一权威 + 文件系统存大产物 + 文件只读导出快照** | 双写（DB + JSON）会产生一致性裂缝；纯文件 JSON 难以并发和查询 |
| Agent 是否长存 | **完全无状态，每次调用即函数调用** | 长存 Agent 实例会让"AI 记住什么/忘记什么"变成隐性状态，崩溃不可恢复 |
| 任务调度粒度 | **Task Ledger（动态任务账本）** — 阶段内是动态可增删的任务列表 | 静态 DAG 无法支持用户中途插入子任务；完全自由又失去骨架的确定性 |
| 长作业执行 | **Huey (SqliteHuey) + 单 worker 顺序跑** | Huey 内置心跳/重试/超时,仍用 SQLite 后端不引入 Redis |
| 推进门禁 | **硬编码 GateKeeper + 偏好确认卡片** | 让 LLM 自己判断"能不能推进"太危险 |
| 前端实时更新 | **WebSocket 事件流（推为主）+ REST 拉兜底** | 纯轮询延迟高；纯 WS 断线会丢事件 |
| 偏好学习 | **每个阶段过门禁时由 PreferenceExtractor 抽取 + 用户显式确认** | 隐式学习容易把用户一次性吐槽当长期偏好 |
| LLM 调用层 | **LiteLLM 统一接口 + Instructor 结构化输出** | LiteLLM 统一多供应商调用 + token 计费;Instructor 替代手写 JSON 解析+重试+schema 校验 |
| 模型路由 | **高风险→Claude,执行→豆包** | GateKeeper/Reviewer/Router 用 Claude 保质量;Producer 初稿/子任务用豆包降成本 |
| Reviewer 检测策略 | **双层架构: L1 程序化→L2 LLM 语义** | ~70% 检查是确定性信号处理,不需要 LLM;L1 先跑(0 成本, ms 级),全 PASS 才进 L2 |
| Canonical Timeline | **P4 产出 `timeline.json` 为全链路唯一时间源** | 各阶段独立读时间轴→累积漂移导致音画不同步 |
| 段落级依赖追踪 | **每个产物按 segment 维护依赖图,修改只标记受影响 segment** | Phase 级回退是 O(N) 重做成本;segment 级追踪让影响范围最小化 |
| 信息密度控制 | **分镜阶段引入 `data_visualization_coverage` 指标和空热量帧检测** | 无密度约束→大量通用 B-Roll 填充→信息密度≈0 |
| 帧级内容对齐 | **分镜 shot 内增加 `animation_keyframes`,图表动画按口播关键词时间点驱动** | Shot 级粒度内画面静态→口播讲"Q1涨了10%"时图表无对应高亮 |
| 叙事节拍 | **P1 大纲标注 narrative beats(hook/context/argument/climax/conclusion),BGM+SFX 据此调整能量级** | 只做情绪匹配不做叙事节奏匹配→BGM 在叙事转折点不换能量 |
| 全媒体风格贯穿 | **偏好 schema 扩展 visual_style + audio_style 两个结构化子域,支持 per-project theme override** | 偏好只影响文本风格→用户视觉/音频审美无处表达 |
| Producer 流式输出 | **Producer 产物走 SSE/WS 流式传输;Review 异步化** | 2000+字脚本修改用户盯着空白等10s;流式+异步将体感从15-20s降到3-5s |
| 跨阶段一致性审计 | **P7(分镜锁定)和 P10(粗剪完成)各做一次全链路数据一致性审计** | 12 阶段线性管道,Reviewer 只和上一阶段对照→数据错误穿透全流程 |
| 可测试性策略 | **每个 Agent 建 eval set + 骨架级 mock 集成测试 + Prompt 变更 CI 回归** | prompt 改一字全局质量变化不可感知→无回归保障 |
| 财经数据外部准确性 | **数据点三级信任标记(user_verified/source_verified/llm_generated) + FactChecker 实际来源校验 + 口播-画面交叉比对前置到 P8** | 跨阶段一致性审计只保证"一致地错" |
| 风格-内容匹配(先选后做) | **BGM 候选 3 选 1 + B-Roll 搜索增加风格维度 + SFX 素材来源定义 + 配色预览前置** | 只做偏好 schema 扩展不够——用户无法在生产前感知风格是否匹配内容 |
| 审美节点候选选择 | **P4/P5/P6/P8/P9 五个审美关键阶段提供候选选择卡片 UI + 风格锁定门禁** | 用户在审美决策点缺少"选择题"→只能接受或 regenerate |
| 素材供给链韧性 | **SFX 素材来源三级(内置库→Freesound API→用户上传) + BGM 备选源(Mubert API→本地库) + B-Roll 备选源(Pexels→Pixabay→占位图) + 离线兜底** | 单一来源挂了整条管道停;三级降级+离线兜底保证任何网络条件下都能产出 |
| 决策可解释性 | **每个 Agent 决策附带 `decision_rationale` 字段 + 图层分解预览(文字层/数据层/视觉层/音频层独立展示)** | 用户看到最终产物但不知道"为什么这么做"→只能接受或全部重做 |
| 金融数据服务层 | **DataService 程序化获取外部金融数据 → Research Agent 调用 → 结果写入 key_data_point(trust_level=source_verified)** | LLM 不可能记住 120 个月的精确金价;FactChecker 只能校验,不能无中生有 |
| 可视化模板三层架构(P0-12 重构) | **废弃 15 个手写 Remotion 组件,改为: ECharts 动画层(8 种图表动效用原生 animation 配置) + React 社区组件层(Framer Motion/Lottie/社区组件) + Remotion 编排层(时间轴/帧同步/渲染)** | v3.9 设计 15 种手写 Remotion 模板是重复造轮子——ECharts 原生 animation 已覆盖全部图表动效;Framer Motion + 社区组件覆盖信息可视化 |
| 连续动画机制 | **animation_keyframes 扩展为 continuous(起止时间/插值/进度映射) + discrete(时间点/动作/目标) 双模式** | v3.7 keyframes 只支持离散事件;"箭头沿折线逐步画线"需要连续动画 |
| 信息可视化模板族 | **6 类信息模板(新闻卡片/事件时间线/政策对比表/关系连线图/地图标注/引用卡片)通过社区组件实现,不手写 Remotion 组件** | 财经视频不只是图表——新闻、政策、行业格局需要不同可视化模板;React 生态已有成熟方案 |
| 口播语音参数体系 | **全局 voice_params(voice_id+style+style_degree+pitch+volume) + per-segment 覆盖(rate_multiplier/emotion/volume/emphasis_words) + 数字感知降速** | 只有 voice_id + 全局 speaking_rate 相当于"买了高级音响只用音量旋钮" |
| Voice Direction Sheet | **P3 润色稿新增结构化 `voice_direction` 字段,由 StyleAgent 根据内容语义自动生成,P4 TTSAgent 据此生成精确 SSML** | P3 知道内容语义,P4 需要声音参数,但两者之间缺少桥接——影视制作中导演给配音演员"配音方向单" |
| TTS API 抽象层 | **TTSProvider 标准化接口:synthesize(text, ssml_tags, voice_params) → audio_bytes;provider adapter 映射标准参数;不支持的参数优雅降级** | 不同 TTS API 支持的参数差异巨大;不做抽象层换 provider 就要改全链路代码 |
| 音色候选预览 | **P4 取口播前 2 段文本,用 2-3 种音色+风格组合各生成 15 秒预览;复用审美候选机制;选定后锁定 global_voice_params** | 配音是审美决策,不能只指定 voice_id 就一条路走到底 |
| 字幕系统 | **subtitle_style 纳入 theme.json;关键词高亮程序化 regex 检测+颜色映射;逐词动画用 Remotion `<Word>` 组件** | 财经视频的字幕是核心信息承载层——"320 亿"和"47.3%"需要用不同颜色/大小突出 |
| 封面/缩略图生成 | **P11 精剪后自动生成 2-3 个封面候选(复用审美候选机制);Pillow 渲染;输出适配 16:9/3:4/1:1 三种尺寸** | 零视频基础用户不会自己做封面;系统已有全部素材,只缺组合渲染 |
| 多平台适配 | **P0 需求采集增加 target_platform 字段;渲染参数从 target_platform 查表获取;V1 只做 16:9 横版但架构预留画幅参数** | 同一内容发 B站(16:9)和抖音(9:16)需要完全不同的画面布局 |
| 品牌一致性 | **用户级 brand_kit 配置:Logo/片头片尾模板/品牌色板/水印;新建项目自动继承,项目级可 override;P11 程序化叠加** | 金融内容创作者通常有个人品牌;当前方案每次新项目从零选配色 |
| 预览播放器 | **@remotion/player 作为前端预览播放器;支持进度条 seek/帧级步进/倍速/多轨道切换/时间轴标注** | 标准 `<video>` 标签无法满足 10 分钟视频的帧级控制和图层分解预览需求 |
| 错误状态 UX | **错误消息三级分类:🟡 自动处理中→🟠 需要用户选择→🔴 需要重试;用户友好提示替代技术细节** | 零视频基础用户看到"Worker task failed"会不知所措 |
| **【v3.16-BDD】安全护栏** | **SafetyPolicyEngine 在 IntentRouter 前硬拦截:五档决策(allow/clarify/restrict/refuse/转人工);模板配置热更新;事件写 events 表(input_hash 不存原文)** | 缺乏前置安全护栏会让 LLM 即兴回答政治/违法/未验证投资建议;Router 前硬拦截是单一收敛点 |
| **【v3.16-BDD】Claim 一等对象** | **ClaimRegistry 把 fact/data/event/citation/image_backed 提升为系统级一等对象,跨 P2/P7/P8/P9 共享;VerificationOrchestrator 按 claim_type 路由;增量重验;生产阻断 Gate-P8/P10/P11** | 各阶段独立做事实校验导致重复工作和验证状态丢失;统一对象+增量重验避免全量复验 |
| **【v3.16-BDD】偏好四层 scope + 阶段注入矩阵** | **global / cross_project / project / stage 四层;优先级 stage > project > cross_project > user > global;STAGE_INJECTION_MATRIX 常量化决定注入规则;统一回写接口** | 三层 scope 无法表达"仅本阶段适用"的偏好;各阶段独立回写有重复 prompt 工程 |
| **【v3.16-BDD】结构化局部插入** | **PatchPlan 数据结构 + 位置推荐算法(基于大纲/叙事节拍/段落语义) + DiffAuditor(max_unrelated_change_ratio ≤ 5% 校验)** | 全量 regenerate 一段就刷掉整篇是粗暴的;让 LLM 自由改稿可能引入意外修改 |
| **【v3.16-BDD】分镜 anchor 强制锚点** | **shot.json 强制 anchor(anchor_text + script_span_id + start_char/end_char);L1 程序化校验 substring 合法性;预览态(480p/跳动画)vs 生产态(1080p/完整动画)** | 拆分时如果不强制锚点,画面与口播在 P10 合成阶段才发现脱节代价巨大 |
| **【v3.16-BDD】图表请求闭环** | **ChartIntentEngine 状态机:awaiting_clarification → fetching → awaiting_verification → awaiting_confirmation → rendering → completed;AxisSpec 自动生成纯确定性算法;失败时允许"占位预览"但禁入 P10** | "画一张黄金价格折线图"用 inject_subtask 通道丢失了"澄清-取数-验证-确认"的语义节点 |
| **【v3.16-BDD】阶段回看与历史只读** | **ProjectState 增 latest_reached_phase + phase_history[];PhaseDetailView 聚合器;历史阶段默认 read_only,显式 revert 解锁** | 用户回到项目只能看到 current_phase 不够;无聚合视图需分别访问 5-7 个端点 |
| **【v3.17】主音频产物链** | **P4 narration_master → P5 bgm_mix_master → P6 final_audio_master;MasterAudioArtifact schema 统一;project_state.master_audio_ref 指向当前权威主音频;下游只读 master_audio_ref** | P4/P5/P6 之前建模为 "segment-only",缺失完整可下载主音频文件链路;canonical timeline 只覆盖时间轴 |
| **【v3.17】P5 混音预览** | **AudioMixPreviewService 输出 bgm_mix_preview(人声+BGM 混合预览);BgmMixRenderer 输出 bgm_mix_master;MusicFitReviewer 升级 L1(harmony/transition/intelligibility)** | 用户默认应在"人声+BGM"语境下判断候选,而非单独听 BGM |
| **【v3.17】P6 Layout + Mix 双层模型** | **sfx_layout_plan.json(全局规划层:时间点/sfx_type/rationale) + sfx_mix_segments.json(局部执行层:分段混音文件);Step2 执行前必须 user_confirmed_layout=true** | 音效设计需要全局规划(叙事节奏)和局部执行(分段混音)两个独立关注点 |
| **【v3.17】P7A 物料准备子阶段** | **P7 与 P8 之间新增 P7A StoryboardAssetSupplement;三角色:StoryboardAssetPlanner(LLM) → MaterialFetcher(程序化) → MaterialVerifier(L1+L2);Gate 7A:required_materials 全 verified 才进 P8** | P8 渲染时临时找素材导致流程中断和质量不可控;前置物料准备让渲染阶段只消费不搜索 |
| **【v3.17】Chart Material Contract** | **chart_material schema 作为 P7A 产物:metric_name/date_range/granularity/source/chart_spec/axis_spec;P8 模板优先使用 chart_material 而非自由文本** | FinancialDataService + 模板 schema 之间缺"分镜需求→渲染输入"的中间 contract |
| **【v3.17】P8 严格消费 + 事实/工程降级二分** | **MaterialReadinessCheck 前置校验;KeyframeRenderAgent 禁外部 HTTP 出站;render_failed→工程降级(默认文字卡继续);material_missing/unverified→事实阻塞(回跳 P7A)** | 区分"渲染技术失败"(可降级继续)和"素材事实缺失"(必须回退)——混淆二者导致错误内容进入视频 |

> **机制细节**: v3.16-BDD 各子系统(SafetyPolicyEngine / ClaimRegistry / 偏好四层 / PatchPlanner / StoryboardShotAnchor / ChartIntentEngine / PhaseDetailView / 增量重验时序)的详细数据流、状态机、算法、失败模式见原文档 §22.A-§22.H。
> **v3.17 机制细节**: 主音频链 schema、P5 混音/MusicFitReviewer、P6 Layout/Mix 双层、P7A 三角色、Chart Material Contract、P8 降级二分、前端 State 契约的详细定义见原文档 §23.A-§23.H。

---

## 2. 系统分层

```
 ┌─────────────────────────────────────────────────────────┐
 │ 前端 (Next.js + TS)                                      │
 │  · 项目列表页  · 工作流页(双栏)  · Agent 活动流面板       │
 └────────────┬──────────────────────┬─────────────────────┘
              │ HTTP REST            │ WebSocket(实时)
 ┌────────────▼──────────────────────▼─────────────────────┐
 │ API 层 (FastAPI + uvicorn)                               │
 │  REST: 项目 CRUD / 产物下载 / 状态查询 / Pre-flight       │
 │  WS  : 对话消息 / Agent 事件流 / 长任务进度订阅           │
 └────────────┬─────────────────────────────────────────────┘
              │
 ┌────────────▼─────────────────────────────────────────────┐
 │ WorkflowEngine (V1 合并为单类，内部纯函数调用)            │
 │  · 12 阶段 FSM     · GateKeeper 校验                      │
 │  · Task Ledger CRUD · 任务分派 / 异步任务提交 / 事件广播  │
 └────────────┬─────────────────────────────────────────────┘
              │
 ┌────────────▼─────────────────────────────────────────────┐
 │ Agent 执行层 (全部无状态函数调用)                         │
 │  · IntentRouter (意图识别)                                │
 │  · 12 × Producer Agent (需求/大纲/脚本/...)               │
 │  · Reviewer 集群 (双层: L1 程序化检测→L2 LLM 语义审查)   │
 │  · 通用子任务 Agent (Research/DataVerify/CrossCheck)      │
 └────────────┬─────────────────────────────────────────────┘
              │
 ┌────────────▼─────────────────────────────────────────────┐
 │ 数据服务层 (DataService)                                  │
 │  · FinancialDataService (金融数据: Yahoo Finance /        │
 │    Alpha Vantage / 东方财富, 带本地缓存)                  │
 └────────────┬─────────────────────────────────────────────┘
              │
 ┌────────────▼─────────────────────────────────────────────┐
 │ 持久化层                                                  │
 │  SQLite (权威): projects, phases, task_ledger,            │
 │                 async_tasks, events, agent_call_log,      │
 │                 preferences, system_status                │
 │  文件系统(权威大产物): 脚本 md / 音频 / 图片 / 视频       │
 │  文件系统(只读导出): snapshot.md / project_state.json     │
 └───────────────────────────────────────────────────────────┘
```

---

## 3. 核心数据流

### 3.1 用户修改请求

```
浏览器 → WS → API → Router(Claude Haiku, 3s超时) → WorkflowEngine 追加 task
  → Dispatcher 调度 Producer Agent → 产物写入 → phase.artifact_version++
  → 自动追加 review task → 事件广播 → 前端渲染
```

### 3.2 长任务(TTS/渲染)

```
用户点击 → API 创建 async task → AsyncTaskManager → Huey worker 拉取执行
  → 每 5s 刷新 heartbeat + 广播进度 → 用户可关浏览器
  → 完成时同事务更新 task_ledger + async_tasks + events
```

### 3.3 阶段推进

```
POST /projects/{id}/advance (不走 Router)
  → 检查偏好确认 → 未确认则 PreferenceExtractor → 候选卡片 → 用户确认
  → GateKeeper.check(phase) → 通过则 FSM.transition → 初始化新阶段 task_ledger
```

### 3.4 Producer 流式输出 + Review 异步

```
Router 识别意图 → 前端乐观更新 → Producer SSE/WS 流式推送 → 打字机效果
  → Producer 完成 → 异步提交 Review → 前端显示"审核中..."badge
  → Review 完成 → badge 更新,不阻塞用户操作
```

---

## 4. 技术栈与选型理由

| 组件 | 选型 | 理由 |
|---|---|---|
| 前端框架 | Next.js + TypeScript | SSR + 路由开箱即用;类型安全 |
| 实时通信 | WebSocket (FastAPI 原生) + REST 兜底 | 推拉结合对抗断线丢事件 |
| 后端框架 | FastAPI + Pydantic | 天然结构化 schema 校验,与 LLM JSON 输出对齐 |
| 进程模型 | uvicorn(API) + 独立 worker 进程 | 长任务不能阻塞 Web 请求线程 |
| 数据库 | SQLite | 单机私有化最省心;WAL 模式下读写并发够用 |
| 长任务队列 | Huey (SqliteHuey backend) | 内置心跳/重试/超时;仍用 SQLite 不引入 Redis |
| LLM 统一调用 | LiteLLM + Instructor | 统一 Claude/豆包接口 + token 计费 + 自动 JSON 解析+schema 校验+重试 |
| LLM 模型路由 | Claude (Reviewer/GateKeeper/Router) + 豆包 (Producer/SubTask) | 高风险决策用 Claude;执行类用豆包降成本 |
| TTS | 外部 API,通过 TTSProvider 抽象层调用 | 不自建;provider adapter 映射标准参数,不支持的优雅降级 |
| 视频渲染 | ECharts (原生动画图表) + Framer Motion/Lottie (信息可视化动效) + Remotion (时间轴编排/帧同步/最终渲染) / ffmpeg-python (合成) / Pillow (静态图) | 三层架构:图表动效零自建组件;社区方案覆盖信息可视化;Remotion 只做编排 |
| 金融数据 API | Yahoo Finance + Alpha Vantage + 东方财富 (akshare) | 三级降级;本地 SQLite 缓存;全部程序化获取 |
| 音频检测 | pydub + ffprobe + pyloudnorm | 确定性信号处理替代 LLM 猜测;EBU R128 响度标准化 |
| 字幕对齐 | Whisper (whisper-base/small, 本地运行) | 强制对齐替代估算,字幕精度从 80% 提升到 95%+ |
| 字幕渲染 | Remotion `<Word>` 组件 + theme.json subtitle_style | 逐词动画+关键词高亮;样式从 theme 读取 |
| B-Roll 素材搜索 | python-pexels + pixabay-python SDK | 封装分页/速率限制/错误重试,替代裸 HTTP |
| 封面生成 | Pillow (背景合成+文字渲染) | 轻量级图片合成,复用已有依赖 |
| 预览播放器 | @remotion/player | 复用 Remotion 组件体系;支持帧级控制 |
| 容器化 | Docker Compose (3 服务) | 单命令部署;Volume 映射便于 host 级备份 |

**为什么用 Huey 而不是 Celery/Redis**: SqliteHuey 后端把队列数据存在 SQLite 里,与业务数据同一个 DB 文件,事务可一并提交。内置心跳、重试、超时、定时任务,V1 单机单 worker 场景比 Celery+Redis 轻量一个数量级。

---

## 5. 并发与一致性模型

- **单项目单 tab**: 前端检测到同项目第二个编辑页,提示回原 tab
- **单 Huey worker 顺序跑 async 任务**: `workers=1`;出队顺序由 Huey 管理
- **事务边界**: Worker 完成任务时在同一事务内更新 `task_ledger` + `async_tasks` + `events`
- **乐观锁防 cancel 竞态**: worker 写回结果时 `WHERE status IN (running,queued)`
- **心跳超时兜底**: 参数表见原文档 §5（`heartbeat_interval_sec=5 / scan_interval_sec=30 / stale_threshold_sec=task_timeout_sec+60 / default_max_attempts=3`）

**口径统一规则**: 任何自然语言描述心跳/扫描/超时须指回参数表,禁止未挂钩参数名的模糊表述。

---

## 6. Agent 上下文注入规则

IntentRouter 每次调用严格按模板构造 prompt,不累积跨调用历史:

```
[System] 你是视频制作项目第 {current_phase} 阶段的意图识别助手...
[项目元信息] 标题/分类/时长/当前阶段/阶段目标
[当前阶段主产物快照]  ≤ 2000 tokens
[当前 Task Ledger 摘要] ≤ 800 tokens
[本阶段最近 N 轮对话]   固定 N=6
[用户偏好规则]         三层合并,≤ 20 条 / 1200 tokens
[可用 actions]         revise / regenerate / inject_subtask / clarify
[用户本轮输入]         原文
[输出] 严格 JSON
```

三条铁律:
1. 跨阶段 turn 历史清空(只保留偏好层累积)
2. 超时或 JSON 解析失败 → 回退为 `clarify`
3. Router 模型由 `model_config.json` 显式指定,换模型前须在 100 条标注集上复跑,连续两周 <85% 才允许升级

---

## 7. 可观测性

每次动作须留下四种可观测证据:

| 证据类型 | 存在哪里 | 查看方式 |
|---|---|---|
| **状态** | SQLite 表 | `GET /projects/{id}/state` API |
| **事件** | SQLite `events` 表 + WebSocket 广播 | 前端 Agent 活动流面板 |
| **LLM 调用审计** | SQLite `agent_call_log` | 按 project_id 和 agent_name 聚合查询 |
| **产物文件** | `data/projects/{id}/phase_X/*` | 文件系统 |

**成本可观测**: `agent_call_log` 按 project_id 和 phase 聚合 token 和金额;V1 目标 P50 ≤ $8 / P90 ≤ $15;超阈值只告警不熔断。

**脱敏规则**: 所有入库 prompt/response/events 经中间件脱敏。SECRET_REGEXES 清单见原文档 §7（7 条 regex,覆盖 sk-* / Bearer / api_key / AWS / GitHub / Slack / password 模式）。超过 8KB 文本做摘要化。`scripts/leak_scan.py` 每日抽样回归。

---

## 8. 失败与降级路径

| 失败场景 | 处理 |
|---|---|
| Producer Agent 生成失败 | 自动重试(默认 3 次);全部失败后 task 置 failed,前端红色标注 + 手动重试按钮 |
| Reviewer 判 FAIL | 不阻塞账本,但门禁卡住;前端显示 `blocking_issues[]` |
| Router JSON 解析失败 / 超时 | 回退为 `clarify` |
| 连续 2 次 clarify | 前端展示 4 个动作候选按钮兜底 |
| TTS/渲染等外部 API 挂了 | Pre-flight 标记 degraded → Router 对依赖该 API 的请求 clarify 告知不可用 |
| Worker 崩溃 | Huey 内置重试机制自动处理;崩溃恢复时序见原文档 §8.1（与 SPEC D.4.1/D.4.3 对齐） |
| DB 文件损坏 | 从 `app.sqlite3.bak` 恢复;绝不从 `project_state.json` / `snapshot.md` 反向回写 |
| 连续 5 次 regenerate 仍不满意 | 前端引导"回到上一阶段改输入"或"冻结进入人工编辑" |
| 回退到 Phase X | Phase X+1~current 产物标记 `invalidated`;V1 回退前展示受影响 segment 数量和预估成本 |

**原则**: 失败必须可见、可恢复、可审计。

---

## 9. 部署与环境

3 服务 Docker Compose: `web` (Next.js, :3000) + `api` (FastAPI, :8000) + `worker` (Python, 单 worker)

- **共享 Volume**: `./data/{config,users,projects,logs,db}`
- **敏感配置**: `.env` 文件(600 权限,不进 git),通过 `env_file:` 注入容器
- **非敏感配置**: `data/config/model_config.json`
- **启动**: `docker compose up -d` → `http://localhost:3000`
- **Pre-flight Check**: API 启动时跑一次,结果 24h 有效写入 `system_status`;关键项失败阻塞,可降级项失败 Banner 提示

---

## 10. 里程碑 → 见原文档 §10

---

## 11. 风险登记册 → 见原文档 §11

---

## 12. 与 PRD 的对应关系

TECH_PLAN 回答"为什么这么设计",SPEC 回答"做到什么算做完了"。完整需求→规格→验收追溯见 SPEC 文档。每条 SPEC 带: PRD 溯源 / 精确规格 / 动机 / 可观测输出 / 验收断言。

---

## 13. 变更历史索引

每版本仅列架构决策/技术选型层面的变更。实现细节、代码块、参数表、验收清单见原文档对应章节。

| 版本 | 架构决策变更 | 原文章节 |
|---|---|---|
| v3.3→v3.4 | 无架构决策变更(仅参数对齐 SPEC D.4.1) | §13 |
| v3.4→v3.5 | LiteLLM+Instructor; Huey; pydub/ffprobe/pyloudnorm; Whisper 强制对齐; ECharts+Remotion 混合; ffmpeg-python; 多模型路由(Claude/豆包) | §14 |
| v3.5→v3.6 | 双层 Reviewer(L1 程序化→L2 LLM); 5 个 Producer 子步骤程序化分离 | §15 |
| v3.6→v3.7 | 信息密度控制; 帧级内容对齐; 叙事节拍; 全媒体风格贯穿; Canonical Timeline; Producer 流式+Review 异步; 段落级依赖追踪; 可测试性策略; 跨阶段一致性审计 | §16 |
| v3.7→v3.8 | 数据点三级信任标记; FactChecker 升级为实际来源校验; 口播-画面交叉比对前置到 P8; 风格-内容匹配(先选后做); 审美节点候选选择 UI; 素材供给链韧性; 决策可解释性与图层预览 | §17 |
| v3.8→v3.9 | 金融数据服务层(DataService); 可视化模板三层架构(P0-12); 连续动画机制(continuous+discrete 双模式); 信息可视化模板族(6 类,社区组件方案) | §18 |
| v3.9→v3.10 | 全局 voice_params 扩展; per-segment 语音覆盖; 数字感知降速(SSML 词级 prosody); Voice Direction Sheet; TTS API 抽象层(TTSProvider); 音色候选预览 | §19 |
| v3.10→v3.11 | P0-12 根本性重构:废弃 15 个手写 Remotion 组件,改为 ECharts 动画层 + React 社区组件层 + Remotion 编排层三层架构;模板发现与搭建能力 | §20 |
| v3.11→v3.12 | 字幕系统设计; 封面/缩略图生成; 多平台适配(target_platform); 品牌一致性(brand_kit); 预览播放器(@remotion/player); 错误状态 UX 三级分类; TemplateProps TS 接口; EChartsFrameController 帧级映射; 社区组件选型固化(react-chrono/@nivo/react-simple-maps); CandidateSelector 通用组件 | §21 |
| v3.12→v3.16-BDD | SafetyPolicyEngine(5 档决策); ClaimRegistry + VerificationOrchestrator(claim 一等对象,增量重验); 偏好四层 scope + STAGE_INJECTION_MATRIX; PatchPlanner + DiffAuditor(≤5%); StoryboardShotAnchor(预览态/生产态); ChartIntentEngine 状态机; ProjectState.latest_reached_phase + PhaseDetailView; 用户质疑增量重验时序 | §22 |
| v3.16-BDD→v3.17 | 主音频产物链(narration_master→bgm_mix_master→final_audio_master); P5 混音预览(AudioMixPreviewService + MusicFitReviewer 升级); P6 Layout+Mix 双层模型; P7A StoryboardAssetSupplement(三角色+Gate 7A); Chart Material Contract; P8 严格消费+事实/工程降级二分; 前端 State+下载协议补齐 | §23 |

---

> **本文档所有数值参数均以 SPEC D.4.1 为权威源。若 TECH_PLAN 与 SPEC 出现不一致,以 SPEC 为准。**
