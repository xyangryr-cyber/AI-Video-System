# [SPEC-C-104] PatchPlanner + DiffAuditor

## Metadata
- **task_id**: SPEC-C-104
- **spec_ref**: `SPEC-C` §C-BDD-5
- **depends_on**: [SPEC-C-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 PatchPlanner 输出 1-3 个 `(after_segment_id, score, reason)` 候选位置，并由 DiffAuditor 在 unrelated_change_ratio > 5% 时阻断 commit；insert_section 始终产生新 segment_id，与 regenerate_section 路径明确分离，新段落事实走 ClaimExtractor。

## Allowed Files
- `src/backend/agents/patch_planner.py`
- `src/backend/services/diff_auditor.py`
- `tests/unit/agents/test_patch_planner.py`
- `tests/integration/test_diff_auditor_5pct.py`

## Acceptance Criteria
- [ ] AC-1: 位置推荐 1-3 候选 `(after_segment_id, score, reason)`
- [ ] AC-2: DiffAuditor unrelated_change_ratio > 5% 时 FAIL + 阻断 commit
- [ ] AC-3: 与 regenerate_section 路径区分:insert_section 产生新 segment_id
- [ ] AC-4: 集成测试:恶意 LLM 输出改写无关段落 → FAIL

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_104.py -v
```

## Completion Definition
PatchPlanner 输出 1-3 候选位置、DiffAuditor 在 unrelated_change_ratio > 5% 时阻断 commit、insert_section 路径产生新 segment_id 与 regenerate_section 区分、恶意 LLM 改写无关段落用例正确 FAIL，全部 AC 与单测/集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_104.py | test_position_recommends_one_to_three_candidates |
| AC-2 | tests/unit/backend-core/test_spec_c_104.py | test_unrelated_change_ratio_over_5pct_blocks_commit |
| AC-3 | tests/unit/backend-core/test_spec_c_104.py | test_insert_section_creates_new_segment_id |
| AC-4 | tests/unit/backend-core/test_spec_c_104.py | test_malicious_llm_unrelated_rewrite_fails |
