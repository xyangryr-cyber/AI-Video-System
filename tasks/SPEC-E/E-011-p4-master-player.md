# [SPEC-E-011] P4 主播放器 + 下载 + 分段精修面板

## Metadata
- **task_id**: SPEC-E-011
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §E-AUDP7A-1
- **delta_id**: PRD-DELTA-01 / TECH-DELTA-08
- **depends_on**: [SPEC-A-017, SPEC-E-015]
- **priority**: P0
- **estimated_complexity**: M

## Scope
P4 阶段预览组件 props 扩展，顶部新增主播放器（waveform + play/pause + 进度）+ 下载按钮，数据源 = `master_audio.master_audio_url`；分段精修面板（v3.15）保持；订阅 WebSocket `master_audio.updated` 事件自动重载。

## Allowed Files
- `src/frontend/components/phase4/Phase4Preview.tsx` (MODIFY；扩展 props + 顶部播放器槽位)
- `src/frontend/components/phase4/MasterAudioPlayer.tsx` (NEW)
- `src/frontend/hooks/useMasterAudioSubscription.ts` (NEW；WebSocket 订阅)
- `src/frontend/api/master_audio.ts` (NEW；GET /artifacts/master_audio?phase=4 调用)
- `tests/unit/frontend/phase4/Phase4Preview.test.tsx` (MODIFY 加 v3.17 断言)
- `tests/unit/frontend/phase4/MasterAudioPlayer.test.tsx` (NEW)
- `tests/integration/frontend/p4_master_audio_e2e.spec.ts` (NEW Playwright)

## Forbidden Files
- `src/shared/**`
- `src/backend/**`
- `src/frontend/components/phase{5,6,7a}/**`

## Acceptance Criteria
- [ ] AC-1：组件单测（vitest）：传入 master_audio prop → MasterAudioPlayer 渲染 waveform / play/pause / 进度三元素
- [ ] AC-2：交互测试：下载按钮点击触发 GET `/api/projects/{id}/artifacts/master_audio?phase=4`，URL 结构正确
- [ ] AC-3：WebSocket 测试：mock `master_audio.updated` 事件 → MasterAudioPlayer 重渲（src 属性变化或 audio.load() 调用）
- [ ] AC-4：v3.15 分段精修流程不回归（既有测试套件 PASS）
- [ ] AC-5：a11y：MasterAudioPlayer 含 `role="region"` `aria-label="主旁白播放器"`；下载按钮含 `aria-label`
- [ ] AC-6：master_audio prop 缺失时显示骨架屏（loading state），不报错

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_011.py -v
npx playwright test tests/integration/frontend/p4_master_audio_e2e.spec.ts
npx tsc --noEmit src/frontend/components/phase4/Phase4Preview.tsx src/frontend/components/phase4/MasterAudioPlayer.tsx
```

## Completion Definition
新组件 + hook + API client + 全部 6 条 AC PASS + Playwright e2e 通过 + v3.15 零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_011.py | renders_waveform_play_progress |
| AC-2 | tests/unit/frontend/test_spec_e_011.py | download_button_calls_correct_url |
| AC-3 | tests/unit/frontend/test_spec_e_011.py | rerenders_on_master_audio_updated |
| AC-4 | tests/unit/frontend/test_spec_e_011.py | (v3.15 segment revise suite) |
| AC-5 | tests/unit/frontend/test_spec_e_011.py | a11y_role_and_aria_label |
| AC-6 | tests/unit/frontend/test_spec_e_011.py | shows_skeleton_when_master_audio_missing |

## §23.9 验收门禁映射
- 第 10 行：前端 master_audio_url 可用（P4 部分）
