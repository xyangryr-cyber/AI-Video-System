# REST API Contracts: Phase 0

**Date**: 2026-05-02
**Source**: SPEC-A-1A (25 endpoints) + TECH_PLAN_v3.3 §3 + Phase 0 spec FR-001 to FR-030

## Phase 0 Endpoints

### 1. Create Project

```
POST /api/projects
```

**Request**:
```json
{
  "title": "黄金价格走势分析",
  "description": "做一个关于近期黄金价格走势的分析视频，从技术面和基本面两个角度解读，适合投资新手观看"
}
```

**Validation** (FR-001, FR-002):
- `title`: non-empty string
- `description`: string, >= 10 characters

**Response** (201 Created):
```json
{
  "project_id": "proj_20260502_001",
  "title": "黄金价格走势分析",
  "description": "做一个关于近期黄金价格走势的分析视频，从技术面和基本面两个角度解读，适合投资新手观看",
  "current_phase": 0,
  "status": "active",
  "latest_reached_phase": 0,
  "phase_history": [],
  "created_at": "2026-05-02T10:00:00Z",
  "updated_at": "2026-05-02T10:00:00Z"
}
```

**Error Responses**:
```json
// 400 Bad Request — validation failure
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "标题不能为空",
    "details": {"field": "title", "constraint": "non_empty"}
  }
}

// 400 Bad Request — description too short
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "描述不能少于 10 个字",
    "details": {"field": "description", "constraint": "min_length", "min": 10, "actual": 5}
  }
}
```

**Backend behavior** (FR-003, FR-004, FR-005):
1. Generate `project_id` in format `proj_YYYYMMDD_NNN`
2. INSERT into `projects` table (current_phase=0, status='active')
3. INSERT 12 rows into `phases` table (phase_0 status='active', others status='pending')
4. Background task: invoke RequirementsAgent → generate `requirements.json`
5. Return created project

---

### 2. Get Project State

```
GET /api/projects/{project_id}/state
```

**Response** (200 OK):
```json
{
  "project": {
    "project_id": "proj_20260502_001",
    "title": "黄金价格走势分析",
    "description": "做一个关于近期黄金价格走势的分析视频...",
    "current_phase": 0,
    "status": "active",
    "latest_reached_phase": 0,
    "phase_history": [],
    "created_at": "2026-05-02T10:00:00Z",
    "updated_at": "2026-05-02T10:00:05Z"
  },
  "phases": [
    {
      "phase_num": 0,
      "status": "active",
      "artifact_version": 1,
      "artifact_path": "data/projects/proj_20260502_001/requirements.json"
    }
  ],
  "system_status": {
    "llm_available": true,
    "tts_available": true,
    "degraded_services": []
  }
}
```

**Error Responses**:
```json
// 404 Not Found
{
  "error": {
    "code": "NOT_FOUND",
    "message": "项目不存在",
    "details": {"project_id": "proj_nonexistent"}
  }
}
```

---

### 3. Get Phase Artifact

```
GET /api/projects/{project_id}/phases/0/artifact
```

**Response** (200 OK):
```json
{
  "project_id": "proj_20260502_001",
  "title": "黄金价格走势分析",
  "topic": "近期黄金价格技术面与基本面分析",
  "target_duration": {
    "min_sec": 480,
    "max_sec": 720
  },
  "target_word_count": {
    "min": 1920,
    "max": 2880
  },
  "platform": [
    {
      "name": "bilibili",
      "resolution": "1920x1080",
      "bitrate": "6M",
      "format": "mp4",
      "aspect_ratio": "16:9"
    }
  ],
  "category": {
    "level1": "财经",
    "level2": "贵金属投资"
  },
  "clarification_needed": [
    {
      "dimension": "target_platform",
      "question": "你希望发布到哪个平台？",
      "options": ["bilibili", "douyin", "youtube"]
    }
  ],
  "created_at": "2026-05-02T10:00:15Z",
  "version": 1
}
```

**Error Responses**:
```json
// 404 Not Found — artifact not yet generated
{
  "error": {
    "code": "NOT_FOUND",
    "message": "产物尚未生成",
    "details": {"phase": 0, "project_id": "proj_20260502_001"}
  }
}

// 404 Not Found — phase invalid
{
  "error": {
    "code": "INVALID_PHASE",
    "message": "无效的阶段编号",
    "details": {"phase": 99, "valid_range": [0, 11]}
  }
}
```

---

### 4. Chat / Send Message

```
POST /api/projects/{project_id}/chat
```

**Request**:
```json
{
  "message": "改成8-12分钟"
}
```

**Response** (200 OK):
```json
{
  "intent": "revise",
  "message": "已将时长更新为 8-12 分钟，其他字段保持不变。新的审核正在进行中...",
  "artifact_updated": true,
  "artifact_version": 2,
  "review_triggered": true
}
```

**Intent-specific responses**:

