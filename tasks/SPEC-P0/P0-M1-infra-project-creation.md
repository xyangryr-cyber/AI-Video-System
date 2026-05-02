# [SPEC-P0-M1] 基础设施与项目创建

## Metadata
- **task_id**: SPEC-P0-M1
- **spec_ref**: Phase0需求.md §2, §8, §14; TECH_PLAN_v3.3.md §4, §5
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: L

## Scope
创建系统配置文件、SQLite 数据库 Schema、健康检查端点、项目创建 API。用户提交标题和描述后，系统初始化项目、Phase 0 和 task_ledger。前端提供 `/projects/new` 页面含输入校验。本模块是所有后续模块的前置依赖。

**业务闭环**: 配置就绪 → 用户提交标题+描述 → 项目创建成功，Phase 0 启动，任务清单就绪。

## Allowed Files
- `config/platforms.json`
- `config/categories.json`
- `config/model_config.json`
- `config/phase_templates.json`
- `src/backend/models/project.py`
- `src/backend/models/phase.py`
- `src/backend/models/task_ledger.py`
- `src/backend/models/async_task.py`
- `src/backend/models/event.py`
- `src/backend/models/agent_call_log.py`
- `src/backend/models/preference.py`
- `src/backend/api/health.py`
- `src/backend/api/projects.py`
- `src/backend/services/project_service.py`
- `src/frontend/pages/projects/new.tsx`
- `tests/unit/test_project_creation.py`
- `tests/integration/test_api_projects.py`

## Forbidden Files
- `src/backend/agents/**`
- `src/backend/engine/**`
- `docs/specs/**`
- `docs/TECH_PLAN_v3.3.md`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `config/platforms.json` 包含 bilibili/douyin/wechat/youtube 四个平台及 specs（resolution/bitrate/format）
- [ ] AC-2: `config/categories.json` 包含金融财经/科技互联网/知识科普/社会热点 四个 level1 及其 level2 子类
- [ ] AC-3: `config/model_config.json` 包含 LLM 模型路由映射（intent_router_primary / reviewer / gatekeeper / producer / requirements_agent 等）+ speech_rate 默认 240
- [ ] AC-4: `config/phase_templates.json` 包含 phase_0 的 initial_tasks（generate_artifact + review）及 depends_on 关系
- [ ] AC-5: SQLite 建表：projects / phases / task_ledger / async_tasks / events / agent_call_log / preferences，所有字段类型和约束符合 §8.2 定义
- [ ] AC-6: `GET /health` 返回 200 + `{"status": "ok"}`；`GET /health/llm` 返回 `{"status": "ok"}` 或 `{"status": "degraded"}`
- [ ] AC-7: `POST /projects` 校验标题非空、描述 ≥10 字，失败时返回 422 + 错误信息
- [ ] AC-8: `POST /projects` 成功时：生成 `proj_YYYYMMDD_NNN` 格式 project_id → 写入 projects 表（status=active）→ 写入 phases 表（phase_0.status=active，其余 phase pending）→ 按 phase_templates.json 初始化 task_ledger（generate_artifact pending, review pending）→ 返回 project_id
- [ ] AC-9: 前端 `/projects/new` 页面渲染标题输入框 + 描述输入框（多行）+ 提交按钮；校验失败在前端阻止提交并显示错误文案
- [ ] AC-10: 前端提交成功后跳转到 `/projects/{project_id}`

## Verification Commands
```bash
# Config file schema validation
python -c "import json; json.load(open('config/platforms.json')); json.load(open('config/categories.json')); json.load(open('config/model_config.json')); json.load(open('config/phase_templates.json')); print('All configs valid JSON')"

# DB schema creation
python -c "from src.backend.models import *; print('All models importable')"

# Unit tests
pytest tests/unit/test_project_creation.py -v

# Integration tests
pytest tests/integration/test_api_projects.py -v

# Type check
mypy src/backend/models/ --strict
mypy src/backend/api/projects.py --strict
```

## Completion Definition
4 个配置文件存在且为合法 JSON。7 张 SQLite 表创建成功。`GET /health` 和 `GET /health/llm` 可用。`POST /projects` 通过校验创建项目并初始化 Phase 0 + task_ledger。前端 `/projects/new` 页面可提交并跳转。所有测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-7 | 场景 6.1 — 输入校验 | 6.1 标题为空/描述不足10字被阻止 |
| AC-8 | 场景 1.2 — 提交完整信息 | 1.2a 跳转到 /projects/{id} |
| AC-8 | 场景 1.2 — 提交完整信息 | 1.2b Phase 0 高亮 |
| AC-8 | 场景 1.2 — 提交完整信息 | 1.2e 任务清单显示两个任务 |
| AC-9 | 场景 1.1 — 进入创建页 | 1.1a-c 页面元素完整 |
| AC-6 | Pre-flight 检查 | LLM/API/SQLite 健康状态 |
