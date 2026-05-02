#!/usr/bin/env bash
# [SPEC-B-011] Schema migration rollback.
# Usage: schema_rollback.sh [--dry-run]
# Steps: stop services -> restore app.sqlite3.bak -> restart
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DB_FILE="$REPO_ROOT/data/db/app.sqlite3"
BACKUP_FILE="$REPO_ROOT/data/db/app.sqlite3.bak"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

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

if $DRY_RUN; then
    echo "[DRY-RUN] Would execute:"
    echo "  1. docker compose -f $REPO_ROOT/docker-compose.yml down"
    echo "  2. cp $BACKUP_FILE $DB_FILE  (if backup exists)"
    echo "  3. docker compose -f $REPO_ROOT/docker-compose.yml up -d"
    echo "  4. Health check: curl http://localhost:8000/api/observability/status"
    exit 0
fi

echo "[1/3] Stopping services..."
docker compose -f "$REPO_ROOT/docker-compose.yml" down

if [[ -f "$BACKUP_FILE" ]]; then
    echo "[2/3] Restoring database from backup..."
    cp "$BACKUP_FILE" "$DB_FILE"
else
    echo "[ERROR] No backup file at $BACKUP_FILE"
    exit 1
fi

echo "[3/3] Starting services..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up -d

echo "Waiting for health check..."
if health_check; then
    echo "Schema rollback complete."
else
    echo "Rollback applied but health check failed. Manual intervention required."
    exit 1
fi
