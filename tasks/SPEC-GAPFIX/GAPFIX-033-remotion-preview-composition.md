# [SPEC-GAPFIX-033] Remotion PreviewComposition 真实接入

## Metadata
- **task_id**: SPEC-GAPFIX-033
- **spec_ref**: Design Spec §8.5
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: L

## Scope
Replace the 44-line `<div>` wrapper in `src/frontend/remotion/PreviewComposition.tsx` (file does not exist, needs creation) with a real `<Composition>` component that calls `renderMedia()`.

## Allowed Files
- `src/frontend/remotion/PreviewComposition.tsx`
- `src/frontend/remotion/Root.tsx` (if needed for Composition registration)

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `PreviewComposition.tsx` 存在
- [ ] AC-2: 使用 Remotion `<Composition>` 组件 (非裸 `<div>`)
- [ ] AC-3: 接受 `projectId`, `timeline`, `segments` 作为 props
- [ ] AC-4: 渲染 timeline segments 的视觉预览
- [ ] AC-5: `cd src/frontend && npx tsc --noEmit` 无新增错误 (Remotion 模块的 pre-existing 错误除外)

## Verification Commands
```bash
test -f src/frontend/remotion/PreviewComposition.tsx && echo "PASS: file exists" || echo "FAIL: file not found"
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
`PreviewComposition.tsx` 使用 Remotion `<Composition>` 实现真实视频预览。vitest 通过。
