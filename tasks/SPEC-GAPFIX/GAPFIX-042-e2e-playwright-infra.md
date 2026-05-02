# [SPEC-GAPFIX-042] E2E Playwright 基础设施

## Metadata
- **task_id**: SPEC-GAPFIX-042
- **spec_ref**: 第四轮扫描报告 发现 4.1; SPEC-B-018
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M

## Scope
`tests/e2e/test_e2e_placeholder.py` 中只有 `pytest.skip("NOT IMPLEMENTED")`。非占位符 E2E 测试 = 0。

修复:
1. 安装 Playwright 依赖: `pnpm --filter frontend add -D @playwright/test`
2. 创建 `src/frontend/playwright.config.ts`
3. 创建 `tests/e2e/test_app_loads.py` — 验证首页加载非白屏
4. 创建 `tests/e2e/test_api_integration.py` — 验证前后端连通
5. 更新 `nightly_e2e.yml` 中的 playwright 命令指向正确配置

## Allowed Files
- `tests/e2e/` (新建测试)
- `src/frontend/playwright.config.ts` (新建)
- `src/frontend/package.json` (添加 @playwright/test)
- `pnpm-lock.yaml` (依赖锁)

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `@playwright/test` 已安装 (检查 package.json)
- [ ] AC-2: `playwright.config.ts` 配置: baseURL=http://localhost:3000, webServer 自动启动
- [ ] AC-3: `tests/e2e/test_app_loads.py` 验证首页加载, 页面含文字内容 (非空白)
- [ ] AC-4: `tests/e2e/test_api_integration.py` 验证前端能通过 proxy 调后端 /api
- [ ] AC-5: `npx playwright test --grep @e2e-real` 可运行 (需要 docker compose up 环境)

## Verification Commands
```bash
# 检查依赖
grep "@playwright/test" src/frontend/package.json
# 检查配置
cat src/frontend/playwright.config.ts | head -20
# 检查测试文件
ls -la tests/e2e/test_app_loads.py tests/e2e/test_api_integration.py 2>/dev/null
# 前端测试
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
Playwright 基础设施就位, 至少 2 个 E2E 测试文件 (非占位符)。vitest 全部通过。

## Note
Per HARNESS §4.3, infra/config changes are TDD-exempt。E2E 测试本身不需要 TDD (它们是验证层), 但测试代码需要语法正确。
