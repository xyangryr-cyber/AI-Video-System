# [SPEC-A-018] 错误码 render_failed / material_missing / material_unverified + WebSocket phase.shot_blocked 事件

## Metadata
- **task_id**: SPEC-A-018
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-6
- **delta_id**: PRD-DELTA-08 / TECH-DELTA-07
- **depends_on**: [SPEC-A-015]
- **priority**: P0
- **estimated_complexity**: S

## Scope
在 SPEC-13A 错误码体系追加 3 个新码（`render_failed` 500 / `material_missing` 422 / `material_unverified` 422），在 SPEC-11A WebSocket 事件追加 `phase.shot_blocked` 事件，并约束 SPEC-13B 统一日志格式：渲染失败 / 阻断日志的 `event` 字段必须为新 3 个错误码之一。

## Allowed Files
- `src/shared/constants/error_codes.py` (MODIFY 追加 3 个枚举)
- `src/shared/types/error_codes.ts` (MODIFY 追加 3 个枚举)
- `src/shared/schemas/ws_events.py` (MODIFY 追加 PhaseShotBlockedEvent)
- `src/shared/types/ws_events.ts` (MODIFY 追加 PhaseShotBlockedEvent)
- `src/shared/constants/log_event_codes.py` (MODIFY 加入 3 个允许 event 名)
- `tests/unit/contracts/test_error_codes_v317.py` (NEW)
- `tests/unit/contracts/test_phase_shot_blocked_event.py` (NEW)

## Forbidden Files
- `src/backend/api/**`
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：SPEC-13A 表新增 3 行（含 http_status 500/422/422 + 触发场景 + 处理建议）；Pydantic + TS ErrorCode 枚举同步；既有 17 个错误码不删不改
- [ ] AC-2：`PhaseShotBlockedEvent` Pydantic + TS 字段：type=`phase.shot_blocked` / project_id / phase=`P8` / shot_id / error_code ∈ {material_missing, material_unverified} / blocking_material_ids / ts ISO8601
- [ ] AC-3：日志格式校验：渲染失败/阻断行的 `event` 字段必须属于新 3 种之一；构造非法 event 名抛 `InvalidLogEventError`
- [ ] AC-4：单测：构造三类失败场景各一例（mock 渲染异常 / 物料不存在 / 物料未验证），断言对应错误码枚举触发
- [ ] AC-5：`PhaseShotBlockedEvent` 与 v3.16 既有 17 种事件不冲突（type 命名空间唯一）

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_018.py -v
mypy src/shared/constants/error_codes.py src/shared/schemas/ws_events.py --strict
npx tsc --noEmit src/shared/types/error_codes.ts src/shared/types/ws_events.ts
```

## Completion Definition
错误码 + 事件契约就位 + 日志格式约束 + 全部 5 条 AC 测试 PASS + v3.15/v3.16 既有错误码与事件不破坏。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_018.py | test_three_new_codes_present / test_http_status_mapping / test_v315_codes_intact |
| AC-2 | tests/unit/contracts/test_spec_a_018.py | test_event_payload_schema / test_error_code_constrained_to_two_values |
| AC-3 | tests/unit/contracts/test_spec_a_018.py | test_log_event_field_constrained / test_invalid_log_event_raises |
| AC-4 | tests/unit/contracts/test_spec_a_018.py | test_render_failed_triggered / test_material_missing_triggered / test_material_unverified_triggered |
| AC-5 | tests/unit/contracts/test_spec_a_018.py | test_event_type_namespace_unique |

## §23.9 验收门禁映射
- 第 9 行：MaterialReadinessCheck 阻断 P8（本任务承担错误码 + 事件契约；执行逻辑由 C-022 / D-022 / F-014 承担）
