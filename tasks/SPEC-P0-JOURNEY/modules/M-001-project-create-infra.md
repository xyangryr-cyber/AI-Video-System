# SPEC-M-001: Project Creation Infrastructure (API + DB + task_ledger Init)

## Metadata

```yaml
spec_id: SPEC-M-001
delivery_kind: module
parent_journey: SPEC-J-001
evidence_type: consumer_driven
status: PENDING
allowed_files:
  - "src/backend/api/routes/projects.py"
  - "src/backend/models/project.py"
  - "src/backend/models/phase.py"
  - "src/shared/schemas/project.py"
  - "config/phase_templates.json"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

项目创建是 Phase 0 的入口。`POST /projects` 接收标题+描述，初始化 `projects`/`phases`/`task_ledger` 三张表，并触发 RequirementsAgent 生成首版需求。task_ledger 按 `phase_templates.json` 初始化 Phase 0 的两个初始任务（generate_artifact + review）。此模块是整个流水线的起点——没有它，后续所有阶段都无法启动。

## Consumer / Evidence

### evidence_type: consumer_driven

| Field | Value |
|---|---|
| Concrete consumer | SPEC-M-004 (NewProject page 调用 POST /projects) 和 SPEC-M-005 (WorkflowPage 读取 GET /projects/{id}/state) |
| Verification command | `pytest tests/integration/test_project_create.py -v` |
| Non-placeholder check | `python scripts/assert_artifact.py --phase 0 --check db:projects,phases,task_ledger` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `POST /projects` | `{title: str, description: str}` | `ProjectState` (含 project_id, phase_status, task_ledger) | 422 (校验失败), 503 (LLM 不可用) | `curl -X POST /projects -d '{"title":"新能源","description":"分析2024年新能源市场"}'` |
| `GET /projects/{id}/state` | `project_id: str` | `ProjectState` (完整状态快照) | 404 | `curl /projects/proj_20260430_001/state` |
| `GET /health/llm` | — | `{status: "ok"\|"degraded"}` | — | pre-flight 检查 |

## Data Constraints

| target | rules |
|---|---|
| `projects` 表 | `id` 格式 `proj_YYYYMMDD_NNN`；`status` 初始 `active`；`current_phase` 初始 `0` |
| `phases` 表 | 12 行（phase_0..11）全部在项目创建时初始化；phase_0.status = `active`，其余 `pending` |
| `task_ledger` 表 | Phase 0 初始 2 行：generate_artifact(depends_on=[]) + review(depends_on=[generate_artifact])；status 初始 `pending` |
| 输入校验 | title 非空；description ≥ 10 字；校验失败返回 422，不发 API 请求 |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| LLM API 不可用 | pre-flight 连续 3 次失败或返回 degraded | 前端红色 Banner "AI 服务暂不可用"；新建项目按钮禁用；返回 503 |
| SQLite 写失败 | `SQLITE_READONLY` 或 `SQLITE_CORRUPT` | 前端黄色 Banner "系统存储异常"；不阻止浏览已有数据 |
| description < 10 字 | 前端校验 | 阻止提交，显示"描述不能少于 10 个字"，不发 API 请求 |
| 服务重启后恢复 | API 重启，内存状态丢失 | SQLite 是唯一可信状态源；GET /projects/{id}/state 从 DB 恢复完整状态 |

## Verification Commands

- `pytest tests/integration/test_project_create.py::test_create_project_success -v`
- `pytest tests/integration/test_project_create.py::test_create_project_validation_failure -v`
- `pytest tests/integration/test_project_create.py::test_task_ledger_initialized -v`
- `sqlite3 data/db/test.sqlite3 "SELECT COUNT(*) FROM task_ledger WHERE project_id='proj_test' AND phase=0"` → 返回 2

## Definition of Done

- [ ] Verification commands above all pass
- [ ] NewProject page 可成功创建项目并跳转到详情页
- [ ] task_ledger 初始化后包含 generate_artifact 和 review 两个任务
- [ ] pre-flight 检查在 LLM 不可用时正确阻止项目创建
- [ ] Parent journey SPEC-J-001 的 playwright test 通过
