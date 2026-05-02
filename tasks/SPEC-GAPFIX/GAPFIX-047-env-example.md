# [SPEC-GAPFIX-047] .env.example 完善

## Metadata
- **task_id**: SPEC-GAPFIX-047
- **spec_ref**: 第四轮扫描报告 发现 5.2
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S

## Scope
`.env.example` 已存在但缺少以下关键配置说明:
- `VITE_API_TARGET` (GAPFIX-035 引入的新变量)
- `CORS_ORIGINS` (GAPFIX-039 引入的新变量)
- `DATABASE_URL` (`docker-compose.dev.yml` 使用, 与 `.env.example` 中的 `DB_URL` 不一致)
- Docker 环境下的推荐值

修复:
1. 添加 `VITE_API_TARGET=http://localhost:8000` 及 Docker 环境推荐值注释
2. 添加 `CORS_ORIGINS=http://localhost:3000` 及多 origin 示例
3. 统一 `DATABASE_URL` 和 `DB_URL` — 保留 `DATABASE_URL` (docker-compose 使用), 标注 `DB_URL` 为别名

## Allowed Files
- `.env.example`

## Forbidden Files
- `.env` (secrets, never modify)
- `src/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `.env.example` 含 `VITE_API_TARGET` 变量及注释
- [ ] AC-2: `.env.example` 含 `CORS_ORIGINS` 变量及注释
- [ ] AC-3: `DATABASE_URL` 和 `DB_URL` 关系明确 (标注别名)
- [ ] AC-4: Docker 环境下推荐值有注释说明
- [ ] AC-5: 文件语法正确 (bash source 不会报错)

## Verification Commands
```bash
# 验证变量存在
grep -n "VITE_API_TARGET\|CORS_ORIGINS\|DATABASE_URL\|DB_URL" .env.example
# 验证语法 (bash source)
bash -c 'set -a; source .env.example; set +a' 2>&1 || echo "WARNING: check syntax"
# 行数 (必须是纯配置, 不含 .env 实际值)
wc -l .env.example
```

## Completion Definition
`.env.example` 包含所有环境变量定义及 Docker 环境推荐值。新开发者复制 `.env.example` 到 `.env` 后即可启动。

## Note
Per HARNESS §4.3, config file changes are TDD-exempt.
