# WebSocket Contracts: Phase 0

**Date**: 2026-05-02
**Source**: SPEC-A-11A (17 event types) + TECH_PLAN_v3.3 §3.4 + SPEC-A-1A endpoint #25

## Connection

```
WS /ws/{project_id}
```

- Protocol: WebSocket (RFC 6455)
- Auth: None (V1 single-user)
- Reconnection: Client must implement exponential backoff (1s, 2s, 4s, max 30s)
- Heartbeat: Server sends `ping` every 30s, client must respond with `pong`

## Event Envelope

All events follow this envelope:

```json
{
  "event": "<event_type>",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:01.000Z",
  "payload": {}
}
```

## Phase 0 Event Types

### 1. task.created

Emitted when a new task is added to the task ledger.

```json
{
  "event": "task.created",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:01.000Z",
  "payload": {
    "task_id": "task_uuid_001",
    "type": "generate_artifact",
    "status": "pending",
    "depends_on": []
  }
}
```

**Frontend behavior**: Add task to task list. If task list is collapsed, show new task as the current task (FR-020).

---

### 2. task.started

Emitted when a task transitions from `pending`/`queued` to `running`.

```json
{
  "event": "task.started",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:02.000Z",
  "payload": {
    "task_id": "task_uuid_001",
    "type": "generate_artifact",
    "status": "running"
  }
}
```

**Frontend behavior**: Update task status to running. Show spinner/loading indicator on the current task in collapsed view.

---

### 3. task.completed

Emitted when a task transitions to `succeeded`.

```json
{
  "event": "task.completed",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:15.000Z",
  "payload": {
    "task_id": "task_uuid_001",
    "type": "generate_artifact",
    "status": "succeeded",
    "result_ref": "data/projects/proj_20260502_001/requirements.json",
    "duration_ms": 13200,
    "tokens": {"input": 800, "output": 500},
    "cost_usd": 0.002
  }
}
```

**Frontend behavior**: Update task status to succeeded (green checkmark). If this was `generate_artifact`, fetch and display the updated requirements artifact. The next task (review) should appear as the current task.

---

### 4. task.failed

Emitted when a task transitions to `failed`.

```json
{
  "event": "task.failed",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:30.000Z",
  "payload": {
    "task_id": "task_uuid_001",
    "type": "generate_artifact",
    "status": "failed",
    "error_message": "LLM API 调用失败：连接超时",
    "retry_count": 3,
    "can_retry": true
  }
}
```

**Frontend behavior**: Show red error badge on task. Display error message. If `can_retry: true`, show retry button. If all retries exhausted (`retry_count >= 3`), show manual retry option.

---

### 5. task.superseded

Emitted when a task is marked `superseded` (e.g., old review superseded by new artifact version).

```json
{
  "event": "task.superseded",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:02:00.000Z",
  "payload": {
    "task_id": "task_uuid_002",
    "type": "review",
    "status": "superseded",
    "superseded_by": "task_uuid_004",
    "reason": "new_artifact_version"
  }
}
```

**Frontend behavior**: Show task as greyed out / strikethrough with "已覆盖" label (FR-020).

---

### 6. artifact.updated

Emitted when the Phase 0 artifact (`requirements.json`) is created or updated.

```json
{
  "event": "artifact.updated",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:15.000Z",
  "payload": {
    "artifact_version": 2,
    "artifact_path": "data/projects/proj_20260502_001/requirements.json",
    "trigger": "user_revision"
  }
}
```

**Frontend behavior**: Fetch updated artifact from `GET /projects/{id}/phases/0/artifact` and re-render `P0RequirementsView`. If `trigger` is `user_revision`, scroll to updated fields.

---

### 7. review.completed

Emitted when the CompletenessReviewer finishes its audit.

```json
{
  "event": "review.completed",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:20.000Z",
  "payload": {
    "task_id": "task_uuid_002",
    "verdict": "PASS",
    "notes": "所有字段验证通过，需求定义完整。",
    "artifact_version": 1
  }
}
```

