# [SPEC-A-103] ChartRequest / AxisSpec / ChartStyleOverrides / StoryboardShotAnchor

## Metadata
- **task_id**: SPEC-A-103
- **spec_ref**: `SPEC-A` §A-BDD-4(SPEC-0A.11 + SPEC-0A.12)
- **depends_on**: [SPEC-A-100]
- **priority**: P0
- **estimated_complexity**: L

## Scope
定义图表请求与分镜锚点的统一契约:ChartRequest(7 状态枚举 + claim_refs)、AxisSpec(zero_based 选项)、ChartStyleOverrides、StoryboardShotAnchor(强制锚定字段 + 可选 downstream_bindings),覆盖 Pydantic 与 TS 两侧。

## Allowed Files
- `src/shared/schemas/chart_request.py`
- `src/shared/types/chart_request.ts`
- `src/shared/schemas/axis_spec.py`
- `src/shared/schemas/chart_style_overrides.py`
- `src/shared/schemas/storyboard_shot_anchor.py`
- `src/shared/types/storyboard_shot_anchor.ts`
- `tests/unit/contracts/test_chart_schemas.py`
- `tests/unit/contracts/test_shot_anchor_schema.py`

## Acceptance Criteria
- [ ] AC-1: `ChartRequest` 状态枚举 7 值(`awaiting_clarification/fetching/awaiting_verification/awaiting_confirmation/rendering/completed/cancelled/failed`)
- [ ] AC-2: `AxisSpec` 含 x_axis/y_axis 且 y_axis 支持 zero_based 布尔
- [ ] AC-3: `StoryboardShotAnchor` 强制字段 anchor_text ≤ 200 字 / script_span_id / start_char / end_char 均非空
- [ ] AC-4: `downstream_bindings` 三字段均 optional

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_103.py -v
```

## Completion Definition
ChartRequest/AxisSpec/ChartStyleOverrides/StoryboardShotAnchor 在 Pydantic + TS 两侧契约一致,所有 AC 对应测试 GREEN。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_103.py | test_chart_request_status_enum_has_seven_values |
| AC-2 | tests/unit/contracts/test_spec_a_103.py | test_axis_spec_supports_zero_based_on_y_axis |
| AC-3 | tests/unit/contracts/test_spec_a_103.py | test_storyboard_shot_anchor_requires_anchor_text_within_200_chars_and_span_fields |
| AC-4 | tests/unit/contracts/test_spec_a_103.py | test_downstream_bindings_three_fields_are_optional |
