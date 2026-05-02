# SPEC-P0-FIX-007: WorkflowPage UX 细节修复

> **来源 Bug**: BUG-008 (阶段标签显示 mock 数据格式)
> **根因**: 硬编码的 PHASE_LABELS 数组和 phase 显示格式有小问题，且 ArtifactList 使用了 mock phaseLabels
> **严重级别**: LOW
> **依赖**: SPEC-P0-FIX-001（需要真实数据层）

---

## 根因分析

```typescript
// WorkflowPage.tsx:19-33
const PHASE_LABELS = [
  "需求定义", "内容主线", "口播脚本", "脚本润色",
  "人声旁白", "背景音乐", "音效设计", "分镜脚本",
  "关键画面", "B-Roll素材", "粗剪合成", "精剪交付", "最终输出",
] as const

// WorkflowPage.tsx:68-69
阶段 {currentPhase}/{PHASE_LABELS.length - 1} · {phaseLabel}
// 显示: "阶段 0/12 · 需求定义"
// 问题: currentPhase 是 0-based，但用户看到 "0/12" 会困惑
```

两个小问题：
1. Phase 从 0 开始计数，"0/12" 显示不直观 — 用户期望看到 "Phase 1/13" 或保持 P0 风格
2. `PHASE_LABELS` 在 WorkflowPage 中重复定义（`PhaseNavigation.tsx` 中也有相同的数组）

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | 阶段显示使用 1-based 或 P0 风格 | Playwright: 验证显示 "阶段 1/13" 或 "P0 · 需求定义" |
| AC-2 | PHASE_LABELS 从共享常量导入，不在 WorkflowPage 中重复定义 | 静态检查: `grep PHASE_LABELS WorkflowPage.tsx` 无重复定义 |
| AC-3 | ArtifactList 不再使用 WorkflowPage 传入的 phaseLabels（从自身数据源获取） | 检查 ArtifactList props |

---

## TDD 实现计划

### RED 1: 阶段标签格式测试

```typescript
// 测试: WorkflowPage 的 phase 显示
// - currentPhase=0 → 显示 "P0 · 需求定义" 而非 "阶段 0/12 · 需求定义"
// - currentPhase=0 → 显示 "阶段 1/13"  (1-based)
```

### GREEN 1: 修复标签 + 提取常量

```typescript
// 1. 在 src/shared/constants/ 中定义 PHASE_LABELS
//    export const PHASE_LABELS = ["需求定义", ...] as const

// 2. WorkflowPage 和 PhaseNavigation 都从共享常量导入

// 3. 修复显示格式:
//    <div>P{currentPhase} · {phaseLabel}</div>
//    或 <div>阶段 {currentPhase + 1}/{PHASE_LABELS.length}</div>
```

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/pages/WorkflowPage.tsx` | 修复标签格式, 移除重复常量 |
| `src/frontend/components/PhaseNavigation.tsx` | 从共享常量导入 PHASE_LABELS |
| `src/shared/constants/phaseLabels.ts` | **新建** — 阶段名称共享常量 |
| `tests/unit/frontend/WorkflowPage.test.tsx` | 更新 |

---

## 验证命令

```bash
# 确保无重复定义
grep -rn "PHASE_LABELS" src/frontend/pages/WorkflowPage.tsx
# 预期: 只导入，不定义

# 类型检查
cd src/frontend && npx tsc --noEmit
```
