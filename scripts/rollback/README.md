# Rollback Scripts (SPEC-B-011)

Three rollback scenarios for production deployment failures.

## Scripts

| Script | Scenario | Steps |
|--------|----------|-------|
| `compose_rollback.sh` | Docker Compose upgrade fails | down -> restore old yml -> up |
| `schema_rollback.sh` | Schema migration fails | stop -> restore .bak -> restart |
| `worker_recovery.sh` | Worker upgrade crashes | detect orphans -> reset -> restart |

## Dry-Run Mode

All scripts support `--dry-run`:

```bash
bash scripts/rollback/compose_rollback.sh --dry-run
bash scripts/rollback/schema_rollback.sh --dry-run
bash scripts/rollback/worker_recovery.sh --dry-run
```

## Health Check

After rollback, each script waits up to 5 minutes for
`curl http://localhost:8000/api/observability/status` to respond OK.
