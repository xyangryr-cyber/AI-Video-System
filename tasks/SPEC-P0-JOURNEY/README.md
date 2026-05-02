# SPEC-P0-JOURNEY — Phase 0 Vertical Slice SPEC Cards

> **拆分来源**: `docs/Phase0需求.md` (930 lines, 15 sections)
> **拆分方法**: `split-spec` (硅基员工 #36) — Journey-first vertical slicing
> **拆分日期**: 2026-05-01
> **状态**: PENDING（SPEC 卡片已生成，待实现）

---

## Journey Map

```
用户访问 /projects/new
  │
  ├── J-001: 创建项目 → 需求生成
  │    输入标题+描述 → 提交 → 看到需求摘要卡片+澄清问题
  │    Modules: M-001..M-004
  │
  ├── J-002: 需求迭代修改
  │    输入修改意见 → Router 识别 → 卡片更新 → 自动 re-review
  │    Modules: M-005..M-008
  │
  └── J-003: 偏好确认 → 门禁推进
       点击"确认进入下一阶段" → 偏好 Modal → GateKeeper → Phase 1
       Modules: M-009..M-011
```

---

## Journey SPECs

| ID | User Behavior (一句话) | evidence_type | Modules |
|---|---|---|---|
| [J-001](J-001-project-create-generate.md) | 用户创建项目 → ≤60s 看到结构化需求摘要卡片+澄清问题 | user_observable | M-001..M-004 |
| [J-002](J-002-requirements-iterate.md) | 用户输入修改意见 → Router 识别 → ≤60s 卡片更新+自动审核 | user_observable | M-005..M-008 |
| [J-003](J-003-preference-gate-advance.md) | 用户确认偏好 → GateKeeper 校验 → Phase 0 完成/Phase 1 高亮 | user_observable | M-009..M-011 |

---

## Module SPECs

| ID | Title | Parent Journey | evidence_type |
|---|---|---|---|
| [M-001](modules/M-001-project-create-infra.md) | Project Creation Infrastructure (API + DB + task_ledger) | J-001 | consumer_driven |
| [M-002](modules/M-002-requirements-agent.md) | RequirementsAgent + requirements.json Schema | J-001 | eval_based |
| [M-003](modules/M-003-new-project-page.md) | NewProject Page + Form Validation | J-001 | user_observable |
| [M-004](modules/M-004-phase0-workflow-view.md) | Phase 0 Workflow View (需求卡片 + 任务清单) | J-001 | user_observable |
| [M-005](modules/M-005-intent-router.md) | Intent Router | J-002 | eval_based |
| [M-006](modules/M-006-completeness-reviewer.md) | CompletenessReviewer | J-002 | eval_based |
| [M-007](modules/M-007-revise-regenerate-flow.md) | Revise/Regenerate Flow + Artifact Versioning | J-002 | consumer_driven |
| [M-008](modules/M-008-chat-input.md) | Chat Input + Interaction Area | J-002 | user_observable |
| [M-009](modules/M-009-preference-extractor.md) | PreferenceExtractor | J-003 | eval_based |
| [M-010](modules/M-010-gatekeeper-advance.md) | GateKeeper + Advance Endpoint + Preferences | J-003 | consumer_driven |
| [M-011](modules/M-011-preference-modal-advance-button.md) | Preference Modal + Advance Button UI | J-003 | user_observable |

---

## Evidence Type Distribution

| evidence_type | Count | Modules |
|---|---|---|
| user_observable | 5 | M-003, M-004, M-008, M-011 (+ 3 journeys) |
| eval_based | 4 | M-002, M-005, M-006, M-009 |
| consumer_driven | 3 | M-001, M-007, M-010 |

---

## 与原始文档的映射

| Phase0需求.md 章节 | 对应 SPEC 卡片 |
|---|---|
| §1 定位与概述 | J-001 (概述分散到 3 条 Journey) |
| §2 项目创建与入口 | M-001 (API+DB), M-003 (NewProject page) |
| §3 RequirementsAgent | M-002 |
| §4 CompletenessReviewer | M-006 |
| §5 用户交互 | M-005 (Router), M-007 (revise/regenerate), M-008 (ChatInput) |
| §6 Gate 0 门禁与偏好 | M-009 (PreferenceExtractor), M-010 (GateKeeper), M-011 (Modal+Button) |
| §7 前端 UI | M-003, M-004, M-008, M-011 |
| §8 数据持久化 | M-001 (DB), M-010 (preferences) |
| §13 阶段回退 | J-003 (DoD 隐含覆盖) |
| §14 task_ledger 初始化 | M-001 |
| §10 边界条件 | 各 Module 的 Exception Handling 节 |
| §11 安全护栏 | 未单独拆出（跨切面关注点，在 SPEC-A 中） |
| §12 API 合约 | M-001, M-010 的 Interfaces 节 |
| §15 验收清单 | 3 条 Journey 的 Definition of Done |

---

## 下一步

1. 按 J-001 → J-002 → J-003 顺序实现（依赖关系：J-002 需要 J-001 的产物，J-003 需要 J-001+J-002 的产物）
2. 每条 Journey 先写 playwright test → 看到 RED → 再实现 Modules
3. 每条 Journey 的 Internal Modules 可并行开发（前端/后端/Agent 独立）
4. 实现完成后运行 `superpowers:verification-before-completion` 验证
