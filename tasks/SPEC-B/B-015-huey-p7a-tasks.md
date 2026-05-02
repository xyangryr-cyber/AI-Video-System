# [SPEC-B-015] Huey worker — P7A material_fetch / material_verify / chart_material_fetch 任务类型

## Metadata
- **task_id**: SPEC-B-015
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §B-AUDP7A-3
- **delta_id**: TECH-DELTA-05
- **depends_on**: [SPEC-A-015]
- **priority**: P0
- **estimated_complexity**: M

## Scope
为 P7A MaterialFetcher / MaterialVerifier 注册三类 Huey 任务（material_fetch / material_verify / chart_material_fetch），分配独立 `phase_7a` 队列，配置优先级、重试、超时、限流规则；与 task_ledger 关联。

## Allowed Files
- `src/backend/workers/p7a_tasks.py` (NEW Huey @task 注册)
- `src/backend/workers/p7a_throttle.py` (NEW provider 维度令牌桶)
- `config/huey_queues.yaml` (MODIFY 追加 phase_7a 队列)
- `tests/unit/workers/test_p7a_tasks.py` (NEW)
- `tests/unit/workers/test_p7a_throttle.py` (NEW)
- `tests/integration/workers/test_p7a_task_ledger_consistency.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/agents/**` (P7A Agent 由 C-021 实现，本任务仅提供任务调度基础)
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：Huey 注册三个新 task：`material_fetch`（queue=phase_7a, priority=5, retries=3, timeout=60s）/ `material_verify`（queue=phase_7a, priority=5, retries=2, timeout=30s）/ `chart_material_fetch`（queue=phase_7a, priority=4, retries=3, timeout=90s）
- [ ] AC-2：本地 worker 启动后能消费三类任务（`docker compose up -d` 后日志可见三个 task 注册）
- [ ] AC-3：限流测试：单 provider 并发 > 配额 → 任务排队，无丢失（构造 5 个并发 fetch，配额=2，断言 3 个排队）
- [ ] AC-4：失败重试测试：fetch 抛 5xx → 自动重试至上限 3 次 → 终态写 `verification_status=missing` 到 manifest（mock provider 验证）
- [ ] AC-5：task_ledger 一致性：每条 Huey 任务必有一条对应 task_ledger 记录（type=material_fetch / material_verify，与 v3.16 task_ledger.type 扩展一致）
- [ ] AC-6：phase_7a 队列与 phase_8 渲染队列独立，互不阻塞（构造长 fetch + 短 render 同时跑，验证渲染不被阻塞）
- [ ] AC-7：worker 进程命令行参数包含 `-Q default,claim_verification,claim_verification_priority,phase_7a`，不破坏 v3.16 既有队列

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_015.py -v
docker compose up -d worker
docker compose logs worker | grep -E "phase_7a|material_fetch|material_verify|chart_material_fetch"
```

## Completion Definition
三 Huey 任务注册 + 限流模块 + worker 配置 + 全部 7 条 AC 测试 PASS + 与 v3.16 既有 claim_verification 队列零冲突。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_015.py | test_material_fetch_registered / test_material_verify_registered / test_chart_material_fetch_registered |
| AC-2 | tests/unit/infra/test_spec_b_015.py | test_worker_consumes_three_task_types |
| AC-3 | tests/unit/infra/test_spec_b_015.py | test_provider_quota_throttling |
| AC-4 | tests/unit/infra/test_spec_b_015.py | test_fetch_retry_to_missing |
| AC-5 | tests/unit/infra/test_spec_b_015.py | test_huey_task_ledger_one_to_one |
| AC-6 | tests/unit/infra/test_spec_b_015.py | test_phase_7a_does_not_block_phase_8 |
| AC-7 | tests/unit/infra/test_spec_b_015.py | test_worker_cli_args_include_phase_7a |

## §23.9 验收门禁映射
- 第 7 行：P7A FSM 三角色串行（本任务承担 worker 调度基础；Agent 实现由 C-021 承担）
