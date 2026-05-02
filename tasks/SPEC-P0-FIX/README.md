# SPEC-P0-FIX: Phase 0 Bug 修复 — 按根因分类

> 来源: `docs/Phase0_Manual_Test_Bug_Report.md` (2026-04-30)
> 测试方法: Playwright 浏览器自动化，通过前端 UI 操作

---

## Bug → SPEC 映射

| Bug | 描述 | SPEC |
|-----|------|------|
| BUG-001 | WorkflowPage 使用硬编码 Mock 数据 | SPEC-001 |
| BUG-004 | 项目标题始终显示 Mock 值 | SPEC-001 |
| BUG-002 | ChatInput handleSend 是空函数 | SPEC-002 |
| BUG-003 | PhaseNavigation 未渲染 | SPEC-003 |
| BUG-006 | 无 Agent 输出展示 | SPEC-004 |
| BUG-005 | Advance 按钮不存在 | SPEC-005 |
| BUG-007 | 表单提交后不跳转 | SPEC-006 |
| BUG-008 | 阶段标签 mock 格式 | SPEC-007 |

---

## 依赖关系与实现顺序

```
SPEC-006 (表单可靠性)     SPEC-001 (数据层 — 基础)
    │                          │
    └──────────┬───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
          SPEC-002        SPEC-003         SPEC-004
        (Chat API)    (PhaseNavigation)  (P0 Preview)
               │               │               │
               └───────────────┼───────────────┘
                               │
                               ▼
                          SPEC-005
                     (Advance/GateKeeper)
                               │
                               ▼
                          SPEC-007
                        (UX Cleanup)
```

**推荐实现顺序**:
1. **SPEC-006** — 独立，无依赖，可最先做
2. **SPEC-001** — 基础层，所有其他 SPEC 的依赖
3. **SPEC-002 + SPEC-003 + SPEC-004** — 可并行（都依赖 SPEC-001）
4. **SPEC-005** — 依赖 SPEC-001 和 SPEC-004
5. **SPEC-007** — 最后收尾

---

## TDD 实施清单

每个 SPEC 遵循 RED → GREEN → REFACTOR 循环：

| SPEC | RED (失败测试) | GREEN (最小实现) | 新建文件数 |
|------|---------------|-----------------|-----------|
| 001 | WorkflowPage 渲染真实数据 | 接入 useProjectState，替换 MOCK_* | 1 (测试) |
| 002 | useChat hook 单元测试 | 创建 useChat，接入 ChatInput | 2 (hook + 测试) |
| 003 | PhaseNavigation 存在性测试 | 导入并渲染 PhaseNavigation | 0 |
| 004 | ArtifactModal 渲染 Preview | 接入 PhasePreviewRouter | 1 (测试) |
| 005 | AdvanceButton 状态测试 | useAdvance hook + 按钮 | 2 (hook + 测试) |
| 006 | useCreateProject 测试 | 修复 apiClient 201 处理 | 2 (测试) |
| 007 | 阶段标签格式测试 | 提取 PHASE_LABELS 常量 | 1 (常量) |

---

## 完成后验收

所有 SPEC 实现完成后，重跑 Phase 0 手动测试场景：

```bash
npx playwright test phase0-manual-scenarios.spec.ts
```

**目标**: 通过率从 40.5% → > 80%
- 场景 1 (创建+需求): PASS (原 FAIL)
- 场景 2 (对话修改): PASS (原 FAIL)
- 场景 3 (澄清处理): PASS (原 FAIL)
- 场景 6 (输入校验): 保持 PASS
- 场景 4/5: 需后端 Agent 实际响应，可能仍 PARTIAL

---

## 实测结果 (2026-05-01)

```bash
npx playwright test phase0-manual-scenarios.spec.ts
```

**17 passed, 1 failed (48.6s)**

### 按场景汇总

| 场景 | ✅ PASS | ⚠️ PARTIAL | ❌ FAIL | ⊘ SKIP | 通过率 | 含PARTIAL |
|------|---------|-------------|---------|---------|--------|-----------|
| 场景1-需求定义 | 8 | 3 | 7 | 0 | 44.4% | 61.1% |
| 场景2-对话修改 | 3 | 6 | 2 | 0 | 27.3% | 81.8% |
| 场景3-澄清处理 | 1 | 8 | 2 | 0 | 9.1% | 81.8% |
| 场景4-偏好提取 | 0 | 0 | 1 | 0 | 0% | 0% |
| 场景5-门禁推进 | 0 | 1 | 0 | 1 | — | — |
| 场景6-输入校验 | 4 | 0 | 0 | 0 | **100%** | 100% |
| 场景7-UI细节 | 4 | 0 | 3 | 0 | 57.1% | 57.1% |
| **总计** | **20** | **18** | **15** | **1** | **37.0%** | **70.4%** |

### 1 个失败

**场景 4 — 偏好提取与确认** (`advanceBtn.click()` 超时):
- 按钮 `<button disabled title="等待门禁条件满足">` 存在但 disabled
- 原因: 系统使用 mock 数据，门禁条件 (gate conditions) 未满足

### 主要问题模式

| 问题 | 影响场景 | 状态 |
|------|---------|------|
| PhaseNavigation sidebar 不存在于 WorkflowPage | 1.2d | ❌ 未修复 |
| 页面标题使用硬编码 MOCK_PROJECT_TITLE | 7.2f | ❌ 未修复 |
| ArtifactList 区域缺失 | 7.2c | ❌ 未修复 |
| FactualLedger 区域缺失 | 7.2d | ❌ 未修复 |
| TaskCard 显示硬编码 mock 任务 | 1.2g | ⚠️ 部分 |
| 无加载/处理中指示器 | 1.2f | ❌ 未修复 |
| Advance 按钮 disabled (门禁条件未满足) | 1.4c, 3.3c, 4.1 | ❌ 未修复 |
| ChatInput 消息发送正常 | 2.1, 7.2e | ✅ 已修复 |
| 表单校验正常 | 6.1, 6.2 | ✅ 已修复 |
| 项目列表页正常 | 7.1 | ✅ 已修复 |

### vs 目标对比

| 指标 | 修复前 | 目标 | 实际 |
|------|--------|------|------|
| 总通过率 | 40.5% | >80% | 37.0% |
| 含PARTIAL通过率 | — | — | 70.4% |
| 场景6 (输入校验) | PASS | PASS | ✅ 100% |
| 场景1 (需求定义) | FAIL | PASS | ❌ 44.4% |
| 场景2 (对话修改) | FAIL | PASS | ❌ 27.3% |
| 场景3 (澄清处理) | FAIL | PASS | ❌ 9.1% |

**结论**: SPEC-006 (表单可靠性) 已完全修复。其余 SPEC 的修复未生效或仅部分生效 — WorkflowPage 仍使用 mock 数据作为主要数据源，PhaseNavigation/ArtifactList/FactualLedger 组件未渲染，advance 按钮无法点击。
