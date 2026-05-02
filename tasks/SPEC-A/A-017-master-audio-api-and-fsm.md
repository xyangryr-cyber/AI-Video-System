# [SPEC-A-017] API GET /artifacts/master_audio + FSM phase_7a 枚举

## Metadata
- **task_id**: SPEC-A-017
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-5
- **delta_id**: PRD-DELTA-01 / PRD-DELTA-06 / TECH-DELTA-01 / TECH-DELTA-05 / TECH-DELTA-08
- **depends_on**: [SPEC-A-013, SPEC-A-015]
- **priority**: P0
- **estimated_complexity**: S

## Scope
在 SPEC-1A 路由总表追加 `GET /api/projects/{id}/artifacts/master_audio?phase={4|5|6}` 端点；扩展 SPEC-0A FSM `PhaseId` 枚举增加 `phase_7a` 子态；扩展 v3.16 `GET /phases/{phase}/detail` 端点的 `phase` 参数枚举。

## Allowed Files
- `src/shared/types/api_routes.ts` (MODIFY 追加新端点 + 扩 phase 枚举)
- `src/shared/schemas/api_master_audio.py` (NEW Pydantic Request/Response)
- `src/shared/types/api_master_audio.ts` (NEW TS Request/Response)
- `src/shared/types/phase_enum.ts` (MODIFY 追加 phase_7a)
- `src/shared/schemas/phase_enum.py` (MODIFY 追加 phase_7a)
- `tests/unit/contracts/test_master_audio_api.py` (NEW)
- `tests/unit/contracts/test_phase_enum.py` (NEW or MODIFY)

## Forbidden Files
- `src/backend/api/**` (实现由后续 task 承担，此处仅契约层)
- `src/backend/services/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：OpenAPI / Pydantic 路由定义包含新端点，路径与 query 参数（phase=4|5|6）契约准确
- [ ] AC-2：Response 模型字段：master_audio_url / download_url / based_on_phase / kind / checksum / version；与 A-013 `MasterAudioArtifact` 字段对齐
- [ ] AC-3：错误码契约：phase ∉ [4,5,6] → 400 `invalid_phase`；master 未就绪 → 404 `master_not_ready`
- [ ] AC-4：`PhaseId` 枚举类型新增 `phase_7a`，TS + Pydantic 同步；既有 P0-P11 不删不改
- [ ] AC-5：v3.16 `GET /phases/{phase}/detail` 的 `phase` 参数枚举扩展支持 `phase_7a`（回归测试 v3.16 既有路径）
- [ ] AC-6：phases 表 phase_id 列允许 `phase_7a` 值（跨与 SPEC-1B 表约束的契约一致性，本任务在 schema 层文档化，DDL 修改由 B-013 之外的迁移任务承担——由 C-021 / D-021 协同）

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_017.py -v
mypy src/shared/schemas/api_master_audio.py --strict
npx tsc --noEmit src/shared/types/api_master_audio.ts src/shared/types/phase_enum.ts
```

## Completion Definition
新端点契约 + 新 phase 枚举 + 错误码契约文档化 + 全部 6 条 AC 测试 PASS + v3.16 既有端点不破坏（回归通过）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_017.py | test_route_definition_present / test_query_param_phase_enum |
| AC-2 | tests/unit/contracts/test_spec_a_017.py | test_response_fields_match_master_audio_artifact |
| AC-3 | tests/unit/contracts/test_spec_a_017.py | test_invalid_phase_returns_400 / test_master_not_ready_returns_404 |
| AC-4 | tests/unit/contracts/test_spec_a_017.py | test_phase_7a_in_enum / test_p0_to_p11_unchanged |
| AC-5 | tests/unit/contracts/test_spec_a_017.py | test_v316_phase_detail_supports_phase_7a |
| AC-6 | tests/unit/contracts/test_spec_a_017.py | test_phase_id_column_allows_phase_7a_value |

## §23.9 验收门禁映射
- 第 7 行：P7A FSM 态位（本任务承担枚举；FSM 转换边由 D-021 承担）
- 第 10 行：前端 master_audio_url 可用（本任务承担 API 契约；前端组件由 E-011/E-012/E-013 承担）
