# SPEC-P0 Phase 0 需求定义 — 开发模块索引

> **版本**: v1.0
> **日期**: 2026-04-30
> **来源文档**: `docs/Phase0需求.md` (v1.0)
> **测试场景**: `docs/Phase0_Manual_Test_Scenario.md` (v1.0)
> **技术架构**: `docs/TECH_PLAN_v3.3.md` (v3.12)
> **定位**: Phase 0 开发拆分为 8 个独立模块，每个模块实现一个业务闭环，可被测试场景独立验收。

---

## 模块拆分原则

1. **业务闭环**: 每个模块有明确的业务输入和输出，完成一个完整的用户价值链路
2. **可独立验收**: 每个模块对应 `Phase0_Manual_Test_Scenario.md` 中的一个或多个测试用例
3. **技术架构合规**: 所有技术选型符合 `TECH_PLAN_v3.3.md` 的架构决策
4. **HARNESS 合规**: 每个 task card 遵循 `HARNESS.md` §12 的格式和约束

---

## 模块总览

| # | 模块 | 业务闭环 | 复杂度 | 依赖 | 验收场景 |
|---|------|---------|--------|------|---------|
| M1 | 基础设施与项目创建 | 配置就绪 → 项目创建，Phase 0 启动 | L | 无 | 场景 1.1-1.2, 6.1 |
| M2 | 需求生成 Agent | 自然语言 → 结构化 requirements.json | M | M1 | 场景 1.3, 3.1 |
| M3 | 完整性审核 Agent | requirements.json → PASS/FAIL 判定 | M | M2 | 场景 1.4, 3.3 |
| M4 | 意图路由与需求修订 | 用户反馈 → 意图识别 → 产物更新 + 重新审核 | L | M2, M3 | 场景 2, 3.2 |
| M5 | 偏好提取与阶段门禁 | 对话历史 → 偏好学习 → GateKeeper → Phase 1 | L | M3, M4 | 场景 4, 5 |
| M6 | 前端项目创建与需求展示 | 用户操作 → 工作区 UI（导航/任务/需求卡片） | L | M1 | 场景 1, 3, 6.1-6.2 |
| M7 | 前端对话交互与门禁界面 | 对话 + 偏好确认 → 阶段推进 UI | L | M6 | 场景 2, 4, 5 |
| M8 | 实时通信与状态恢复 | 系统事件 → 实时 UI + 断线/重启恢复 | M | M1 | 场景 6.3 |

---

## 依赖关系图

```
M1 (基础设施与项目创建)
 ├── M2 (需求生成 Agent)
 │    └── M3 (完整性审核 Agent)
 │         └── M4 (意图路由与需求修订)
 │              └── M5 (偏好提取与阶段门禁)
 └── M6 (前端项目创建与需求展示)
      └── M7 (前端对话交互与门禁界面)
 └── M8 (实时通信与状态恢复)
```

**可并行开发**:
- M2/M3 链 与 M6 可并行（后端 Agent 链 vs 前端展示层）
- M4 与 M7 可并行（后端路由逻辑 vs 前端对话 UI）
- M8 可在 M1 完成后立即开始（WebSocket + REST 基础设施）

---

## 推荐开发顺序

```
Round 1: M1 (所有模块的前置依赖)
Round 2: M2 → M3 (后端 Agent 链)  ‖  M6 (前端展示层)  ‖  M8 (实时通信)
Round 3: M4 (后端修订流水线)       ‖  M7 (前端对话 UI)
Round 4: M5 (偏好 + 门禁, 收束全部后端逻辑)
```

---

## 与技术架构的对齐

| 架构决策 | 涉及模块 | 对齐方式 |
|---------|---------|---------|
| 确定性 FSM + 无状态 LLM Agent | M2, M3, M4, M5 | Agent 每次调用为纯函数，状态全部在 SQLite |
| SQLite 单一权威状态源 | M1, M8 | 所有状态在 DB，文件系统存大产物 |
| LiteLLM + Instructor | M2, M3, M4, M5 | 所有 LLM 调用走 LiteLLM，Instructor 校验输出 |
| 模型路由（高风险→Claude，执行→豆包） | M2, M3, M4, M5 | Reviewer/GateKeeper/Router 用 Claude；Producer 用豆包 |
| WebSocket 推 + REST 拉兜底 | M8 | 实时事件走 WS，断线走 REST |
| Huey 单 worker 顺序跑 | M2, M3, M4 | Agent task 通过 Huey 调度执行 |
| 双层 Reviewer（L1 程序化→L2 LLM） | M3, M5 | CompletenessReviewer 用 LLM；GateKeeper 为纯函数 |

---

## Task Card 文件清单

| 文件 | 模块 |
|------|------|
| [P0-M1-infra-project-creation.md](P0-M1-infra-project-creation.md) | M1: 基础设施与项目创建 |
| [P0-M2-requirements-agent.md](P0-M2-requirements-agent.md) | M2: 需求生成 Agent |
| [P0-M3-completeness-reviewer.md](P0-M3-completeness-reviewer.md) | M3: 完整性审核 Agent |
| [P0-M4-intent-router-revision.md](P0-M4-intent-router-revision.md) | M4: 意图路由与需求修订 |
| [P0-M5-preference-gate-advance.md](P0-M5-preference-gate-advance.md) | M5: 偏好提取与阶段门禁 |
| [P0-M6-frontend-creation-display.md](P0-M6-frontend-creation-display.md) | M6: 前端项目创建与需求展示 |
| [P0-M7-frontend-dialogue-gate.md](P0-M7-frontend-dialogue-gate.md) | M7: 前端对话交互与门禁界面 |
| [P0-M8-realtime-resilience.md](P0-M8-realtime-resilience.md) | M8: 实时通信与状态恢复 |

---

## 需求覆盖矩阵

| Phase0需求.md 章节 | 覆盖模块 |
|-------------------|---------|
| §2 项目创建与 Phase 0 入口 | M1, M6 |
| §3 RequirementsAgent | M2 |
| §4 CompletenessReviewer | M3 |
| §5 Phase 0 用户交互 | M4, M7 |
| §6 Gate 0 门禁与偏好确认 | M5, M7 |
| §7 前端 UI 规格 | M6, M7 |
| §8 数据持久化 | M1 |
| §9 事件流 | M8 |
| §10 边界条件与错误处理 | M1, M8 |
| §11 安全护栏 | M4 |
| §12 API 合约 | M1, M5, M8 |
| §13 阶段回退 | M5 |
| §14 task_ledger 初始化 | M1 |
| §15 验收清单 | 全部 |

---

## 测试场景覆盖矩阵

| 测试场景 | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 |
|---------|----|----|----|----|----|----|----|----|
| 场景 1: 创建项目 + 生成完整需求 | ✓ | ✓ | ✓ | | | ✓ | | |
| 场景 2: 自然对话修改需求 | | | | ✓ | | | ✓ | |
| 场景 3: 澄清问题处理 | | ✓ | ✓ | ✓ | | ✓ | ✓ | |
| 场景 4: 偏好提取与确认 | | | | | ✓ | | ✓ | |
| 场景 5: 门禁与推进 | | | | | ✓ | | ✓ | |
| 场景 6: 边界与恢复 | ✓ | | | | | ✓ | | ✓ |

---

> **关联文档**:
> - 需求规格: `docs/Phase0需求.md`
> - 手动测试场景: `docs/Phase0_Manual_Test_Scenario.md`
> - 技术架构: `docs/TECH_PLAN_v3.3.md`
> - 开发约束: `HARNESS.md`
> - 项目导航: `CLAUDE.md`
