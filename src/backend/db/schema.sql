-- [SPEC-A-007] SQLite Database Schema DDL
-- Authority: SPEC-A-contracts.md SPEC-1B
-- Scope: V1 core tables (10). BDD-added tables (claims, verification_records,
-- stage_preferences) and projects column extensions (latest_reached_phase,
-- phase_history) land in later migrations -- this file is the baseline.

-- Project registry.
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    current_phase INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK(status IN ('active','completed','archived','deleted')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Per-project phase state (12 phases P0..P11).
CREATE TABLE phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase_num INTEGER NOT NULL CHECK(phase_num BETWEEN 0 AND 11),
    phase_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','active','completed','skipped','invalidated')),
    artifact_version INTEGER NOT NULL DEFAULT 0,
    artifact_status TEXT DEFAULT NULL
        CHECK(artifact_status IN ('ok','damaged','missing') OR artifact_status IS NULL),
    artifact_path TEXT,
    preferences_confirmed_at TEXT,
    style_lock_path TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(project_id, phase_num)
);

-- Task ledger (FSM action record).
CREATE TABLE task_ledger (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN (
        'generate_artifact','regenerate_section','user_revision',
        'review','research','verify','cross_check','user_annotation'
    )),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
        'pending','queued','running','succeeded','failed','superseded','timeout'
    )),
    depends_on TEXT,
    produces_version INTEGER,
    target_version INTEGER,
    params TEXT NOT NULL DEFAULT '{}',
    result_ref TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Async task queue (consumed by worker; SPEC-B-003 Huey).
CREATE TABLE async_tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase INTEGER NOT NULL,
    ledger_task_id TEXT REFERENCES task_ledger(id),
    type TEXT NOT NULL,
    params TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','queued','running','succeeded','failed','cancelled')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
    worker_id TEXT,
    attempt INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Event log (WebSocket replay source).
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    type TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}'
);

-- Per-project preferences (three-layer markdown + brand kit + last candidates).
CREATE TABLE preferences (
    project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
    global_rules_md TEXT NOT NULL DEFAULT '',
    user_preferences_md TEXT NOT NULL DEFAULT '',
    project_preferences_md TEXT NOT NULL DEFAULT '',
    brand_kit_json TEXT,
    last_candidates_json TEXT,
    last_confirmed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- LLM call log (cost / token tracking).
CREATE TABLE agent_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    tokens INTEGER NOT NULL CHECK(tokens > 0),
    duration_ms INTEGER NOT NULL,
    phase INTEGER,
    project_id TEXT REFERENCES projects(project_id),
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Pre-flight system status snapshot.
CREATE TABLE system_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ok','degraded','failed')),
    message TEXT,
    checked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    valid_until TEXT NOT NULL
);

-- Financial data cache (dedup external fetches).
CREATE TABLE financial_data_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    granularity TEXT NOT NULL,
    date_range_start TEXT NOT NULL,
    date_range_end TEXT NOT NULL,
    data_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    expires_at TEXT NOT NULL,
    UNIQUE(symbol, granularity, date_range_start, date_range_end)
);

-- Preference version history.
CREATE TABLE preference_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    snapshot_content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
