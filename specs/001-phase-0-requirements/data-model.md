# Data Model: Phase 0 - Requirements Definition

**Date**: 2026-05-02
**Source**: [spec.md](./spec.md) Key Entities + TECH_PLAN_v3.3 + SPEC-A-1B DDL

## Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    projects      │──1:N──│     phases        │──1:N──│   task_ledger    │
│                  │       │  (phase_num=0)    │       │  (phase=0 tasks) │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         │                    ┌─────▼─────┐              ┌─────▼─────┐
         └──1:N──┤ agent_call_log │              │   events   │
                    └─────────────┘              └───────────┘

File System:
data/projects/{project_id}/
├── requirements.json     # Phase 0 artifact (Requirements schema)
└── dialogue/
    └── phase_0.md        # Phase 0 dialogue history
```

## Entity Definitions

### 1. Project

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | TEXT (PK) | format: `proj_YYYYMMDD_NNN` | Unique project identifier |
| `title` | TEXT | NOT NULL, non-empty | Project title from user input |
| `description` | TEXT | NOT NULL, >= 10 chars | Natural language description |
| `current_phase` | INTEGER | NOT NULL, DEFAULT 0 | Current active phase (0-11) |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | Project lifecycle status |
| `latest_reached_phase` | INTEGER | NOT NULL, DEFAULT 0 | Furthest phase reached |
| `phase_history` | TEXT (JSON) | NOT NULL, DEFAULT '[]' | Ordered list of completed phases |
| `created_at` | TEXT | ISO 8601 timestamp | Creation time |
| `updated_at` | TEXT | ISO 8601 timestamp | Last modification time |

**State transitions**:
```
active ──→ completed ──→ archived
  │
  └──→ failed
```

**Phase 0 lifecycle**: Project is created with `current_phase=0`. After advancing past Phase 0, `current_phase` becomes 1 and `latest_reached_phase` is updated.

### 2. Phase (phase_num=0)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | TEXT (FK) | REFERENCES projects(id) | Parent project |
| `phase_num` | INTEGER | 0 | Phase number |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | Phase status |
| `artifact_version` | INTEGER | DEFAULT 0 | Current artifact version number |
| `artifact_path` | TEXT | nullable | Path to requirements.json |

**Phase status values**: `active`, `completed`, `skipped`

**Phase 0 state transitions**:
```
active ──→ completed (after Gate 0 PASS + advance)
```

### 3. Task (task_ledger, phase=0)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (PK) | UUID | Task unique identifier |
| `project_id` | TEXT (FK) | REFERENCES projects(id) | Parent project |
| `phase` | INTEGER | 0 | Phase this task belongs to |
| `type` | TEXT | NOT NULL | Task type (see below) |
| `status` | TEXT | NOT NULL | Task status (see below) |
| `depends_on` | TEXT (JSON) | nullable | JSON array of prerequisite task IDs |
| `params` | TEXT (JSON) | nullable | Task-specific parameters |
| `result_ref` | TEXT | nullable | Reference to task output |
| `error_message` | TEXT | nullable | Error details if failed |
| `created_at` | TEXT | ISO 8601 | Creation timestamp |
| `updated_at` | TEXT | ISO 8601 | Last update timestamp |

**Phase 0 task types**: `generate_artifact`, `review`, `user_revision`

**Task status values**: `pending`, `queued`, `running`, `succeeded`, `failed`, `skipped`, `superseded`

**Terminal states**: `succeeded`, `failed`, `skipped`, `superseded`

**Phase 0 task lifecycle**:
```
1. generate_artifact (RequirementsAgent)
   pending → queued → running → succeeded/failed
                              ↓ (superseded if user triggers regenerate)
   
2. review (CompletenessReviewer)
   depends_on: generate_artifact
   pending → queued → running → succeeded/failed
                              ↓ (superseded if new artifact version created)

3. user_revision (triggered by chat revise)
   depends_on: none
   pending → queued → running → succeeded/failed
   
   On success: 
   - artifact_version++ 
   - supersedes previous review task
   - auto-creates new review task
