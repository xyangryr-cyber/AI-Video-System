# [SPEC-B-012] 非功能需求验收与测试策略基础设施

## Metadata
- **task_id**: SPEC-B-012
- **spec_ref**: SPEC-15.1, SPEC-15.2, SPEC-15.3, SPEC-15.4, SPEC-16.1, SPEC-16.2, SPEC-16.3, SPEC-16.4
- **depends_on**: [SPEC-A-xxx] (SPEC-1A API 路由), [SPEC-B-001], [SPEC-B-003], [SPEC-B-009]
- **priority**: P2
- **estimated_complexity**: L
- **bdd_tags**: [@performance]

## Scope
实现非功能需求的后端部分：(1) 同一项目单 Tab 限制（后端锁机制）；(2) 连续 5 次 regenerate 引导人工编辑；(3) 确保无 HTTP handler 中同步等待 TTS/渲染；(4) .gitignore 含 .env，代码中无硬编码 API Key。搭建测试策略基础设施：(5) eval 集目录结构 `tests/eval/{agent_name}.jsonl`；(6) Reviewer 黄金数据集格式；(7) CI path filter 配置（prompts/**/agents/** 变更触发回归）；(8) 骨架集成测试 `tests/integration/test_pipeline_e2e.py` 框架（mock LLM）。

## Allowed Files
- `src/backend/api/middleware/single_tab.py`
- `src/backend/core/regenerate_limiter.py`
- `tests/eval/` (目录结构和模板文件)
- `tests/integration/test_pipeline_e2e.py`
- `.github/workflows/eval_regression.yml`
- `tests/unit/infra/test_nonfunctional.py`

## Forbidden Files
- `src/frontend/**` (前端单 Tab UI 由 SPEC-E 负责)
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 同一项目第二个连接请求被拒绝（返回 409 + 提示信息）
- [ ] AC-2: 第 5 次 regenerate 后 API 返回 `suggest_manual_edit=true`
- [ ] AC-3: 无 HTTP handler 中同步等待 TTS/渲染的代码路径
- [ ] AC-4: `.gitignore` 含 `.env`，`grep -rn "sk-" src/**/*.py` 结果为空
- [ ] AC-5: `tests/eval/` 目录存在，包含 JSONL 模板文件（{input, expected_output, eval_criteria[], tags[]}）
- [ ] AC-6: CI 配置含 `prompts/**` 和 `agents/**` path filter
- [ ] AC-7: `tests/integration/test_pipeline_e2e.py` 骨架存在，使用 mock LLM，可运行

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_012.py -v
ls tests/eval/
grep -rn "sk-" src/backend/**/*.py  # 应无结果
cat .github/workflows/eval_regression.yml | grep "paths:"
```

## Completion Definition
非功能需求的后端约束已实现，测试策略基础设施（eval 目录、CI 配置、骨架集成测试）就位。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_012.py | test_single_tab_rejects_second_connection |
| AC-2 | tests/unit/infra/test_spec_b_012.py | test_regenerate_limit_suggests_manual_edit |
| AC-3 | tests/unit/infra/test_spec_b_012.py | test_no_sync_wait_in_handlers |
| AC-7 | tests/unit/infra/test_spec_b_012.py | test_pipeline_skeleton_runs |
