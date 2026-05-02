# SPEC-P0-FIX-004: Phase 0 产物预览接入真实数据

> **来源 Bug**: BUG-006 (无 Agent 输出展示 — 需求卡片、平台规格、字数计算、字段标记)
> **根因**: `P0RequirementsView.tsx` 和 `PhasePreviewRouter.tsx` 已实现，但 WorkflowPage 未使用它们来展示 Phase 0 产物；ArtifactList 的 `onSelect` 点击后弹出 ArtifactModal，但 modal 内未渲染对应 phase 的 Preview 组件
> **严重级别**: MEDIUM — 阻塞用户查看 Agent 生成的结构化需求
> **依赖**: SPEC-P0-FIX-001（需要真实 artifact 数据）

---

## 根因分析

两套基础设施已就绪但未连接：

1. **Preview 组件链**:
   - `PhasePreviewRouter.tsx` — 根据 `phase` 路由到对应 Preview 组件
   - `P0RequirementsView.tsx` — 渲染 Phase 0 需求结构化卡片
   - Preview 文件: P1~P11 共 11 个组件全部已实现

2. **ArtifactModal**:
   - WorkflowPage 通过 `ArtifactList.onSelect` → `setModalPhase(idx)` → `ArtifactModal` 显示
   - `ArtifactModal` 接受 `projectId`, `phaseIndex`, `phaseLabel` 但未渲染 Preview 组件

3. **artifact 数据获取**:
   - `useArtifact.ts` 已存在，返回 `artifact` 数据
   - `useArtifactStatus.ts` 已存在

**缺失的连接**: ArtifactModal 内需要根据 phase 渲染对应的 Preview 组件，并传入从 API 获取的真实 artifact 数据。

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | Phase 0 的 artifact 预览在 ArtifactList 中可见（条目 "需求定义"） | Playwright: ArtifactList 面板中出现 Phase 0 条目 |
| AC-2 | 点击 ArtifactList 中的 Phase 0 条目 → ArtifactModal 弹出 | Playwright: 点击后 modal 可见 |
| AC-3 | ArtifactModal 中渲染 P0RequirementsView（通过 PhasePreviewRouter） | Playwright: Modal 中显示 structured requirements 内容 |
| AC-4 | P0RequirementsView 显示正确的平台规格（B站→1920x1080, 8Mbps, H.264） | Playwright: 验证 modal 内文字含 "1920x1080" |
| AC-5 | P0RequirementsView 显示目标字数范围（时长×240×语速比） | Playwright: 验证字数 |
| AC-6 | P0RequirementsView 的已确认字段显示绿色勾 | Playwright: 验证绿色标记元素 |
| AC-7 | P0RequirementsView 缺失字段显示橙色问号 | Playwright: 验证橙色/黄色标记元素 |
| AC-8 | artifact 数据为空时显示 "暂无需求数据" | Playwright: 新项目创建后立即查看 |
| AC-9 | ClarificationQuestionList 在需要澄清时显示 | Playwright: 不完整描述创建的项目 |

---

## TDD 实现计划

### RED 1: ArtifactModal 渲染 Preview 测试

```typescript
// tests/unit/frontend/components/workflow/ArtifactModal.test.tsx
// - mock useArtifact 返回 Phase 0 requirements JSON
// - 断言 P0RequirementsView 渲染在 modal 内
// - 断言 platform.specs 数据显示 (1920x1080)
// - 断言 target_word_count 数据显示
```

### RED 2: P0RequirementsView 空数据测试

```typescript
// - mock useArtifact 返回 null/undefined
// - 断言 "暂无需求数据" 文案显示
```

### RED 3: P0RequirementsView 字段标记测试

```typescript
// - mock requirements 数据: 某些字段有值, 某些为空
// - 断言有值字段显示绿色勾 (confirmed)
// - 断言空缺字段显示橙色问号 (needs_clarification)
```

### GREEN 1: ArtifactModal 接入 PhasePreviewRouter

```typescript
// ArtifactModal.tsx
import { PhasePreviewRouter } from "@frontend/components/previews/PhasePreviewRouter"
import { useArtifact } from "@frontend/hooks/useArtifact"

export function ArtifactModal({ projectId, phaseIndex, phaseLabel, open, onClose }) {
  // useArtifact(projectId, phaseIndex) 获取 artifact 数据
  const { data: artifact } = useArtifact(projectId, phaseIndex);

  return (
    <Modal open={open} onClose={onClose}>
      <h2>{phaseLabel}</h2>
      <PhasePreviewRouter
        phase={phaseIndex}
        artifactData={artifact}
      />
    </Modal>
  );
}
```

### GREEN 2: 确保 P0RequirementsView 数据映射正确

```typescript
// 检查 useArtifact(projectId, 0) 返回的 artifact 结构
// 与 PhasePreviewRouter → P0RequirementsView 之间的数据传递
// 确保 P0RequirementsViewProps.requirements 得到正确的 RequirementsJSON
```

### REFACTOR

- 将 useArtifact 的 artifact 缓存策略优化（artifact 数据不会频繁变更）
- 考虑在 ArtifactList 中为当前 phase 显示 artifact status badge

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/components/workflow/ArtifactModal.tsx` | 接入 PhasePreviewRouter |
| `src/frontend/hooks/useArtifact.ts` | 可能需要增强（确保 Phase 0 artifact path 正确） |
| `tests/unit/frontend/components/workflow/ArtifactModal.test.tsx` | 新增 |

## 禁止修改的文件

- `src/frontend/components/previews/P0RequirementsView.tsx`
- `src/frontend/components/previews/PhasePreviewRouter.tsx`
- `src/frontend/components/workflow/ArtifactList.tsx`

---

## 验证命令

```bash
# 单元测试
cd src/frontend && npx vitest run tests/unit/frontend/components/workflow/ArtifactModal.test.tsx

# E2E 验证 (Playwright)
# 1. 创建完整描述项目 → 等待 Agent 处理完成
# 2. ArtifactList 面板中点击 Phase 0 "需求定义" 条目
# 3. ArtifactModal 弹出 → 渲染 P0RequirementsView
# 4. 验证: 平台规格 1920x1080, 字数范围, 已确认字段绿色勾
# 5. 创建不完整描述项目 → 验证澄清问题区域
```