```json
// verdict: FAIL
{
  "event": "review.completed",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:20.000Z",
  "payload": {
    "task_id": "task_uuid_002",
    "verdict": "FAIL",
    "notes": "存在以下问题需要处理",
    "blocking_issues": [
      "topic 字段为空",
      "缺少可识别的观点"
    ],
    "artifact_version": 1
  }
}
```

**Frontend behavior**:
- If PASS: Show green "审核通过" badge. Advance button becomes enabled (if other gates pass).
- If FAIL: Show red "审核未通过" badge with `blocking_issues` listed. Advance button shows reason.

---

### 8. phase.completed

Emitted when Phase 0 is marked complete (after successful advance).

```json
{
  "event": "phase.completed",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:05:00.000Z",
  "payload": {
    "completed_at": "2026-05-02T10:05:00Z",
    "next_phase": 1,
    "artifact_version": 2
  }
}
```

**Frontend behavior**: Update phase indicator to green checkmark. Disable Phase 0 chat/editing (read-only). Activate Phase 1 navigation.

---

### 9. agent.activity

Emitted for real-time agent activity transparency (TECH_PLAN_v3.3 §7).

```json
{
  "event": "agent.activity",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:02.000Z",
  "payload": {
    "agent_name": "RequirementsAgent",
    "action": "analyzing_description",
    "message": "正在分析您的视频需求描述...",
    "progress": null
  }
}
```

**Agent activity messages for Phase 0**:

| agent_name | action | message |
|------------|--------|---------|
| RequirementsAgent | analyzing_description | 正在分析您的视频需求描述... |
| RequirementsAgent | extracting_topic | 正在提取视频主题和观点... |
| RequirementsAgent | matching_platform | 正在匹配目标平台规格... |
| RequirementsAgent | classifying_category | 正在匹配内容分类... |
| RequirementsAgent | calculating_word_count | 正在计算推荐字数范围... |
| RequirementsAgent | finalizing | 正在生成结构化需求... |
| CompletenessReviewer | auditing | 正在审核需求完整性... |
| CompletenessReviewer | done | 审核完成 |

**Frontend behavior**: Display in Agent Activity Panel as a live log stream. Each message appears with a timestamp and agent name badge.

---

### 10. error.occurred

Emitted for non-task errors (system-level issues).

```json
{
  "event": "error.occurred",
  "project_id": "proj_20260502_001",
  "phase": 0,
  "timestamp": "2026-05-02T10:00:30.000Z",
  "payload": {
    "error_code": "LLM_TIMEOUT",
    "severity": "warning",
    "message": "AI 服务响应超时，正在自动重试...",
    "can_recover": true
  }
}
```

**Error severity levels** (TECH_PLAN_v3.3 §12):
- 🟡 `info`: Auto-recovering, no user action needed
- 🟠 `warning`: Degraded but functional; user may need to take action
- 🔴 `error`: Blocking; user must retry or choose alternative path

---

## Client Implementation Contract

### Connection Lifecycle

```
1. Connect: new WebSocket(`ws://host:8000/ws/${projectId}`)
2. On open: fetch initial state via REST (GET /projects/{id}/state, GET /projects/{id}/tasks)
3. On message: route by event type → update UI
4. On close: attempt reconnect with backoff (1s, 2s, 4s, 8s, 16s, 30s max)
5. On reconnect: re-fetch state via REST to catch missed events
```

### Frontend Event Handler Map

| Event | Handler |
|-------|---------|
| `task.created` | Add task to list; if collapsed, show as current |
| `task.started` | Update task status → running; show spinner |
| `task.completed` | Update task → succeeded; fetch artifact if generate_artifact |
| `task.failed` | Update task → failed; show error + retry button |
| `task.superseded` | Grey out task with "已覆盖" |
| `artifact.updated` | Fetch & re-render P0RequirementsView |
| `review.completed` | Update review badge; update advance button state |
| `phase.completed` | Update navigation; disable Phase 0 editing |
| `agent.activity` | Append to Agent Activity Panel |
| `error.occurred` | Show toast/banner based on severity |

### Fallback: REST Polling

When WebSocket is disconnected and reconnecting, poll at 3s intervals:
- `GET /projects/{id}/state` (check phase status)
- `GET /projects/{id}/tasks?phase=0` (check task statuses)

Stop polling when WebSocket reconnects.
