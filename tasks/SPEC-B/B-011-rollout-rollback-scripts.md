# [SPEC-B-011] 发布级 Rollout/Rollback 脚本

## Metadata
- **task_id**: SPEC-B-011
- **spec_ref**: SPEC-14.3
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL), [SPEC-B-001], [SPEC-B-003]
- **priority**: P1
- **estimated_complexity**: M

## Scope
为三种发布失败场景编写可执行的回滚脚本：(1) Docker Compose 升级失败 → 恢复旧 docker-compose.yml 并重启；(2) Schema migration 失败 → 从 app.sqlite3.bak 恢复；(3) Worker 升级后任务恢复失败 → 孤儿任务清理并重启 worker。每种场景回滚后 5 分钟内恢复正常。

## Allowed Files
- `scripts/rollback/compose_rollback.sh`
- `scripts/rollback/schema_rollback.sh`
- `scripts/rollback/worker_recovery.sh`
- `scripts/rollback/README.md`
- `tests/unit/infra/test_rollback_scripts.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `docker-compose.yml` (不应被回滚脚本本身修改，脚本只做文件替换)

## Acceptance Criteria
- [ ] AC-1: `scripts/rollback/compose_rollback.sh` 可执行：down → 恢复旧 yml → up
- [ ] AC-2: `scripts/rollback/schema_rollback.sh` 可执行：停服务 → 恢复 .bak → 重启
- [ ] AC-3: `scripts/rollback/worker_recovery.sh` 可执行：检测孤儿任务 → 重置状态 → 重启 worker
- [ ] AC-4: 回滚后服务在 5 分钟内恢复正常（脚本中含健康检查等待）
- [ ] AC-5: 每个脚本有 `--dry-run` 模式（只打印操作不执行）

## Verification Commands
```bash
bash scripts/rollback/compose_rollback.sh --dry-run
bash scripts/rollback/schema_rollback.sh --dry-run
bash scripts/rollback/worker_recovery.sh --dry-run
pytest tests/unit/infra/test_spec_b_011.py -v
```

## Completion Definition
三种回滚场景各有可执行脚本，dry-run 模式验证通过，健康检查逻辑完整。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_011.py | test_compose_rollback_dry_run |
| AC-2 | tests/unit/infra/test_spec_b_011.py | test_schema_rollback_dry_run |
| AC-3 | tests/unit/infra/test_spec_b_011.py | test_worker_recovery_dry_run |
| AC-4 | tests/unit/infra/test_spec_b_011.py | test_health_check_in_scripts |
| AC-5 | tests/unit/infra/test_spec_b_011.py | test_dry_run_no_side_effects |
