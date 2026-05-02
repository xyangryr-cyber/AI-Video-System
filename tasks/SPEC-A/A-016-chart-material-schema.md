# [SPEC-A-016] ChartMaterial schema（含 axis_spec 子 schema）

## Metadata
- **task_id**: SPEC-A-016
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-4
- **delta_id**: PRD-DELTA-07 / TECH-DELTA-06
- **depends_on**: [SPEC-A-015]
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增 `chart_material` schema 作为 P7A 出口 / P8 入口的中间 contract（已抓数据 + 已生成 axis），与 v3.16 `ChartRequest`（用户意图层）通过 `chart_id ↔ request_id` 一一对应。落入 SPEC-0A.1 artifact registry。

## Allowed Files
- `src/shared/schemas/chart_material.py` (NEW Pydantic)
- `src/shared/types/chart_material.ts` (NEW TS)
- `schemas/chart_material.schema.json` (NEW JSON Schema)
- `src/shared/schemas/artifact_registry.py` (MODIFY 追加 1 条 chart_material 条目)
- `tests/unit/contracts/test_chart_material_schema.py` (NEW)

## Forbidden Files
- `src/shared/schemas/chart_request.py` (v3.16 既有，禁止重定义)
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：JSON Schema 校验合法/非法 payload，特别覆盖 axis_spec 边界（min < max、x_axis.range 长度=2、y_axis.scale_mode 枚举、verification_status 必为 "verified"）
- [ ] AC-2：Pydantic + TS 镜像，字段名/必填一致
- [ ] AC-3：与 `ChartRequest`（v3.16 SPEC-0A.11）的引用关系测试：`ChartMaterial.chart_id` 派生规则与 `ChartRequest.request_id` 一一对应（不重定义 ChartRequest）
- [ ] AC-4：property-based 测试（hypothesis）：随机生成 date_range + granularity → axis_spec.x_axis.labels 数量符合粒度（day=按日数 / week=按周数 / month=按月数，±1 容差）
- [ ] AC-5：artifact registry 一条新条目（phase_7a/chart_materials/chart_*.json）落入 SPEC-0A.1
- [ ] AC-6：冲突验证测试：构造 `chart_spec.kind=line` 但 `axis_spec.x_axis.type=category` 的不一致 payload，断言 L1 校验返回 violation

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_016.py -v
mypy src/shared/schemas/chart_material.py --strict
npx tsc --noEmit src/shared/types/chart_material.ts
python scripts/contracts/check_schema_alignment.py chart_material
```

## Completion Definition
schema 三态就位 + artifact registry 1 条新条目 + 全部 6 条 AC 测试 PASS + property-based 测试覆盖 6 种数据形态 + 与 ChartRequest 双向引用文档化。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_016.py | test_valid / test_invalid_y_axis_min_gt_max / test_x_axis_range_length / test_verification_status_must_be_verified |
| AC-2 | tests/unit/contracts/test_spec_a_016.py | test_pydantic_ts_alignment |
| AC-3 | tests/unit/contracts/test_spec_a_016.py | test_chart_id_derived_from_request_id |
| AC-4 | tests/unit/contracts/test_spec_a_016.py | test_property_based_axis_labels |
| AC-5 | tests/unit/contracts/test_spec_a_016.py | test_registry_contains_chart_material_entry |
| AC-6 | tests/unit/contracts/test_spec_a_016.py | test_l1_chart_axis_consistency |

## §23.9 验收门禁映射
- 第 8 行：chart_material schema + axis_spec 校验（本任务承担 schema + L1 校验入口；模板渲染消费由 F-013 承担；前端确认卡由 E-014 承担）
