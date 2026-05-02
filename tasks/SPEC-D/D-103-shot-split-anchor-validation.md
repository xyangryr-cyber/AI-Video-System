# [SPEC-D-103] shot 拆分语义对齐 + anchor 校验 + 预览态/生产态切换

## Metadata
- **task_id**: SPEC-D-103
- **spec_ref**: SPEC-D §D-BDD-4
- **depends_on**: [SPEC-A-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
扩展 P7 Storyboard Reviewer L1 增加 4 条校验规则（A4 anchor substring、A5 区间不重叠、A6 时长加和、A7 downstream_bindings 合法性），并实现 shot 拆分逻辑与独立的 anchor 校验服务，确保子 shot 与父 shot 在文本与时长上严格对齐。

## Allowed Files
- `src/backend/agents/reviewers/storyboard_reviewer.py`
- `src/backend/agents/phase_executors/p7_storyboard.py`
- `src/backend/services/shot_anchor_validator.py`
- `tests/unit/reviewers/test_storyboard_l1_v316.py`

## Acceptance Criteria
- [ ] AC-1: L1-A4 anchor_text 是 polished_script substring（hash 比对）
- [ ] AC-2: L1-A5 子 shot 字符区间不重叠不遗漏
- [ ] AC-3: L1-A6 子 shot 时长之和 = 父 shot 时长 ± 100ms
- [ ] AC-4: L1-A7 downstream_bindings 引用合法性（P8/P9/P10）

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_103.py -v
```

## Completion Definition
Storyboard Reviewer L1 新增的 A4-A7 四条规则在单元测试中全部通过，shot 拆分逻辑保证子 shot 与父 shot 在文本区间和时长上严格对齐，downstream_bindings 引用全部合法。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_103.py | test_l1_a4_anchor_text_is_substring_of_polished_script |
| AC-2 | tests/unit/pipeline/test_spec_d_103.py | test_l1_a5_child_shot_intervals_no_overlap_no_gap |
| AC-3 | tests/unit/pipeline/test_spec_d_103.py | test_l1_a6_child_shot_durations_sum_equals_parent_within_100ms |
| AC-4 | tests/unit/pipeline/test_spec_d_103.py | test_l1_a7_downstream_bindings_reference_validity |
