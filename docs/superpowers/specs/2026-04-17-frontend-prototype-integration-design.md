# 前端原型集成开发流设计 (Frontend Prototype Integration Design)

- **日期**: 2026-04-17
- **作者**: 许阳 + Claude (brainstorming)
- **状态**: Draft → 待用户 review
- **关联**: SPEC-A / SPEC-B / SPEC-E / HARNESS.md / `tasks/SPEC-{B,E}/`
- **后续**: 通过后由 `superpowers:writing-plans` 拆 Wave 0 + v3.18 DELTA 执行计划

---

## 0. 背景与目标

### 0.1 现状
许阳已在 Google AI Studio 上完成 AI-Video-System 的交互式前端原型，已导出完整 React/TS 代码到 `/Users/xyangryr/Downloads/ai-video (1)/`（含 `src/`、`package.json`、`vite.config.ts`、`tsconfig.json` 等）。Wave 0 将其拷入项目内 `prototype/` 目录。该原型相对 SPEC-E 与 PRD v3.3 中的前端定义存在两类差异：
- **UI 层差异**：组件视觉/交互细节大量增补
- **契约层差异**：可能引入新字段、新事件类型，超出现有 SPEC-A 契约范围

项目当前的开发 flow 已固化：
- 6 SPEC（A 契约 → B 基础设施 → C 后端核心 → D 流水线 → E 前端 → F 媒体渲染）
- HARNESS.md 强制 TDD（RED → GREEN → REFACTOR → COMMIT），文件大小限制（Python 400 行 / TS 300 行），7 层依赖方向 + madge 圈检
- 21 张 SPEC-E 任务卡（E-001~E-015 + E-100~E-105），其中 11 张已带 `npx playwright test` 验证命令

### 0.2 目标（用户原话）
> "最终开发出来的前端遵循原型、可被开发测试 Loop 覆盖、可前后端联调"

三条硬约束：
1. **遵循原型**：原型是 UI 真值；最终前端在视觉与交互上必须与原型一致
2. **可被开发测试 Loop 覆盖**：所有变更走 RED-GREEN-REFACTOR-COMMIT，不绕过 TDD
3. **可前后端联调**：从 mock 联调到真实环境联调全链路打通，不能停留在"能跑组件测试"

### 0.3 联调现状缺口（直接回答许阳的问题）

**已有覆盖**：
- ✅ `tasks/SPEC-B/B-012-nonfunctional-and-test-strategy.md` AC-7 — `tests/integration/test_pipeline_e2e.py` 骨架（mock LLM）
- ✅ `tests/integration/test_workflow_e2e.py` 占位（全部 `pytest.skip("NOT IMPLEMENTED")`）
- ✅ 11 张 SPEC-E 任务卡（E-011/012/013/014, E-100~E-105）含 `npx playwright test ...` 验证命令

**关键缺口**：
- ❌ 前端没有 mock 层方案（无 MSW，无 fixture 单一来源）
- ❌ 没有真实联调环境（无 `make dev`、无 `docker-compose.dev.yml`、无种子数据脚本）
- ❌ 没有契约一致性测试（`src/frontend/types/` ↔ `src/shared/schemas/*.json` 漂移无防护）
- ❌ 现有 playwright 验证命令未声明运行目标（mock 后端 还是 真实后端？）
- ❌ 原型添加的字段/事件未反哺 SPEC-A，前端实现时会再次手工"对齐"，重复劳动

→ **本设计要补这 5 个缺口**。

---

## 1. 目录布局与隔离纪律

### 1.1 新增顶层目录
```
AI-Video-System/
├── prototype/                    # ★ 新增：原型源码隔离区
│   ├── README.md                 #   说明：只读真值，禁止 import 到 src/
│   ├── src/                      #   Google AI Studio 导出的原始 React/TS
│   ├── package.json              #   原型独立依赖
│   └── PROTOTYPE_INDEX.md        #   原型组件索引 + 与 SPEC-E 任务卡的映射
└── src/frontend/                 # 现有：生产前端，从 prototype 渐进迁移
```

### 1.2 隔离纪律
- `prototype/` 是**只读真值**，作为 UI/UX 行为对照基准
- **禁止 `src/frontend/**` 直接 import `prototype/**`**（HARNESS §1.2 风格的 forbidden path，写入 `.eslintrc` + madge 规则）
- 原型代码迁入生产路径时**必须重写**以满足：SPEC-A types、TDD、文件大小限制、HARNESS 命名规范
- 原型独立 `package.json`，依赖与生产前端解耦，避免污染主依赖树

