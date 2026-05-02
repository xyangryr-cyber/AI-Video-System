#!/usr/bin/env bash
# [SPEC-B-011] Docker Compose upgrade rollback.
# Usage: compose_rollback.sh [--dry-run]
# Steps: down -> restore old docker-compose.yml -> up
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
BACKUP_FILE="$REPO_ROOT/docker-compose.yml.bak"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

health_check() {
    local max_wait=300  # 5 minutes
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
    echo "  1. docker compose -f $COMPOSE_FILE down"
    echo "  2. cp $BACKUP_FILE $COMPOSE_FILE  (if backup exists)"
    echo "  3. docker compose -f $COMPOSE_FILE up -d"
    echo "  4. Health check: curl http://localhost:8000/api/observability/status"
    exit 0
fi

echo "[1/3] Stopping services..."
docker compose -f "$COMPOSE_FILE" down

if [[ -f "$BACKUP_FILE" ]]; then
    echo "[2/3] Restoring backup docker-compose.yml..."
    cp "$BACKUP_FILE" "$COMPOSE_FILE"
else
    echo "[WARN] No backup file at $BACKUP_FILE, using current compose file"
fi

echo "[3/3] Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for health check..."
if health_check; then
    echo "Rollback complete."
else
    echo "Rollback applied but health check failed. Manual intervention required."
    exit 1
fi
