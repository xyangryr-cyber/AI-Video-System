# [SPEC-C-021] P7A 三角色 — StoryboardAssetPlanner / MaterialFetcher / MaterialVerifier + WorkflowEngine 编排

## Metadata
- **task_id**: SPEC-C-021
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-6
- **delta_id**: TECH-DELTA-05
- **depends_on**: [SPEC-A-015, SPEC-A-016, SPEC-A-017, SPEC-B-015]
- **priority**: P0
- **estimated_complexity**: L

## Scope
新增三个 P7A Agent（一个 LLM Planner + 两个程序化 Fetcher/Verifier），WorkflowEngine 接入 phase_7a 编排：P7 PASS → Planner 一次性输出 manifest → 对每个 material 派发 fetch Huey 任务 → fetch 完成回调派发 verify → 全部结束触发 Gate 7A。shot_id 与 v3.16 StoryboardShotAnchor 对齐。

## Allowed Files
- `src/backend/agents/storyboard_asset_planner.py` (NEW LLM Agent)
- `src/backend/agents/material_fetcher.py` (NEW 程序化 + 工具调用)
- `src/backend/agents/material_verifier.py` (NEW L1 + L2 FactChecker)
- `src/backend/engine/phase_7a_orchestrator.py` (NEW；WorkflowEngine 接入)
- `src/backend/repositories/material_manifest_repo.py` (NEW manifest 读写)
- `tests/unit/agents/test_storyboard_asset_planner.py` (NEW)
- `tests/unit/agents/test_material_fetcher.py` (NEW)
- `tests/unit/agents/test_material_verifier.py` (NEW)
- `tests/integration/engine/test_phase_7a_orchestration.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/api/**`
- `src/backend/reviewers/material_readiness_*.py` (由 C-022 承担)
- `src/backend/services/**` (除 manifest_repo 外)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：`StoryboardAssetPlanner` 单测：mock 分镜 + chart_requests → 输出合法 manifest（material_manifest.schema.json 通过）；包含 chart 类与非 chart 类各 ≥ 1 条
- [ ] AC-2：`MaterialFetcher` 三种 source.kind 各一例：api（mock DataService）/ url（mock HTTP）/ internal（本地路径）；fetched_at 字段写入；文件落 phase_7a/verified_materials/{material_id}.{ext}
- [ ] AC-3：`MaterialVerifier` 三种结果：正常 → verified；缺失 → missing；数据不一致 → rejected；状态机断言通过 A-015 schema
- [ ] AC-4：编排集成测试：从 P7 PASS → phase_7a 启动 → manifest 写入 → Huey fetch/verify 链路 → 全部 verified → FSM 推进到 P8 入口
- [ ] AC-5：失败重试：fetch 抛 5xx 3 次 → verification_status 终态 missing；不阻塞其他 material
- [ ] AC-6：shot_id 一致性：每个 material.shot_id 必须能在 v3.16 StoryboardShotAnchor 中找到（构造负样例必失败）
- [ ] AC-7：chart 类 material 同时输出 chart_material（A-016 schema），写入 phase_7a/chart_materials/chart_*.json

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_021.py -v
mypy src/backend/agents/storyboard_asset_planner.py src/backend/agents/material_fetcher.py src/backend/agents/material_verifier.py src/backend/engine/phase_7a_orchestrator.py --strict
```

## Completion Definition
三 Agent + 编排器 + manifest repo + 全部 7 条 AC PASS + e2e 覆盖正常路径 + 三类结果状态机 + 失败重试 + chart 双产物。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_021.py | test_planner_outputs_valid_manifest / test_includes_chart_and_non_chart |
| AC-2 | tests/unit/backend-core/test_spec_c_021.py | test_fetch_api / test_fetch_url / test_fetch_internal |
| AC-3 | tests/unit/backend-core/test_spec_c_021.py | test_verify_verified / test_verify_missing / test_verify_rejected |
| AC-4 | tests/unit/backend-core/test_spec_c_021.py | test_p7_pass_to_p8_full_chain |
| AC-5 | tests/unit/backend-core/test_spec_c_021.py | test_fetch_retry_to_missing_isolates |
| AC-6 | tests/unit/backend-core/test_spec_c_021.py | test_shot_id_must_exist_in_anchor |
| AC-7 | tests/unit/backend-core/test_spec_c_021.py | test_chart_material_emitted_alongside |

## §23.9 验收门禁映射
- 第 7 行：P7A FSM 态位 + 三角色串行
