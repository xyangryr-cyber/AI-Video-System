# [SPEC-B-001] Docker Compose 三服务拓扑搭建

## Metadata
- **task_id**: SPEC-B-001
- **spec_ref**: SPEC-1.1
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL, SPEC-1A API 路由表)
- **priority**: P0
- **estimated_complexity**: M

## Scope
创建 `docker-compose.yml`，定义 `web`(Next.js)、`api`(FastAPI)、`worker`(Python) 三个服务。共用 `./data/{config,users,projects,logs,db}` Volume。敏感配置通过 `.env` + `env_file:` 注入 api/worker。包含 `.env.example` 模板和 `.gitignore` 配置。

## Allowed Files
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `src/backend/Dockerfile`
- `src/frontend/Dockerfile`
- `scripts/init-data-dirs.sh`

## Forbidden Files
- `src/frontend/src/**` (owned by SPEC-E)
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `docker compose up -d` 后三个服务状态为 Running
- [ ] AC-2: 前端 `http://localhost:3000` 返回 200 OK
- [ ] AC-3: `.env` 在 `.gitignore` 中，不被 git 追踪
- [ ] AC-4: `.env` 文件权限为 600（`scripts/init-data-dirs.sh` 中设置）
- [ ] AC-5: 容器内 `env | grep _API_KEY` 可见注入值
- [ ] AC-6: `ls data/db/app.sqlite3` 存在（Volume 挂载正确）
- [ ] AC-7: `./data/{config,users,projects,logs,db}` 目录结构完整

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_001.py -v
docker compose config --quiet
docker compose up -d
docker compose ps
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
docker compose exec api env | grep _API_KEY
ls data/db/app.sqlite3
stat -c "%a" .env  # 应输出 600
```

## Completion Definition
三服务可通过单命令 `docker compose up -d` 启动，Volume 挂载正确，环境变量注入正常，前端可访问。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_001.py | test_three_services_running |
| AC-2 | tests/unit/infra/test_spec_b_001.py | test_frontend_accessible |
| AC-3 | tests/unit/infra/test_spec_b_001.py | test_env_in_gitignore |
| AC-4 | tests/unit/infra/test_spec_b_001.py | test_env_file_permission_600 |
| AC-6 | tests/unit/infra/test_spec_b_001.py | test_sqlite_db_exists |