### 1.3 CI 守卫
- madge 检查 `src/frontend/**` 不出现 `prototype/` 引用
- ESLint rule: `no-restricted-imports` 禁止 `from "prototype/..."`
- 失败即 PR-blocking

---

## 2. 原型审计与契约缺口反哺

### 2.1 PROTOTYPE_INDEX.md
位置：`prototype/PROTOTYPE_INDEX.md`

内容：
- 原型每个页面/组件 → 对应的 SPEC-E 任务卡（E-001 ~ E-105）
- 每个组件标注："纯 UI 增补" / "需新字段" / "需新事件" / "需新 endpoint"
- 标注差异级别：T1（视觉细节）/ T2（交互行为）/ T3（契约扩展）

### 2.2 SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md
位置：`docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md`

延续 v3.15 / v3.16-BDD / v3.17-AudioMaster 的修订节奏。内容：
- T3（契约扩展）项目逐条列出
- 每条对应 SPEC-A 章节（25 endpoints / 17 events / 17 error codes / 8 artifacts）
- 给出"是否引入新字段 / 新事件 / 新错误码 / 新 artifact"的决策建议
- 明确归类为：**采纳并回写 SPEC-A** / **改原型对齐 SPEC-A** / **暂缓**

### 2.3 三类差异处理流程
- **T1 视觉细节**：直接成为对应 SPEC-E 卡的新增 AC（"组件视觉与原型一致"），不改契约
- **T2 交互行为**：评估是否影响事件流；若影响，转 T3
- **T3 契约扩展**：写入 v3.18 DELTA → 经 review 后回写 SPEC-A → 触发 SPEC-A 任务卡更新

---

## 3. 逐卡 TDD 接入流程

### 3.1 流程不变，AC 增强
**RED → GREEN → REFACTOR → COMMIT 四步硬约束完全保留**（HARNESS §4.1）。

每张 SPEC-E 任务卡的 AC 增加一条**视觉一致性 AC**：

```
- [ ] AC-N: 组件视觉与 prototype/src/components/<对应组件>.tsx 一致
       （通过 playwright snapshot 或 vitest + jest-image-snapshot 验证）
```

### 3.2 GREEN 阶段的"原型代码移植"规则
GREEN 阶段允许参考 `prototype/` 同名组件代码，但必须：

1. **类型必须来自 SPEC-A**：所有 props / state / 事件必须从 `src/shared/types/` 或 `src/shared/schemas/` 导入；`tsc --noEmit` 强制
2. **组件结构遵循 SPEC-E 任务卡 Allowed Files**：原型若把多个职责放在一个组件，迁移时拆分
3. **样式可直接复用**：tailwind class、CSS 变量、主题 token 可整段复制
4. **业务逻辑必须重写**：原型里的 mock data、hardcoded URL、临时 hook 必须替换为 `useProjects` / `useWebSocket` 等正式 hook
5. **文件大小限制**：单文件 ≤ 300 行（HARNESS §6），超过即拆分

### 3.3 RED 阶段的测试形态
- **单元测试**（vitest）：组件 props/state/event 行为
- **集成测试**（vitest + MSW）：组件 + hook + mock API 联动
- **e2e 测试**（playwright）：分两类标签（见 §4.4）
- **视觉测试**（playwright snapshot 或 vitest + jest-image-snapshot）：与原型对比

### 3.4 测试通过即证明"遵循原型"
"遵循原型"不靠人工对照，而是靠测试机制保障：
- 视觉 AC 失败 → 视觉不一致 → 不能 GREEN
- tsc 失败 → 类型不符 SPEC-A → 不能 GREEN
- 契约一致性测试失败（§4.3） → 类型与后端 schema 漂移 → 不能 GREEN

---

## 4. 联调 Mock 层与真实环境

### 4.1 三层联调环境

| 层 | 工具 | 触发 | PR-blocking |
|---|---|---|---|
| Unit / Component | vitest + @testing-library/react + MSW | 每次 commit | 是 |
| Integration (mock backend) | playwright + MSW | 每次 PR | 是 |
| E2E (real backend) | playwright + `make dev` | 夜间定时 | 否 |

### 4.2 MSW + Fixture 单一来源（新卡 SPEC-B-017）

**核心原则**：mock 数据只能有一份真值，前后端测试都从同一份读取。

