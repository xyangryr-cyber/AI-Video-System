# [SPEC-F-101] AxisSpec 自动生成算法(纯确定性)

## Metadata
- **task_id**: SPEC-F-101
- **spec_ref**: SPEC-F §F-BDD-2
- **depends_on**: [SPEC-A-103]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现一个纯确定性的 AxisSpec 自动生成算法，根据数据维度类型与数值范围推导 x_axis/y_axis 配置、tick 格式与 zero_based 启发式策略，前后端共用同一份逻辑。

## Allowed Files
- `src/frontend/remotion/utils/axis_spec_generator.ts`
- `src/backend/services/axis_spec_generator.py`
- `tests/unit/axis_spec/test_axis_spec_determinism.ts`

## Acceptance Criteria
- [ ] AC-1: day/week/month → x_axis.type=time;category 输入 → category
- [ ] AC-2: y_axis.min/max = data min/max ± 5%
- [ ] AC-3: zero_based 启发式:(max-min)/max > 0.5 时 false
- [ ] AC-4: tick_format 依数值范围自动选 0.01/1/1k/1M
- [ ] AC-5: 相同输入产出相同结果(纯函数,property-based)

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_101.py -v
```

## Completion Definition
AxisSpec 生成器在前端 TS 与后端 Python 中行为一致、纯函数、可被 property-based 测试反复重放且产出相同结果，覆盖时间/类目轴推断、min/max ±5%、zero_based 启发式与 tick_format 自动选档。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_101.py | test_x_axis_time_vs_category_inference |
| AC-2 | tests/unit/media-render/test_spec_f_101.py | test_y_axis_min_max_padding_5pct |
| AC-3 | tests/unit/media-render/test_spec_f_101.py | test_zero_based_heuristic_threshold |
| AC-4 | tests/unit/media-render/test_spec_f_101.py | test_tick_format_auto_selection |
| AC-5 | tests/unit/media-render/test_spec_f_101.py | test_property_based_determinism |
