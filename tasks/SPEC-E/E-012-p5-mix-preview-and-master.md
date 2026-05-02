# [SPEC-E-012] P5 混音预览 + 候选比较 + 主播放器

## Metadata
- **task_id**: SPEC-E-012
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §E-AUDP7A-2
- **delta_id**: PRD-DELTA-02 / PRD-DELTA-03 / TECH-DELTA-08
- **depends_on**: [SPEC-A-017, SPEC-E-011, SPEC-E-015]
- **priority**: P0
- **estimated_complexity**: M

## Scope
P5 阶段候选卡片 props 重构：默认试听 = `preview_url`（混音预览）+ 辅助试听 = `raw_bgm_url`（原 BGM）；多候选并排 A/B 比较；选定后调用 BgmMixRenderer → 主播放器 + 下载；no_bgm 路径回退主播放器为 narration_master 视图。

## Allowed Files
- `src/frontend/components/phase5/Phase5CandidateCard.tsx` (MODIFY 扩 preview/raw 双 url)
- `src/frontend/components/phase5/Phase5MasterPlayer.tsx` (NEW)
- `src/frontend/components/phase5/Phase5CandidateGrid.tsx` (NEW；A/B/C 比较)
- `src/frontend/store/phase5_master.ts` (NEW Pinia/Zustand store)
- `tests/unit/frontend/phase5/Phase5CandidateCard.test.tsx` (NEW)
- `tests/unit/frontend/phase5/Phase5MasterPlayer.test.tsx` (NEW)
- `tests/integration/frontend/p5_select_to_master.spec.ts` (NEW Playwright)

## Forbidden Files
- `src/shared/**`
- `src/backend/**`
- `src/frontend/components/phase{4,6,7a}/**`

## Acceptance Criteria
- [ ] AC-1：候选卡片同时渲染 preview / raw 两个播放器入口（两个 audio 标签或两个 button）
- [ ] AC-2：选定候选 → store master_audio 由 null 切换为有效（kind=bgm_mix_master）；MasterPlayer 出现 + 下载按钮启用
- [ ] AC-3：选 "无 BGM" → store master_audio.kind=narration_master（回退）
- [ ] AC-4：A/B 切换不打断当前播放（异步加载测试 + 不取消其他 audio 元素的 play promise）
- [ ] AC-5：fit_review 中含 v3.15+v3.17 7 项检查 verdict，候选卡片展示其聚合 PASS/FAIL 徽章
- [ ] AC-6：a11y：候选卡片含 `role="article"` + 选定状态用 `aria-pressed`；MasterPlayer 同 E-011

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_012.py -v
npx playwright test tests/integration/frontend/p5_select_to_master.spec.ts
npx tsc --noEmit src/frontend/components/phase5/*.tsx
```

## Completion Definition
候选卡片重构 + Master 组件 + Grid + store + 全部 6 条 AC PASS + Playwright e2e。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_012.py | renders_preview_and_raw_buttons |
| AC-2 | tests/unit/frontend/test_spec_e_012.py | select_candidate_shows_master_and_download |
| AC-3 | tests/unit/frontend/test_spec_e_012.py | no_bgm_falls_back_to_narration |
| AC-4 | tests/unit/frontend/test_spec_e_012.py | ab_switch_does_not_break_play |
| AC-5 | tests/unit/frontend/test_spec_e_012.py | renders_fit_review_aggregate_badge |
| AC-6 | tests/unit/frontend/test_spec_e_012.py | a11y_role_and_aria_pressed |

## §23.9 验收门禁映射
- 第 10 行：前端 master_audio_url 可用（P5 部分）