```
tests/fixtures/api/
├── projects/
│   ├── list_response.json           ★ 唯一真值
│   ├── detail_p3.json
│   └── ...
├── events/
│   ├── phase_advance.json
│   └── ...
└── README.md                         字段约定 + schema 引用
```

`src/frontend/mocks/` 通过 MSW handlers 直接读取 `tests/fixtures/api/*.json`，不再独立维护。

CI 通过 `scripts/validate_fixtures.py` 校验所有 fixture 符合 `src/shared/schemas/*.json`，失败即阻塞。

### 4.3 契约一致性测试（新卡 SPEC-A-XXX）

`tests/contract/test_frontend_types_match_schemas.py`：
- 解析 `src/frontend/types/*.ts` 中所有 interface
- 解析 `src/shared/schemas/*.json` 中所有 schema
- 逐字段比对，任一不一致即 FAIL
- PR-blocking

→ 防止前端类型与后端契约悄悄漂移。

### 4.4 真实联调环境（新卡 SPEC-B-018）

```
docker-compose.dev.yml          # FastAPI + SQLite + Redis（如需）
Makefile:
  dev:    docker-compose -f docker-compose.dev.yml up -d && pnpm --filter frontend dev
  seed:   python scripts/seed_dev_db.py
  e2e:    BASE_URL=http://localhost:3000 npx playwright test --grep @e2e-real
scripts/seed_dev_db.py          # 写入 P0~P11 各阶段示例项目
```

夜间定时跑 `@e2e-real` 标签的 playwright 测试，不阻塞 PR；连续 3 晚失败 → 自动开 GitHub issue。

### 4.5 Playwright 测试标签分层

```typescript
test('project list renders', { tag: ['@integration-msw'] }, async ({ page }) => { ... })
test('full pipeline P0 → P11', { tag: ['@e2e-real'] }, async ({ page }) => { ... })
```

11 张已有 SPEC-E playwright 卡：默认归类 `@integration-msw`（PR-blocking），少量真正端到端的关键路径补 `@e2e-real`（夜间）。

---

## 5. 风险与回滚

| # | 风险 | 触发场景 | 守卫 / 回滚 |
|---|---|---|---|
| R1 | 原型与生产前端漂移 | 原型迭代继续，生产已合并 | `prototype/` 目录明确豁免 HARNESS §3.2（不走 SPEC-X-NNN 任务卡流程），其 commit 使用 `[PROTO]` 前缀；每月人工 diff PROTOTYPE_INDEX vs `src/frontend/`；漂移项进入下一轮 v3.X DELTA。该豁免由 SPEC-B-017 AC 明确写入 HARNESS §1.2 例外表 |
| R2 | 契约扩展无序 | 多人并行开新原型组件 → 各自加字段 | 所有契约扩展必须先进 v3.18 DELTA → review 通过 → 才能写入 SPEC-A → 才能在前端用 |
| R3 | TDD 被绕过 | 开发者直接复制原型代码不写测试 | git pre-commit hook 检查：`src/frontend/**/*.tsx` 变更必须有对应 `tests/unit/frontend/**/*.test.tsx` 同步变更；CI 二次校验 |
| R4 | Fixture 漂移 | 前端改了 mock 但没改 schema | `validate_fixtures.py` CI 阻塞；`test_frontend_types_match_schemas.py` PR 阻塞 |
| R5 | E2E 测试不稳定 | 真实联调环境引入 flakiness | `@e2e-real` 不阻塞 PR；连续 3 晚失败开 issue；优先排查 seed 数据/时序问题，不直接禁用测试 |
| R6 | 原型并行演进吞噬迁移工作 | 原型每周改，迁移跟不上 | 锁定 `prototype/` 迁移基线版本（git tag `proto-baseline-YYYYMMDD`），迁移完成前原型 PR 只能改 README/INDEX，不能改 src |

### 5.1 回滚单元
- **PR 级回滚**：单张任务卡 PR 可独立 revert，不影响其他卡
- **Wave 级回滚**：Wave 0 / 1 / 2 / 3 各自独立分支，失败可整 Wave 撤回
- **契约级回滚**：v3.18 DELTA 若被否决，已基于其修改的前端代码必须同步回退

---

## 6. Wave 计划

