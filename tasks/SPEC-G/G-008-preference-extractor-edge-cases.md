# [SPEC-G-008] PreferenceExtractor 边缘情况修复

## Metadata
- **task_id**: SPEC-G-008
- **spec_ref**: SPEC-G3.1, SPEC-G3.2
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S
- **TDD 起点**: `preferences.feature` "nothing_found 仍需用户显式完成门禁动作" + `preferences-2.feature` "音频完成后系统应比较实际设置与偏好差异" 当前 FAIL（视为 RED）→ 修复 extract() 返回值 + 补齐 writeback API → scenario PASS（GREEN）

## Scope
修复 `PreferenceExtractor.extract()` 在无匹配输入时返回 `None` 的问题——应统一返回结构化 dict `{nothing_found: True, candidates: []}`。同时补齐 `compare_for_writeback` 和 `build_writeback_suggestions` API 用于音频完成后比较实际设置与偏好差异。

## Allowed Files
- `src/backend/agents/preference_extractor.py`
- `tests/integration/bdd/steps/preferences_steps.py`
- `tests/integration/bdd/steps/preferences_2_steps.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/engine/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: `extract()` 在无匹配时返回 `{"nothing_found": True, "candidates": [], "confidence": 0.0}`，而非 `None`
- [ ] AC-2: BDD 场景 "nothing_found 仍需用户显式完成门禁动作" → PASS
- [ ] AC-3: `compare_for_writeback()` 和 `build_writeback_suggestions()` 方法存在（至少 `compare_for_writeback`），返回结构化的回写建议列表
- [ ] AC-4: BDD 场景 "音频完成后系统应比较实际设置与偏好差异并建议是否回写" → PASS
- [ ] AC-5: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/features/preferences.feature -v
pytest tests/integration/bdd/features/preferences-2.feature -v
pytest tests/unit/ -q
ruff check src/backend/agents/preference_extractor.py tests/integration/bdd/steps/preferences_steps.py tests/integration/bdd/steps/preferences_2_steps.py
mypy src/backend/agents/preference_extractor.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`preferences.feature` 的 nothing_found 场景 + `preferences-2.feature` 的 writeback 场景均通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/preferences.feature | nothing_found 仍需用户显式完成门禁动作 |
| AC-4 | tests/integration/bdd/features/preferences-2.feature | 音频完成后系统应比较实际设置与偏好差异并建议是否回写 |
