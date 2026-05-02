# [SPEC-E-013] P6 全文标注视图 + 编号片段试听 + 最终音频

## Metadata
- **task_id**: SPEC-E-013
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §E-AUDP7A-3
- **delta_id**: PRD-DELTA-04 / PRD-DELTA-05 / TECH-DELTA-08
- **depends_on**: [SPEC-A-017, SPEC-E-011, SPEC-E-015]
- **priority**: P0
- **estimated_complexity**: L

## Scope
P6 阶段三组件链 + 强制顺序：Step1 全文标注视图（高亮 SFX 触发 + tooltip rationale/narrative_role + 确认按钮）→ Step2 编号片段试听列表（每段独立试听 + mix_feedback 提交）→ Step3 最终主音频播放器 + 下载（FinalAudioAssembler 完成后出现）。

## Allowed Files
- `src/frontend/components/phase6/Phase6ScriptAnnotationView.tsx` (NEW)
- `src/frontend/components/phase6/Phase6SegmentMixList.tsx` (NEW)
- `src/frontend/components/phase6/Phase6FinalMaster.tsx` (NEW)
- `src/frontend/components/phase6/Phase6Pipeline.tsx` (NEW；编排三组件状态机)
- `src/frontend/store/phase6_state.ts` (NEW；user_confirmed_layout / final_master)
- `tests/unit/frontend/phase6/*.test.tsx` (NEW)
- `tests/integration/frontend/p6_three_step_pipeline.spec.ts` (NEW Playwright)

## Forbidden Files
- `src/shared/**`
- `src/backend/**`
- `src/frontend/components/phase{4,5,7a}/**`

## Acceptance Criteria
- [ ] AC-1：annotation_spans 渲染为带 tooltip 的高亮（hover 显示 rationale + narrative_role）；同位置多 trigger 用堆叠徽章
- [ ] AC-2：未点 "确认布局"（user_confirmed_layout=false）→ 编号片段列表 disabled（鼠标悬停光标 not-allowed + aria-disabled）
- [ ] AC-3：mix_feedback 提交后该 segment 的 preview_url 刷新（接收 WebSocket `segment.remixed` 事件 → audio src 更新）
- [ ] AC-4：最终主播放器仅在 store 中 master_audio.kind=final_audio_master 时出现；缺失则保留分段视图
- [ ] AC-5：强制顺序：Step1 → Step2 → Step3 三态切换由 store 驱动；无法跳过 Step1 直接进 Step2
- [ ] AC-6：a11y：annotation 高亮区含 `aria-describedby` 指向 tooltip 容器；确认按钮含明确 `aria-label`

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_013.py -v
npx playwright test tests/integration/frontend/p6_three_step_pipeline.spec.ts
npx tsc --noEmit src/frontend/components/phase6/*.tsx
```

## Completion Definition
三组件 + 编排 + store + 全部 6 条 AC PASS + Playwright 三步骤覆盖。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_013.py | renders_highlights_with_tooltip / stacks_multiple_triggers |
| AC-2 | tests/unit/frontend/test_spec_e_013.py | disabled_until_confirm_layout |
| AC-3 | tests/unit/frontend/test_spec_e_013.py | mix_feedback_refreshes_segment_preview |
| AC-4 | tests/unit/frontend/test_spec_e_013.py | only_renders_when_final_kind |
| AC-5 | tests/unit/frontend/test_spec_e_013.py | enforces_step1_before_step2 |
| AC-6 | tests/unit/frontend/test_spec_e_013.py | a11y_aria_describedby |

## §23.9 验收门禁映射
- 第 10 行：前端 annotation_spans 可用（P6 部分）