```

### 4. Requirements Artifact (requirements.json)

Canonical schema from `src/shared/schemas/artifacts.py`:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | string | non-empty | Parent project ID |
| `title` | string | non-empty | Video title |
| `topic` | string | >= 5 chars | Extracted video topic |
| `target_duration` | object | `{min_sec, max_sec}` | Target duration range in seconds |
| `target_word_count` | object | `{min, max}`, min > 0, max >= min, max <= 100000 | Target word count range |
| `platform` | PlatformEntry[] | non-empty array | Target platform(s) with specs |
| `category` | object | `{level1, level2}` | Content category classification |
| `clarification_needed` | array | nullable | Questions needing user input |
| `created_at` | string | ISO 8601 | Artifact creation timestamp |
| `version` | integer | >= 1 | Artifact version number |

**PlatformEntry schema**:
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Platform name (e.g., "bilibili") |
| `resolution` | string | Video resolution (e.g., "1920x1080") |
| `bitrate` | string | Video bitrate (e.g., "6M") |
| `format` | string | Video format (e.g., "mp4") |
| `aspect_ratio` | string | Aspect ratio (e.g., "16:9") |

**Validation rules** (from CompletenessReviewer, FR-014):
1. `topic` non-empty (>= 5 chars)
2. `description` non-empty with at least one identifiable viewpoint
3. `target_duration.min_sec >= 0`, `target_duration.max_sec >= target_duration.min_sec`
4. `target_word_count` consistent with duration (within +/-10% of duration × 240 chars/min)
5. `platform` entries exist in `config/platform_profiles.json`
6. `category.level1` and `category.level2` exist in `config/categories.json`
7. `clarification_needed` values are valid dimension keys

### 5. Review Verdict

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | Literal | `PASS` or `FAIL` |
| `notes` | string | Human-readable review summary |
| `blocking_issues` | string[] | List of blocking issue descriptions |
| `artifact_version` | integer | Version of artifact reviewed |
| `reviewed_at` | string | ISO 8601 review timestamp |

**Review lifecycle**:
```
RequirementsAgent completes
  → auto-create review task
  → CompletenessReviewer runs
  → verdict: PASS → advance button enabled (if other gates pass)
  → verdict: FAIL → advance button disabled, blocking_issues shown
  
User revise/regenerate
  → old review superseded
  → new artifact version created
  → new review auto-triggered
```

### 6. Dialogue History

Stored as `data/projects/{project_id}/dialogue/phase_0.md`. Format:

```markdown
# Phase 0 Dialogue — proj_20260502_001

## Turn 1 — 2026-05-02T10:00:00Z
**User**: 做一个关于黄金投资的5分钟分析视频
**Agent**: [RequirementsAgent output card]

## Turn 2 — 2026-05-02T10:01:00Z
**User**: 改成8-12分钟
**Agent**: [Updated requirements card]

...
```

Each turn records: timestamp, user message, agent response (or artifact reference).

### 7. Agent Call Log

| Field | Type | Description |
|-------|------|-------------|
| `id` | TEXT (PK) | UUID |
| `project_id` | TEXT (FK) | Parent project |
| `agent_name` | TEXT | e.g., "RequirementsAgent", "CompletenessReviewer" |
| `model` | TEXT | LLM model used |
| `tokens_input` | INTEGER | Prompt token count |
| `tokens_output` | INTEGER | Completion token count |
| `duration_ms` | INTEGER | Call duration in milliseconds |
| `cost_usd` | REAL | Estimated cost in USD |
| `status` | TEXT | `success` or `error` |
| `created_at` | TEXT | ISO 8601 timestamp |

Used for cost aggregation (per project/phase) and LLM call auditing.

## Data Flow: Phase 0 Lifecycle

```
1. CREATE PROJECT
   POST /projects {title, description}
   → INSERT projects (current_phase=0, status=active)
   → INSERT phases (phase_num=0..11, phase_0.status=active)
   → Background: RequirementsAgent.produce()
     → INSERT task_ledger (type=generate_artifact, status=pending)
     → task status: pending → running → succeeded
     → WRITE data/projects/{id}/requirements.json
     → INSERT agent_call_log
     → EMIT events: task.created, task.started, task.completed
   
2. AUTO-REVIEW
   After generate_artifact succeeds:
   → INSERT task_ledger (type=review, depends_on=generate_artifact)
   → CompletenessReviewer.audit(requirements.json)
   → task status: pending → running → succeeded
   → Review verdict (PASS/FAIL) in task result_ref
   → EMIT events: task.created, task.started, task.completed

3. USER REVISE
   POST /projects/{id}/chat {message: "改成8-12分钟"}
   → IntentRouter.classify() → revise
   → INSERT task_ledger (type=user_revision)
   → RequirementsAgent.produce(accumulated_context)
   → artifact_version++
   → WRITE data/projects/{id}/requirements.json (v2)
   → Old review task → superseded
   → New review task auto-created (step 2 repeats)

4. ADVANCE
   POST /projects/{id}/advance
   → GateKeeper.check(phase=0):
     ✓ requirements.json exists and valid
     ✓ Latest review verdict = PASS
     ✓ All tasks in terminal states
   → UPDATE phases SET status='completed' WHERE phase_num=0
   → UPDATE projects SET current_phase=1, latest_reached_phase=1
   → INSERT phase_history entry
   → EMIT event: phase.completed (phase=0)
   → Initialize Phase 1 tasks
```
