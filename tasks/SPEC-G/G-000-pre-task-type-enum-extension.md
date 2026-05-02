# [SPEC-G-000-pre] TaskType 契约扩展 — 新增 6 个 Phase-Level 枚举值

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000-pre
> **顺序**: 本卡是 G-000 拆解的第一张子卡，必须先于 G-000a/b/c/d/e 完成

## Metadata
- **task_id**: SPEC-G-000-pre
- **spec_ref**: SPEC-A SPEC-1B (task_ledger.type DDL) + SPEC-C SPEC-3.2 (TaskType enum)
- **depends_on**: []（无前置 task card，但共同前置必须满足: `.venv` 已重装、`pytest tests/unit/ -q` collection error 为 0、baseline 数字已记录）
- **priority**: P0（阻塞所有 G-000 子卡）
- **estimated_complexity**: S (~50 行)

## Scope
`src/backend/engine/task_types.py:30` 的 `TaskType` 枚举只有 8 个标准值（`generate_artifact` / `regenerate_section` / `user_revision` / `review` / `research` / `verify` / `cross_check` / `user_annotation`）。SPEC-G2.2 要求 BDD 通过 `WorkflowEngine.create_task(task_type=...)` 调起 6 个 phase 级 task type——这些 task_type **不在 enum 中**。

本卡扩展 `TaskType` enum，新增 6 个 phase-level type 作为 `generate_artifact` 的特化变体，行为等同 `generate_artifact`（允许 `produces_version`，禁止 `target_version`）。

**新增的 6 个枚举值**:
| 枚举名 | 字符串值 | 对应 Phase |
|--------|---------|-----------|
| `GENERATE_NARRATION` | `generate_narration` | P4 TTS |
| `PREVIEW_MIX` | `preview_mix` | P5 BGM |
| `PLAN_LAYOUT` | `plan_layout` | P6 SFX |
| `RENDER_KEYFRAMES` | `render_keyframes` | P8 Keyframe |
| `COMPOSE_ROUGH_CUT` | `compose_rough_cut` | P10 RoughCut |
| `EXPORT_FINAL` | `export_final` | P11 FinalCut |

**决策（禁止重新讨论）**: 扩展 enum，不用 `generate_artifact + params` 二级路由（会让 dispatcher 多绕一层），也不用 enum 外字符串（违反 SPEC-3.2 类型纪律）。

## Allowed Files
- `src/backend/engine/task_types.py`
- `src/shared/schemas/task_ledger.json`（如存在）
- `tests/unit/backend-core/test_task_types.py`（创建/更新）

## Forbidden Files
- 任何 `docs/specs/SPEC-*.md`（SPEC 改动留给后续 doc-only commit）
- `src/backend/engine/workflow_engine.py`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `TaskType` 增加 6 个新枚举值: `GENERATE_NARRATION` / `PREVIEW_MIX` / `PLAN_LAYOUT` / `RENDER_KEYFRAMES` / `COMPOSE_ROUGH_CUT` / `EXPORT_FINAL`
- [ ] AC-2: 6 个新 type 在 `Task` Pydantic 模型的 `_validate_version_fields` 中归入"允许 produces_version、禁止 target_version"分支（行为等同 `generate_artifact`）
- [ ] AC-3: 单测: 6 个新 type 各自能通过 Task 模型 validation；带 `target_version` 时报 `ValueError`
- [ ] AC-4: 无回归: `pytest tests/unit/backend-core/test_task_types.py` 全绿；`pytest tests/unit/ -q` 通过数 ≥ 干净 baseline

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/backend-core/test_task_types.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/engine/task_types.py
.venv/bin/mypy src/backend/engine/task_types.py --explicit-package-bases
```

## Completion Definition
`TaskType` 枚举包含 6 个新 phase-level 值。新值在 `_validate_version_fields` 中正确路由。单测全部通过，无回归。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_task_types.py | `test_generate_narration_type_exists` |
| AC-1 | tests/unit/backend-core/test_task_types.py | `test_preview_mix_type_exists` |
| AC-1 | tests/unit/backend-core/test_task_types.py | `test_all_6_phase_types_in_enum` |
| AC-2 | tests/unit/backend-core/test_task_types.py | `test_generate_narration_allows_produces_version` |
| AC-2 | tests/unit/backend-core/test_task_types.py | `test_preview_mix_allows_produces_version` |
| AC-3 | tests/unit/backend-core/test_task_types.py | `test_preview_mix_rejects_target_version` |
| AC-3 | tests/unit/backend-core/test_task_types.py | `test_all_6_phase_types_reject_target_version` |

## TDD Path
1. **RED**: 在 `test_task_types.py` 加 `test_generate_narration_type_exists`、`test_preview_mix_allows_produces_version` 等 6+ 个新测试；跑应失败
2. Commit: `[SPEC-G-000-pre] RED: phase-level TaskType enum tests`
3. **GREEN**: 在 `task_types.py` 加 6 个枚举值 + 在 `_validate_version_fields` 兼容分支增加新 type
4. Commit: `[SPEC-G-000-pre] GREEN: phase-level TaskType enum + Task validation`
