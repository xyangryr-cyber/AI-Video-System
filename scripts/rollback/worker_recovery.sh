#!/usr/bin/env bash
# [SPEC-B-011] Worker upgrade crash recovery.
# Usage: worker_recovery.sh [--dry-run]
# Steps: detect orphan tasks -> reset status -> restart worker
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DB_FILE="$REPO_ROOT/data/db/app.sqlite3"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

count_orphans() {
    sqlite3 "$DB_FILE" \
        "SELECT COUNT(*) FROM async_tasks WHERE status = 'running'" 2>/dev/null || echo "0"
}

reset_orphans() {
    sqlite3 "$DB_FILE" \
        "UPDATE async_tasks SET status = 'queued', worker_id = NULL, started_at = NULL WHERE status = 'running'" 2>/dev/null
}

health_check() {
    local max_wait=300
    local elapsed=0
    local interval=5
    while [[ $elapsed -lt $max_wait ]]; do
        if curl -sf http://localhost:8000/api/observability/status > /dev/null 2>&1; then
            echo "[OK] Health check passed after ${elapsed}s"
            return 0
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    echo "[FAIL] Health check timed out after ${max_wait}s"
    return 1
}

orphan_count=$(count_orphans)

if $DRY_RUN; then
    echo "[DRY-RUN] Would execute:"
    echo "  1. Detect orphan tasks (currently $orphan_count running)"
    echo "  2. UPDATE async_tasks SET status='queued' WHERE status='running'"
    echo "  3. docker compose -f $REPO_ROOT/docker-compose.yml restart worker"
    echo "  4. Health check: curl http://localhost:8000/api/observability/status"
    exit 0
fi

echo "[1/3] Detected $orphan_count orphan task(s) in 'running' state."
if [[ $orphan_count -gt 0 ]]; then
    echo "Resetting orphan tasks to 'queued'..."
    reset_orphans
    echo "Done."
else
    echo "No orphans to recover."
fi

echo "[2/3] Restarting worker..."
docker compose -f "$REPO_ROOT/docker-compose.yml" restart worker

echo "[3/3] Waiting for health check..."
if health_check; then
    echo "Worker recovery complete."
else
    echo "Worker restarted but health check failed. Manual intervention required."
    exit 1
fi
