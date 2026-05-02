# [SPEC-C-020] SFXReviewer 拆为 SfxLayoutReviewer + SfxMixReviewer

## Metadata
- **task_id**: SPEC-C-020
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-5
- **delta_id**: TECH-DELTA-04
- **depends_on**: [SPEC-A-014, SPEC-C-019]
- **priority**: P0
- **estimated_complexity**: M

## Scope
拆 v3.15 SPEC-9.6.2 `SFXReviewer` 单层为 `SfxLayoutReviewer`（L1 纯程序化）+ `SfxMixReviewer`（L1 程序化 + L2 LLM 兜底）。原 SFXReviewer 标 deprecated 保留两个 release。统一调用入口 `SfxReviewerOrchestrator` 按反馈协议 `comment_type` 路由（layout_feedback 重 layout，mix_feedback 仅重 segment）。

## Allowed Files
- `src/backend/reviewers/sfx_layout_reviewer.py` (NEW)
- `src/backend/reviewers/sfx_mix_reviewer.py` (NEW)
- `src/backend/reviewers/sfx_reviewer_orchestrator.py` (NEW)
- `src/backend/reviewers/sfx_reviewer.py` (MODIFY 加 deprecated 标记，保留实现)
- `src/shared/schemas/feedback_protocol.py` (MODIFY 追加 comment_type=layout_feedback|mix_feedback)
- `src/shared/types/feedback_protocol.ts` (MODIFY 同步)
- `tests/unit/reviewers/test_sfx_layout_reviewer.py` (NEW)
- `tests/unit/reviewers/test_sfx_mix_reviewer.py` (NEW)
- `tests/integration/reviewers/test_sfx_orchestrator_routing.py` (NEW)

## Forbidden Files
- `src/backend/services/sfx_*.py` (服务由 C-019 承担)
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：`SfxLayoutReviewer` 4 项 L1 检查独立单测：script_coverage / keyword_anchor (anchor_text overlap ≥ 0.8) / explanation_completeness (rationale + narrative_role 非空) / sparsity (avg ≥ 15s, max 3 条/30s)；每项 PASS / FAIL 各一例
- [ ] AC-2：`SfxMixReviewer` 3 项 L1 + L2 兜底：clipping / speech_snr (≥ -6dB) / bgm_synergy；构造削波 segment → FAIL
- [ ] AC-3：路由隔离测试：构造 layout 问题（缺 rationale）→ 仅 LayoutReviewer FAIL，MixReviewer 不执行；构造 mix 问题（削波）→ 仅 MixReviewer FAIL，LayoutReviewer 不执行
- [ ] AC-4：反馈协议 schema 测试：`comment_type` 必填且 ∈ {layout_feedback, mix_feedback}；`target` 类型与 comment_type 一致（layout→trigger_id；mix→segment_id）
- [ ] AC-5：增量重做测试：mix_feedback 提交后只重 mix 受影响 segment；layout_feedback 触发 Step 1 重 layout
- [ ] AC-6：v3.15 既有 SFXReviewer 测试在 deprecated 路径仍 PASS（向后兼容两个 release）
- [ ] AC-7：Orchestrator 入口的两条路径分发逻辑代码覆盖率 100%

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_020.py -v
# v3.15 兼容性
mypy src/backend/reviewers/sfx_layout_reviewer.py src/backend/reviewers/sfx_mix_reviewer.py src/backend/reviewers/sfx_reviewer_orchestrator.py --strict
```

## Completion Definition
两个新 Reviewer + Orchestrator + 反馈协议扩展 + deprecated 标记 + 全部 7 条 AC PASS + v3.15 兼容回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_020.py | test_script_coverage_pass_fail / test_keyword_anchor_overlap / test_explanation_completeness / test_sparsity |
| AC-2 | tests/unit/backend-core/test_spec_c_020.py | test_clipping_detection / test_speech_snr / test_bgm_synergy |
| AC-3 | tests/unit/backend-core/test_spec_c_020.py | test_layout_problem_isolated / test_mix_problem_isolated |
| AC-4 | tests/unit/backend-core/test_spec_c_020.py (or feedback test file) | test_feedback_protocol_comment_type_required / test_target_type_matches_comment_type |
| AC-5 | tests/unit/backend-core/test_spec_c_020.py | test_mix_feedback_partial_remix / test_layout_feedback_full_relayout |
| AC-6 | tests/unit/backend-core/test_spec_c_020.py | test_v315_path_still_passes |
| AC-7 | tests/unit/backend-core/test_spec_c_020.py | test_orchestrator_branch_coverage |

## §23.9 验收门禁映射
- 第 6 行：SfxLayoutReviewer / SfxMixReviewer 分离
