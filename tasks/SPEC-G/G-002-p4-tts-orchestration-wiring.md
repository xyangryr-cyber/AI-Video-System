# [SPEC-G-002] P4 TTS 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-002
- **spec_ref**: SPEC-G2.2 (P4 TTS)
- **depends_on**: [SPEC-G-001, SPEC-G-000e]
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase4.feature` "TTS 应以异步长任务方式执行" 当前 FAIL（视为 RED）→ 重写 step definitions 走编排层 → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase4_steps.py`，将直接调用 `TTSAgent` 的 step definitions 改为通过 `WorkflowEngine.create_task()` + Dispatcher 调用。BDD 场景"TTS 应以异步长任务方式执行"当前因 step 直接调 agent（stateless 纯函数，不创建 async task）而失败。

**文件大小预警**: `phase4_steps.py` 当前约 80 行，重写后可能逼近 400 行单文件限制（HARNESS §6）。实施时需监控行数，必要时拆分为 `phase4_steps/` 子模块。

## Allowed Files
- `tests/integration/bdd/steps/phase4_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/tts_agent.py` (Agent 实现正确，不需修改)
- `src/frontend/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: `phase4_steps.py` 不再直接 import `TTSAgent`
- [ ] AC-2: When step "用户启动旁白生成" 调用 `WorkflowEngine.create_task(project_id=..., phase=4, task_type="generate_narration", params=...)`（注意: 参数名是 `task_type` 不是 `action`，`params` 不是 `payload`；返回值是 `str` 不是 `dict`）
- [ ] AC-3: Then step "系统应创建 generate_artifact 的 async task" → PASS（task_ledger 行写入成功即 PASS）
- [ ] AC-4: Then step "async_tasks.status 应先为 pending 后变为 running" → PASS（依赖 G-000 worker tasks 已落地）
- [ ] AC-5: Then step "关闭浏览器不应中断该任务" → PASS（task_ledger 状态可查询）
- [ ] AC-6: `pytest tests/unit/ -q` 无回归（保持 1100+ passed）

## Verification Commands
```bash
pytest tests/integration/bdd/features/phase4.feature -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase4_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase4_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase4.feature` 的 step definitions 走编排层完整路径（WorkflowEngine → Dispatcher → Agent）。AC-4 在 P-1 解决前标记为 KNOWN_BLOCKED，其余 Then step 通过。完成后追加一行 commit 记录到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2-5 | tests/integration/bdd/features/phase4.feature | TTS 应以异步长任务方式执行 |
