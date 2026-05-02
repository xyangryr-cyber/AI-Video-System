# [SPEC-GAPFIX-034] main.tsx 启动 MSW worker

## Metadata
- **task_id**: SPEC-GAPFIX-034
- **spec_ref**: 第四轮扫描报告 发现 1.1
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
在 `src/frontend/main.tsx` 中添加 dev 模式下条件启动 MSW worker 的逻辑。当前 `mocks/browser.ts` 已 export `worker = setupWorker(...handlers)`, `mocks/handlers.ts` 已定义 5 个 API handler, 但 `main.tsx` 从未 import 或启动 worker。这导致开发模式下裸 `fetch()` 直接请求后端, 页面白屏。

修复: 添加 `async function bootstrap()` 在 `import.meta.env.DEV` 时动态 import worker 并 `worker.start({ onUnhandledRequest: "bypass" })`, 然后渲染 App。

## Allowed Files
- `src/frontend/main.tsx`

## Forbidden Files
- `src/backend/**`
- `src/frontend/mocks/**` (handler 已正确, 不需要改)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `import.meta.env.DEV` 时, `main.tsx` 动态 import `./mocks/browser` 并调用 `worker.start()`
- [ ] AC-2: `import.meta.env.PROD` 时, 不加载 mocks, 直接渲染 App
- [ ] AC-3: `worker.start()` 传入 `{ onUnhandledRequest: "bypass" }` 避免未 mock 请求报错
- [ ] AC-4: `pnpm --filter frontend test` 全部通过
- [ ] AC-5: 现有 49 个单元测试不受影响 (测试通过各自的 `beforeAll` 启动 MSW server)

## Verification Commands
```bash
# 验证 import 存在
grep -n "mocks/browser" src/frontend/main.tsx
# 验证 bootstrap 逻辑
grep -n "bootstrap\|worker.start\|import.meta.env.DEV" src/frontend/main.tsx
# 单元测试全量
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -10
```

## Completion Definition
`main.tsx` 在 DEV 模式下启动 MSW worker, PROD 模式下跳过。vitest 全量通过。应用在 `npm run dev` 时通过 MSW 拦截 API 调用。

## Note
TDD 流程: 先写测试验证 `main.tsx` 在 dev 模式下的行为 (mock `import.meta.env.DEV`), 确认测试失败后再实现。
