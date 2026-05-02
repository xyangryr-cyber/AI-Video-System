#!/usr/bin/env bash
# [SPEC-B-001] Bootstrap ./data/ directory tree and secure .env permissions.
# Idempotent: safe to re-run. Called once at container startup or by devs
# after `git clone`.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Data subdirectories — keep aligned with SPEC-B storage directory layout.
mkdir -p data/config data/users data/projects data/logs data/db

# Protect secrets. Only chmod if .env exists (first-run users may not have
# copied .env.example → .env yet).
if [[ -f .env ]]; then
  chmod 600 .env
fi

echo "[init-data-dirs] data/{config,users,projects,logs,db} ready"
