# [SPEC-E-103] 分镜编辑器 anchor + shot split UI

## Metadata
- **task_id**: SPEC-E-103
- **spec_ref**: SPEC-E §E-BDD-4
- **depends_on**: [SPEC-A-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现分镜编辑器：左栏脚本根据选中 shot 高亮 anchor_text 区间，右栏卡片支持拖拽切分生成新 shot 并保留 split_from_shot_id 谱系，卡片显示场景类型、时长、claim 数、占位预览与模式 chip。

## Allowed Files
- `src/frontend/components/StoryboardEditor.tsx`
- `src/frontend/components/storyboard/ScriptPane.tsx`
- `src/frontend/components/storyboard/ShotCardGallery.tsx`
- `src/frontend/components/storyboard/ShotSplitter.tsx`
- `src/frontend/components/storyboard/ModeChip.tsx`
- `tests/e2e/storyboard_anchor_split.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 选中 shot 左栏自动高亮对应 anchor_text 区间
- [ ] AC-2: 拖拽切分产生 2 个新 shot.json,父 shot 保留为 `split_from_shot_id`
- [ ] AC-3: 切分后子 shot 时长之和 = 父时长 ± 100ms
- [ ] AC-4: shot 卡片显示 scene_type/时长/claim 数/占位预览/模式 chip

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_103.py -v
npx playwright test tests/e2e/storyboard_anchor_split.spec.ts
```

## Completion Definition
分镜编辑器在 anchor 联动高亮、拖拽切分谱系保留、子时长守恒、卡片元信息渲染四方面均通过 e2e 验证。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_103.py | selecting_shot_highlights_anchor_text_range |
| AC-2 | tests/unit/frontend/test_spec_e_103.py | drag_split_creates_two_shots_with_parent_lineage |
| AC-3 | tests/unit/frontend/test_spec_e_103.py | child_shot_durations_sum_equals_parent_within_100ms |
| AC-4 | tests/unit/frontend/test_spec_e_103.py | shot_card_renders_scene_type_duration_claim_preview_mode |