| Wave | 内容 | 依赖 | 产出 |
|---|---|---|---|
| **Wave 0** | 基础设施 3 张新卡 | 无 | `prototype/` 目录就位、MSW + fixture 体系、`make dev` 可用、契约测试 CI 接入 |
| **Wave 1** | 原型审计 + DELTA 文档 | Wave 0 完成 | `PROTOTYPE_INDEX.md`、`docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` |
| **Wave 2** | SPEC-A 契约更新 | Wave 1 review 通过 | SPEC-A 新增 endpoints/events/types 任务卡，对应实现完成 |
| **Wave 3** | 21 张 SPEC-E 任务卡逐卡 TDD 落地 | Wave 2 完成 | `src/frontend/` 全量实现，所有 AC（含视觉 AC）通过 |

### 6.1 Wave 0 三张新卡

#### SPEC-B-017: 前端 Mock 层与 Fixture 单一来源
- **Allowed**: `src/frontend/mocks/**`、`tests/fixtures/api/**`、`scripts/validate_fixtures.py`、`prototype/**`（新建目录）、`HARNESS.md`（§1.2 例外表新增 `prototype/**` 豁免条目，需红灯审批）
- **Forbidden**: `src/backend/**`、`src/shared/schemas/**`
- **AC-1**: MSW handlers 启动后拦截所有 `/api/v1/*` 请求
- **AC-2**: handlers 数据从 `tests/fixtures/api/*.json` 读取
- **AC-3**: `scripts/validate_fixtures.py` 校验所有 fixture 符合 `src/shared/schemas/*.json`
- **AC-4**: CI 含 fixture 校验步骤，违规阻塞
- **AC-5**: vitest + playwright 都能复用同一套 handler
- **AC-6**: `prototype/` 目录建立，`HARNESS.md` §1.2 明确 `prototype/**` 为"隔离只读原型区，commit 前缀 `[PROTO]`，不受 SPEC-X-NNN 任务卡约束"

#### SPEC-B-018: 真实联调开发环境
- **Allowed**: `docker-compose.dev.yml`、`Makefile`（dev/seed/e2e 目标）、`scripts/seed_dev_db.py`
- **Forbidden**: `infra/prod/**`、`deploy/prod/**`
- **AC-1**: `make dev` 单命令启动后端 + 前端
- **AC-2**: `make seed` 写入 P0~P11 各阶段示例项目（≥12 条）
- **AC-3**: `make e2e` 跑 `@e2e-real` 标签的 playwright 测试
- **AC-4**: `.github/workflows/nightly_e2e.yml` 夜间定时执行
- **AC-5**: 连续 3 晚失败自动开 GitHub issue

#### SPEC-A-XXX: 契约一致性测试
- **Allowed**: `tests/contract/test_frontend_types_match_schemas.py`、`scripts/check_type_schema_parity.py`
- **Forbidden**: `src/frontend/types/**`、`src/shared/schemas/**`（只读）
- **AC-1**: 测试解析 `src/frontend/types/*.ts` 与 `src/shared/schemas/*.json`
- **AC-2**: 任一字段不一致即 FAIL
- **AC-3**: 测试在 PR CI 中执行，失败阻塞
- **AC-4**: 失败信息明确指出哪个字段在哪边、差异是什么

---

## 7. 完成标准（Definition of Done for this Initiative）

- [ ] `prototype/` 目录建立，原型代码导入，PROTOTYPE_INDEX.md 完成
- [ ] `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` 完成并经许阳 review
- [ ] SPEC-B-017 / SPEC-B-018 / SPEC-A-XXX 三张新卡全部 AC 通过
- [ ] v3.18 DELTA 中所有 T3 项要么已回写 SPEC-A，要么已明确 reject
- [ ] 21 张 SPEC-E 任务卡：AC 已加视觉一致性条目，全部 GREEN
- [ ] CI 含：fixture 校验、契约测试、madge 圈检、`@integration-msw` playwright；夜间含 `@e2e-real`
- [ ] PROGRESS.md 记录本 initiative 全过程

---

## 8. 不做什么（明确拒绝的方案）

- ❌ **Pact / Spring Cloud Contract**：SPEC-A 已有 schema 单一真值，再引契约测试框架属过度工程
- ❌ **Chromatic / Percy**：付费视觉回归服务；playwright snapshot + 原型对照已足够
- ❌ **直接把 prototype/ 当生产前端**：会绕过 TDD、类型契约、文件大小限制，违反 HARNESS
- ❌ **保留两份 mock 数据（前端一份 + 后端一份）**：必然漂移；统一到 `tests/fixtures/api/`
- ❌ **现在就读原型源码并设计组件级映射**：先建隔离与流程框架，原型审计放在 Wave 1