```json
// intent: regenerate
{
  "intent": "regenerate",
  "message": "已重新生成需求，旧版本已废弃。请查看新的分析结果。",
  "artifact_updated": true,
  "artifact_version": 3,
  "review_triggered": true
}

// intent: inject_subtask (FR-017 — placeholder)
{
  "intent": "inject_subtask",
  "message": "此功能暂未开放",
  "artifact_updated": false,
  "review_triggered": false
}

// intent: request_advance (FR-022)
{
  "intent": "request_advance",
  "message": "需求已确认。请点击右侧「确认进入下一阶段」按钮完成推进。",
  "artifact_updated": false,
  "review_triggered": false,
  "advance_ready": true
}

// intent: clarify (fallback — 2 consecutive)
{
  "intent": "clarify",
  "message": "抱歉，我不太确定您的意图。请选择以下操作：",
  "suggested_actions": [
    {"type": "revise", "label": "修改需求", "description": "调整特定字段，如时长、平台等"},
    {"type": "regenerate", "label": "重新生成", "description": "放弃当前结果，从零重新分析"},
    {"type": "request_advance", "label": "确认推进", "description": "确认当前需求无误，进入下一阶段"},
    {"type": "clarify", "label": "补充信息", "description": "回答AI的澄清问题"}
  ]
}
```

**Error Responses**:
```json
// 422 Unprocessable Entity — empty message
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "消息不能为空",
    "details": {"field": "message", "constraint": "non_empty"}
  }
}

// 503 Service Unavailable — LLM unavailable
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "AI 服务暂时不可用，请稍后重试",
    "details": {"service": "llm", "retry_after_seconds": 30}
  }
}
```

---

### 5. Get Task List

```
GET /api/projects/{project_id}/tasks?phase=0
```

**Response** (200 OK):
```json
{
  "tasks": [
    {
      "id": "task_uuid_001",
      "phase": 0,
      "type": "generate_artifact",
      "status": "succeeded",
      "depends_on": [],
      "created_at": "2026-05-02T10:00:01Z",
      "updated_at": "2026-05-02T10:00:15Z",
      "result_ref": "data/projects/proj_20260502_001/requirements.json",
      "error_message": null
    },
    {
      "id": "task_uuid_002",
      "phase": 0,
      "type": "review",
      "status": "running",
      "depends_on": ["task_uuid_001"],
      "created_at": "2026-05-02T10:00:15Z",
      "updated_at": "2026-05-02T10:00:16Z",
      "result_ref": null,
      "error_message": null
    }
  ],
  "current_task": {
    "id": "task_uuid_002",
    "type": "review",
    "status": "running"
  }
}
```

Note: `current_task` represents the currently executing task for FR-020 default-collapsed view.

---

### 6. Advance to Next Phase

```
POST /api/projects/{project_id}/advance
```

**Request**: (empty body)

**Response** (200 OK — Gate passed, advanced):
```json
{
  "success": true,
  "from_phase": 0,
  "to_phase": 1,
  "message": "已进入阶段 1：内容主线",
  "gate_checks": {
    "artifact_exists": {"passed": true},
    "review_passed": {"passed": true},
    "no_running_tasks": {"passed": true}
  }
}
```

**Response** (200 OK — Gate failed, NOT advanced):
```json
{
  "success": false,
  "current_phase": 0,
  "message": "尚不满足推进条件",
  "gate_checks": {
    "artifact_exists": {"passed": true},
    "review_passed": {"passed": false, "reason": "审核未通过", "blocking_issues": ["topic 字段为空", "缺少可识别的观点"]},
    "no_running_tasks": {"passed": true}
  },
  "blocking_reasons": [
    "审核未通过"
  ]
}
```

**Frontend contract** (FR-023, FR-024):
- Advance button enabled ONLY when all gate checks pass
- Disabled button shows specific blocking reasons
- States:
  - Review FAIL → "审核未通过" with `blocking_issues` listed
  - Tasks running → "仍有任务正在执行中，请等待完成"
  - No artifact → "需求产物尚未生成"

---

## Common Patterns

### Error Response Format

All errors follow SPEC-A-13A (17 error codes):

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "用户可读的错误描述",
    "details": {}
  }
}
```

**Phase 0 relevant error codes**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_PHASE` | 404 | Phase number out of range |
| `SERVICE_UNAVAILABLE` | 503 | External service (LLM) unavailable |
| `GATE_CHECK_FAILED` | 200* | Gate conditions not met (*non-200 not used for gate — advance returns 200 with success=false) |
| `TASK_RUNNING` | 409 | Cannot perform operation while tasks running |

### Pagination

Not applicable to Phase 0 endpoints (single-project scope, small result sets).

### Authentication

V1: No authentication (single-user private deployment). All endpoints are unauthenticated.

### Idempotency

- `POST /projects`: NOT idempotent (creates new project each call)
- `POST /projects/{id}/advance`: Idempotent from same phase (no-op if already advanced)
- `POST /projects/{id}/chat`: NOT idempotent (each call processes as new user message)
- All GET endpoints: Idempotent (read-only)
