# 复盘：AI-Video-System API 集成阶段缺陷与流程改进方案

- 文档日期：2026-04-26
- 文档版本：**v2（评审反馈修订版）**
- 文档作者：Claude Code（基于本次会话现场分析）
- 文档对象：项目流程与工程系统（Harness、SPEC Coding Workflow）
- 文档用途：作为可被另一 AI 独立评审的复盘材料；评审通过后转化为 AGENTS.md / HARNESS.md 的具体修订条款
- 评审依据：`docs/REVIEW_2026-04-26_API-integration-gap_Spec-Coding-hard-gates.md`

---

## 0.0 v2 修订说明

v1 被审核判定"**不放行**"，主要原因是 R2/R7 等改进仍停留在"AGENTS.md / HARNESS.md 文本约束 + wrapup 模板 + AI 自述证据"层面，属于软约束；R3 根因诊断与项目现状不符（项目已有 `src/shared/contracts/api_routes.py/ts`，真实问题是多真源、非生成、未强制消费）；机制改造缺少 driver / hook / CI / verifier 的机械阻断点；并缺少"检查器本身如何被验证"（fault injection / mutation test）。

v2 按审核反馈做以下结构性修改，所有改动以"硬闸门 + exit code"为目标，禁止把 AI wrapup 自述当证据：

| 修订点 | v1 | v2 |
|---|---|---|
| §1.5 SPEC 现状描述 | "无机器可读源" | 修正为"已有 `api_routes.py/ts` 但未成为唯一真源、未生成、未强制消费" |
| §2 现场证据 | 仅列 5 类错漏 | 新增 §2.6 现场审核证据（24/21/17/9 路由对比） |
| §3 优先级矩阵 | R1-R8 单表 | 重组为 P0/P1/P2 三档；新增 R9-R14 |
| §4.2 R2 | 修订 Verification Contract 文本 | 重写为"Task Done Evidence Gate"，验收落到 `python scripts/verify_task_done.py --task-id <id>` exit code |
| §4.3 R3 | 新建 routes.yaml 作为机器可读源 | 修正根因；明确 `contracts/routes.yaml` 唯一真源 + 生成链 + generated files 禁手改 |
| §4.4 R4 | endpoint coverage | 扩展为 `spec_item_coverage`（endpoint 只是 `item.type=api_route` 的一种） |
| §4.5 R5 | contract / integration tests | 强制加载真实 `src.backend.api.main:app`；引入 Schemathesis / Spectral |
| §4.6 R6 | 启动期 assert + main.py 收敛 | 新增 `scripts/lint_fastapi_routes.py`（AST lint + double-prefix pattern） |
| §4.7 R7 | 禁止裸 `fetch('/api/')` | 升级为禁止业务代码出现任何 `/api/` 字符串字面量；只允许 generated SDK / fixtures / contracts |
| §4.8 R8 | 独立 P2 项 | 降级并入 R3 schema/style lint |
| §4.9 R9（新增） | — | Task Done Evidence Gate（统一 done 判定脚本） |
| §4.10 R10（新增） | — | Fault Injection Gate Test（证明 gate 本身有效） |
| §4.11 R11（新增） | — | `spec_manifest.yaml` / `spec_item_coverage`（不只盯 endpoint） |
| §4.12 R12（新增） | — | Impact-Based Required Gates（按变更文件决定必跑 gate） |
| §4.13 R13（新增） | — | Generated Files 禁手改（`make generate && git diff --exit-code`） |
| §4.14 R14（新增） | — | 禁用正常流程里的 `--no-verify` |
| §5 依赖图 | R3 为中心 | 重画为 contract → generated → runtime → evidence gate → fixer loop |
| §6 元教训 | "TC PASS ≠ task done" | 重写为三段式：测试通过率 ≠ SPEC 覆盖率；Done = 全集覆盖 + runtime gates + 可复现证据；判定主体是 Harness 不是 AI |
| §7（新增） | — | SPEC 写法结构（稳定 ID + 机器合同 + 验证映射 + fixtures） |

v2 完成审核 §9 列出的全部 10 条放行条件后，方可作为 AGENTS / HARNESS / Spec Coding 机制改造的依据。

---

## 0. 评审说明（写给评审 AI）

### 0.1 评审目标
请你不要直接复述本文，而是基于以下五个维度对每条改进项（R1–R8）独立打分并给出修订建议：

1. **根因诊断是否正确**：本文标注的根因，是否真的能解释现场观察到的偏差。是否存在更深一层的根因？
2. **改进方案是否对症**：方案是否真的能阻断该根因下次复发，而不是把症状盖住。
3. **方案 ROI 是否合理**：实施成本（开发人天、工具链改造）vs 预期收益（阻断哪类故障）的比例。
4. **替代方案是否被充分考虑**：本文给出的"为什么不选 X"是否成立，是否漏掉了更优的替代路径。
5. **可验证性**：每条改进的"验收标准"是否真的可以被另一个 AI / 流水线机械化校验。

输出格式建议：

```
R{n}: {改进项编号}
  根因诊断: 正确 / 部分正确 / 错误，理由：...
  方案对症性: 高 / 中 / 低，理由：...
  ROI: 高 / 中 / 低，理由：...
  替代方案盲区: 列出未考虑的替代方案（如有）
  可验证性: 强 / 弱，建议补充的验收点：...
  修订建议: ...
```

### 0.2 评审基线
评审时请假定：
- 本项目是 AI 驱动开发（许阳为产品负责人，不写代码；所有代码由 AI agent 在 Harness 流程下产出）
- 流程哲学约束在 `AGENTS.md`，详见 §1.3
- 现有 Harness 通过 TC（Test Case）数量度量进度，详见 §1.4
- SPEC 文档为 markdown 散文格式，详见 §1.5
- 评审你看不到本次现场的代码，但本文 §2 给出了关键代码片段与现场证据

### 0.3 已知盲点（v2 已部分关闭）
- 本文未深入探讨 BDD 验收层（SPEC-G）与 SPEC-A 路由层的耦合是否也有同类裂缝。**v2 缓解**：R11 `spec_item_coverage` 把 BDD scenario 也纳入 `item.type=bdd_scenario`，由 Harness 客观分母统一覆盖。
- 本文未评估前端 E2E（Playwright/Cypress）是否值得在当前阶段引入，仅在 R5 中提及。
- 本文未量化"已实施改进的工程改造成本"的具体人天，仅按相对工作量分级。
- v2 仍未量化"R10 fault injection 的注入用例集"的完备性，需要在落地阶段持续扩展。

---

## 1. 上下文背景（让评审 AI 不依赖外部材料即可理解）

### 1.1 项目是什么
AI-Video-System 是一个 Web 交互式视频制作系统，PRD v3.3。架构上分为：

- 前端 SPA（位于 `src/frontend`，Vite + React）
- 后端 API（位于 `src/backend`，FastAPI）
- Pipeline phases（视频制作 12 个阶段的 agent 编排）
- 媒体渲染层（TTS / 图像合成 / 视频拼接）

部署形态：`docker compose up` 起 backend + frontend + 依赖服务，浏览器访问 `localhost:3000`。

### 1.2 SPEC 体系
项目把规范拆为 7 份 SPEC：

- SPEC-A：API 契约（路由总表、请求/响应字段、错误码）
- SPEC-B：基础设施与部署
- SPEC-C：后端核心（FSM、agent 编排、状态机）
- SPEC-D：Pipeline 12 阶段
- SPEC-E：前端 UI
- SPEC-F：媒体渲染
- SPEC-G：BDD 验收

本次复盘的核心矛盾点全部落在 **SPEC-A**（路由总表 25 个 endpoint）与其他 SPEC、与实际代码、与前端调用的偏离。

### 1.3 流程约束（AGENTS.md 摘要）
- 标准工作流：Research → Plan → Implement → Verify → Wrapup
- TDD 硬约束：写实现前必须有失败测试（RED-GREEN-REFACTOR）
- Verification Contract：声明完成前必须有命令输出证据
- Business-Complete Delivery Gate：以"业务端到端可用"为最高完成标准
- 决策权限矩阵：红/黄/绿灯三档

### 1.4 Harness 当前状态
- 度量主指标：TC PASS 数 / TC 总数
- 当前基线（写入 memory）：411 passed / 41 skipped
- 验证形态：以 pytest 单元测试 + 部分 BDD scenario 为主

### 1.5 SPEC 当前形态（v2 修正）
SPEC-A 路由总表是 markdown 表格：

```markdown
| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/projects/{id}/costs | 查询项目花费 |
| POST   | /api/projects/{id}/advance | 推进到下一阶段 |
| ...    | ...  | ...         |
```

**v1 错误描述**："无 OpenAPI YAML / JSON schema / routes.yaml 等机器可读源"。

**v2 修正后的真实状态**：
- 项目已经存在 `src/shared/contracts/api_routes.py` 和 `src/shared/contracts/api_routes.ts` 两份"半机器化"路由 registry。
- 但它们：
  - 不是 single source of truth（与 SPEC-A markdown、FastAPI runtime 三处并列存在，互相不强约束）。
  - 不是 generated（手工维护，会与 markdown 漂移）。
  - 不被 runtime / frontend / tests / smoke / CI **强制消费**（没有任何 gate 在跑"declared 与 actual 必须一致"）。
- 因此 R3 的真实问题不是"完全没有机器可读源"，而是"**多真源 + 非生成 + 未强制消费**"。

不存在的关键文件（v2 落地需要新建）：
- `docs/specs/routes.yaml` 或 `contracts/routes.yaml`（候选 single source of truth）
- `scripts/smoke_cold_start.sh`
- `scripts/spec_coverage.py`
- `scripts/verify_task_done.py`
- `scripts/fault_injection_check.py`
- `scripts/lint_fastapi_routes.py`
- `contracts/spec_manifest.yaml`

---

## 2. 现场证据（事故快照）

### 2.1 触发现象
开发者执行 `docker compose up`，浏览器访问 `localhost:3000`，页面显示"加载失败"。后端进程正常启动，未崩溃。

### 2.2 错漏统计
对照 SPEC-A 路由总表（25 endpoint）逐条核对，发现：

| 偏差类型 | 数量 | 占比 |
|----------|-----:|-----:|
| 完全缺失（端点未实现） | 11 | 44% |
| Prefix 双叠（路径错） | 5 | 20% |
| 路径命名不符（单/复数） | 1 | 4% |
| 实现了但 main.py 未挂载 | 1 | 4% |
| 装饰器风格不一致 | 6 | 24% |
| 完全正确 | 1 | 4% |

合计错漏率约 **64%**。在此情况下，pytest 报告依然显示 411 passed。

### 2.3 关键代码片段（节选）

**main.py（错误的双叠 prefix）**
```python
app.include_router(system.router,        prefix="/api/system")
# 而 routes/system.py 内部装饰器写的是：
# @router.get("/api/system/status")
# 实际暴露路径变成：/api/system/api/system/status
```

**routes/settings_bridge.py（唯一正确的写法）**
```python
router = APIRouter(prefix="/api/settings")

@router.put("/preferences")  # 相对路径
def update_preferences(...): ...
```

**SPEC-A vs 后端实际**
```
SPEC-A:  GET /api/projects/{id}/costs   （复数）
后端:    GET /api/projects/{id}/cost    （单数）
```

**已实现但未挂载**
```
src/backend/api/preferences.py 定义了 POST /preferences/writeback-suggestions
（v3.16 BDD-2 修订要求），但 main.py 的 import 列表里没有它。
```

**vite.config.ts 缺 proxy**
```ts
// 当前：
export default defineConfig({
  plugins: [react()],
  // 没有任何 proxy 配置
})
// 结果：dev 环境下 /api/* 和 /ws/* 全部被 SPA 兜底为 index.html
```

### 2.4 关键对比：测试 vs 现实
- 411 个 pytest 测试用例：基本是 unit 层，直接 import handler 函数调用，绕过 FastAPI app 装配
- 没有任何测试启动真实 app 后用 httpx/TestClient 打 SPEC-A 列出的 25 个真实路径
- 没有任何 e2e 测试做 `docker compose up + curl + 检查响应`

### 2.5 一句话本质
**整个开发周期内，AI 从来没"走过一遍用户路径"**。所有 PASS 都发生在抽象空间里；现实空间里 64% 错漏。

### 2.6 v2 现场审核证据（评审 AI 现场核对）

评审过程中执行了以下脚本，对 `src.shared.contracts.api_routes.API_ROUTES` 与 `src.backend.api.main:app` 做 normalized 对比：

```python
import re
from src.backend.api.main import app
from src.shared.contracts.api_routes import API_ROUTES

def norm(p):
    return re.sub(r"\{[^}]+\}", "{}", p)

actual = set()
for route in app.routes:
    if not hasattr(route, 'methods'):
        continue
    for m in route.methods:
        if m not in {'HEAD', 'OPTIONS'}:
            actual.add((m, norm(route.path)))
expected = [(r['method'], r['path'], norm(r['path']))
            for r in API_ROUTES if r['type'] == 'rest']
```

输出：

```text
normalized declared rest: 24
normalized actual registered: 21
normalized missing: 17
double-prefix suspected routes: 9
```

典型 double-prefix 命中：

```text
GET  /api/system/api/system/status
POST /api/system/api/projects
GET  /api/tasks/api/projects/{project_id}/tasks
GET  /api/projects/api/projects/{project_id}/preferences
GET  /api/cost/api/projects/{project_id}/cost
```

证据含义：
1. 项目即使已经有 `api_routes.py` 这份半机器化 registry，仍然没有任何 gate 在 runtime 层强制 declared = actual。
2. 411 passed pytest 完全感知不到这种装配层不一致。
3. 这进一步证实了 R9（Task Done Evidence Gate）和 R3（generated artifacts）必须落地——光有 registry 不够，必须有强制消费它的 gate。

### 2.7 driver / CI 现状（v2 现场核对）

- `scripts/run_task_driver.py` 已经实现 `developer → verifier → fixer → reviewer → fixer` 闭环，但 verifier 主要执行 task card 中的 `verification_commands`，**缺少全局 hard gate**（SPEC coverage / cold-start smoke / OpenAPI diff / frontend contract usage / generated artifacts up-to-date）。
- `.github/workflows/ci.yml` 当前 PR 必过项只有：

  ```text
  pytest tests/unit/ tests/contract/ -v
  pnpm --filter frontend tsc
  pnpm --filter frontend test
  ```

- `nightly_e2e.yml` 是 nightly / manual 触发，**不是 PR / task done 的必过 gate**。
- 因此本次事故链条："driver verifier 通过 → CI 通过 → AI 声明 done"，整条链没有任何一处会跑 cold-start / contract diff。

---

## 3. 优先级矩阵（v2 重组）

v1 的"严重度 / 改造成本"二维矩阵在审核中被指出过于粗糙：R1/R2 都是 P0 但 R2 的落点（修订 AGENTS.md 文本）仍是软约束。v2 按"**让 Harness 不能撒谎 → 减少 AI 犯错空间 → 长期一致性**"三档重排，并新增 R9-R14。

### 3.1 P0：让 Harness 不能撒谎（机制硬化，无证据则 exit 1）

| 顺序 | ID | 项目 | 目标 | 落地形态 |
|---:|---|---|---|---|
| 1 | R9 | Task Done Evidence Gate | 没有机器证据就不能 done | `scripts/verify_task_done.py` exit code |
| 2 | R3 | Single Source of Truth | 选唯一合同源，生成所有派生产物 | `contracts/routes.yaml` + 生成链 + `git diff --exit-code` |
| 3 | R4/R11 | Spec Item Coverage | 用 SPEC 全集做客观分母 | `contracts/spec_manifest.yaml` + `build/spec_coverage.json` |
| 4 | R1 | Cold-start Smoke | 真实环境下验证用户路径 | `scripts/smoke_cold_start.sh` + `build/smoke_report.json` |
| 5 | R10 | Fault Injection Gate Test | 证明 gate 真能抓住已知错误 | `scripts/fault_injection_check.py` |
| 6 | R2 | Driver / CI Enforcement | 把 verification contract 变成命令 exit code | `run_task_driver.py` verifier 后调用 R9，失败进入 fixer loop |

### 3.2 P1：减少 AI 犯错空间（结构性根治）

| 顺序 | ID | 项目 | 目标 | 落地形态 |
|---:|---|---|---|---|
| 7 | R6 | Router 单源 + lint | 阻断 double prefix / 漏 include | `scripts/lint_fastapi_routes.py` + 启动期 assert |
| 8 | R5 | Contract / Integration Tests | 覆盖装配层与业务流 | 必须 `import src.backend.api.main:app`；可选 Schemathesis |
| 9 | R7 | Frontend Generated SDK | 消灭前端手抄路径 | 禁止业务代码出现 `/api/` 字面量；只允许 generated SDK |
| 10 | R12 | Impact-Based Required Gates | 按变更文件自动决定必跑 gate | CI required check matrix |
| 11 | R13 | Generated Files 禁手改 | 强制"改 yaml → 重生成"流程 | `make generate-contracts && git diff --exit-code` |
| 12 | R14 | 禁用正常流程 `--no-verify` | 防止 AI 走捷径 | `AVS_UNSAFE_ALLOW_NO_VERIFY=1` 才允许；wrapup 标记 `NOT_DONE_DEBUG_ONLY` |

### 3.3 P2：长期一致性

| 顺序 | ID | 项目 | 目标 |
|---:|---|---|---|
| 13 | R8（并入 R3） | Naming lint | 控制 API 风格漂移；并入 R3 schema/style lint |
| 14 | — | OpenAPI / Spectral / Schemathesis | 引入成熟生态工具增强合同验证 |

### 3.4 优先级判定原则（v2）

"严重度"和"改造成本"已不再作为主排序依据，因为：

1. v1 把 R1+R2 标为 P0 是对的，但漏掉了"R2 必须从文本变成 exit code"这一关键。
2. v1 把 R3 标为"重 + 中"低估了它——R3 是 R1/R4/R5/R7/R8 的依赖项，不解决 R3 其他都打折扣。
3. v1 没有 R9/R10，导致整套机制缺少"统一 done 判定 + 自验"两个关键节点。

v2 排序逻辑：**先建闸门（R9/R3/R4-R11/R1/R10）→ 再把闸门接入 driver/CI（R2/R12）→ 再消灭代码层犯错空间（R6/R5/R7/R13/R14）→ 最后做风格收敛（R8/Spectral）**。

---

## 4. 改进项详述

> 每条统一八段：**现场证据 → 背景与根因 → 不改会怎样 → 改什么 → 怎么改 → 验收标准 → 为什么这么改（含替代方案对比） → 责任与优先级**。

---

### R1：Cold-Start Smoke 强制闭环

#### 4.1.1 现场证据
- `docker compose up` + 浏览器访问 `localhost:3000` 报"加载失败"
- 但 `pytest` 全绿（411 passed）
- 整个开发周期内，**AI 没有任何一次完整执行过"启动 → 访问 → 操作"的真实闭环**

#### 4.1.2 背景与根因
现有 TC 全部跑在 pytest 进程内：
- 直接 import handler 函数调用
- 或使用 FastAPI TestClient 时绕过了 main.py 的 router 装配（部分测试用 fixture 自定义 app，并非加载真实 main.py）

这意味着：
- main.py 把 `/api/system` 双叠成 `/api/system/api/system/status` —— TestClient 看不见
- preferences.py 没被 include —— pytest 看不见（测试直接 import 测，不依赖 main.py）
- vite.config.ts 没 proxy —— 后端单元测试完全感知不到

**根因：测试发生在抽象空间，从未进入真实运行时空间**。这是 AI 驱动开发的典型盲区——AI 只对"被流程要求做的事"负责，没流程要求 cold-start，AI 就不会主动做。

#### 4.1.3 不改会怎样
- 短期：本次问题修复后，下次新增 endpoint 时同类问题（忘 include / 写错 prefix / 前端 proxy 漏配）会**立刻再发**。这不是低概率事件，而是必然事件。
- 长期：每次集成阶段都要靠人工"启动一下试试"补救。AI 报告的"完成"信用度持续下降。
- 终态：Harness 的 PASS 信号失效，许阳必须每次亲自验证，AI 驱动开发的核心价值（"不需要盯着"）被推翻。

#### 4.1.4 改什么
新增一个**强制 cold-start smoke 阶段**，作为任何里程碑（milestone）声明完成前的最后一道闸门。

#### 4.1.5 怎么改
**A. 新增脚本** `scripts/smoke_cold_start.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. 起服务
docker compose -f docker-compose.dev.yml up -d --build
trap 'docker compose -f docker-compose.dev.yml down' EXIT

# 2. 等待健康
./scripts/wait_for_health.sh http://localhost:8000/api/system/status 60

# 3. 加载 SPEC 路由总表，逐条 curl
python3 scripts/smoke_check_routes.py \
  --spec docs/specs/routes.yaml \
  --base-url http://localhost:8000 \
  --frontend-url http://localhost:3000 \
  --report build/smoke_report.json

# 4. 任何 404 / 500 / connection refused / 双叠路径检测命中 → 退出码非 0
```

**B. `scripts/smoke_check_routes.py` 行为**：
- 读 `routes.yaml`（见 R3）拿到 25 个 endpoint
- 对每条做 `OPTIONS` + `HEAD` + 必要时构造合法 payload 的 `GET/POST`
- 检查响应：
  - 不是 404
  - 不是 5xx（除非 SPEC 显式声明该状态码）
  - 路径在 OpenAPI `/openapi.json` 里存在且**不重复**（防双叠）
- 检查前端：`curl http://localhost:3000` 返回 HTML，且 HTML 内引用的 `/api/*` 在 dev proxy 下能命中后端

**C. 接入 Harness**：
- 修改 `HARNESS.md`：milestone 完成定义里增加一条"smoke_cold_start.sh 退出码 0"
- 修改 `Makefile`：增加 `make smoke`
- 修改 CI（如有）：milestone tag push 触发 smoke

#### 4.1.6 验收标准（v2 硬化）

v1 验收最后一条"AI wrapup 时贴证据"是软约束，被审核否定。v2 改为机器闸门：

- **命令**：`make smoke` 或 `bash scripts/smoke_cold_start.sh`
- **产物**：`build/smoke_report.json`，结构必须包含：

  ```json
  {
    "generated_at": "2026-04-26T12:34:56Z",
    "contract_hash": "sha256:<contracts/routes.yaml 的内容哈希>",
    "runtime_openapi_hash": "sha256:<runtime /openapi.json 的内容哈希>",
    "spec_version": "v3.18",
    "endpoints_checked": 25,
    "endpoints_pass": 25,
    "endpoints_fail": [],
    "double_prefix_hits": [],
    "frontend_proxy_check": "pass"
  }
  ```

- **fail 条件（exit 1）**：
  - 任一 endpoint 返回 404 / 5xx（除 SPEC 显式声明的状态码）
  - 任一路径命中 `/api/api/` 或 `/api/<seg>/api/` double-prefix pattern
  - frontend `/api/*` proxy 探测失败
  - `contract_hash` 与 `contracts/routes.yaml` 当前哈希不匹配（防复用旧报告）
  - `runtime_openapi_hash` 与当前 runtime `/openapi.json` 哈希不匹配
  - 报告 `generated_at` 早于本次 commit 时间（防复用过期证据）
- **接入点**（不再依赖 AI 自觉）：
  - `scripts/run_task_driver.py` 的 verifier 阶段必须调用 R9 evidence gate，evidence gate 内部检查 `build/smoke_report.json` 是否新鲜且通过。失败则进入 fixer loop。
  - `.github/workflows/ci.yml` 在变更触发 R12 矩阵命中 backend / docker-compose 时把 `make smoke` 设为 required check。
- **回归验证**：在不改业务代码前提下重放本次错漏（删除一个 router include / 加一个 double prefix）→ smoke 必须红，且 R10 fault injection 用例覆盖此场景。

#### 4.1.7 为什么这么改

**vs 替代方案 1：依赖人工抽测**
- 不可行。许阳是 product owner 不写代码，AI 不主动做就不会发生。
- 现状已经证明这条路走不通——本次就是没人主动 cold-start。

**vs 替代方案 2：只做 OpenAPI 静态校验，不实启动**
- 漏检面太大。OpenAPI 校验抓不到：vite proxy 没配、前后端跨容器网络不通、依赖服务（DB/Redis）启动顺序错。
- 真启动是唯一能覆盖"装配后行为"的手段。

**vs 替代方案 3：完整 e2e（Playwright）**
- 成本太高。e2e 适合后期，初期一个 smoke 就足以阻断 90% 故障。
- 本方案可向 e2e 平滑升级。

**核心理由**：本次错漏中**所有 5 个类型都会被 smoke 捕获**，且实施成本低（< 1 人天），ROI 极高。这是单点撬动收益最大的一条改进。

#### 4.1.8 责任与优先级
- 优先级：**P0**
- 责任：流程层（Harness）+ 工具层（脚本）
- 落地阻塞：依赖 R3（routes.yaml）才能做"逐条 curl"。在 R3 完成前，可先用硬编码列表过渡。

---

### R2：Driver / CI Enforcement（v2 重写，原"Verification Contract 加入 E2E 强制点"作废）

> **v1 → v2 关键变化**：v1 把 R2 落在"修订 AGENTS.md Verification Contract 文本 + wrapup 模板"，被审核否定为软约束。v2 R2 不再修文本，只做一件事：**让 driver / CI 在没有 R9 evidence gate 通过时不允许任何任务声明 done**。文本类的修订降级为说明，真正承载约束的是 exit code。

#### 4.2.1 现场证据
- `scripts/run_task_driver.py` 已有 `developer → verifier → fixer → reviewer → fixer` 闭环，但 verifier 只跑 task card 的 `verification_commands`，**没有任何全局 hard gate**。
- AGENTS.md "Business-Complete Delivery Gate" 提到"业务端到端可用"，但当前没有任何工具会因为它的缺失而 exit 1。
- 结果：AI 把 411 个 pytest PASS 当作"业务端到端"，driver 看不到 SPEC 覆盖、smoke、OpenAPI diff 是否通过，一路放行到 done。
- §2.7 现场核对印证：CI required check 不包含 e2e / cold-start / contract diff。

#### 4.2.2 背景与根因
AGENTS.md 已经有正确的哲学，但**哲学没有被翻译成命令 exit code**。当 done 判定主体是 AI 自身时，AI 在符号空间通过验证的能力 + 倾向最低成本路径的特性 → 必然系统性偏低估。

**v1 根因（部分对）**：规范层"软约束"没有 enforcement point。
**v2 根因（修正）**：规范层 + 工具层都缺少 enforcement point，**真正缺失的是"done 判定的主体不是 AI，而是机器"**。把 done 还给 AI 自述，等于把考官岗位交给考生。

#### 4.2.3 不改会怎样
- driver verifier 永远只跑局部测试，AI 永远在"task 通过 = 全局通过"的自述中漂移。
- AGENTS.md 哲学条款持续被"理解了但不执行"。
- Harness 信号长期失真，需要许阳事后人肉兜底。

#### 4.2.4 改什么
**只改两处工具，不改文本**：

1. **`scripts/run_task_driver.py`**：在 verifier 阶段之后，强制调用 R9 evidence gate；evidence gate 失败则进入 fixer loop，不允许跳过、不允许人工 override（除非显式 `AVS_UNSAFE_ALLOW_NO_VERIFY=1`，见 R14）。
2. **`.github/workflows/ci.yml`**：按 R12 Impact-Based Required Gates 矩阵把对应 evidence 命令设为 required check。

文本修订（AGENTS.md / HARNESS.md）只做"指向新工具"的一句话引用，不再承载约束。

#### 4.2.5 怎么改
**A. `run_task_driver.py` 改造**：

```python
# 原有：
# developer -> verifier -> fixer -> reviewer -> fixer

# 改造后：
# developer -> verifier -> evidence_gate -> fixer -> reviewer -> evidence_gate -> fixer

def run_evidence_gate(task_id: str) -> int:
    return subprocess.call([
        "python", "scripts/verify_task_done.py",
        "--task-id", task_id,
    ])

# verifier 通过后必须调 evidence_gate
if run_evidence_gate(task_id) != 0:
    enter_fixer_loop(reason="evidence_gate_failed")
```

**B. CI 修订**（按 R12 矩阵）：

```yaml
# .github/workflows/ci.yml
jobs:
  evidence-gate:
    needs: [unit, contract, frontend-tsc]
    runs-on: ubuntu-latest
    steps:
      - run: make smoke           # R1
      - run: make spec-coverage   # R4/R11
      - run: make openapi-diff
      - run: python scripts/verify_task_done.py --task-id ${{ github.event.pull_request.title }}
```

把 `evidence-gate` 加入 branch protection 的 required status checks。

**C. 文本修订（仅指向新工具，不承载约束）**：

AGENTS.md "Verification Contract" 节追加一行：

```markdown
- Task done 判定主体不再是 AI 自述。
  唯一 done 判定器：`python scripts/verify_task_done.py --task-id <id>`（exit 0 = done，非 0 = NOT_DONE）。
  详见 R9。
```

#### 4.2.6 验收标准（命令 + exit code，无 AI 自述）

- 故意删除 `build/smoke_report.json` → `verify_task_done.py` exit 1 → driver 进入 fixer loop。
- 故意把 `build/smoke_report.json` 的 `contract_hash` 改错 → exit 1。
- 故意 `spec_coverage.coverage_rate < 1.0` → exit 1。
- 全部满足 → exit 0 → driver 允许 done。
- CI required check 列表中包含 `evidence-gate` 一项。

#### 4.2.7 为什么这么改（vs v1 替代方案）

**v1 方案"修订 AGENTS.md Verification Contract 文本"被否的原因**：
- 文本约束依赖 AI 阅读、记忆、自觉应用——本次事故就是"AI 看到了但没跑"。
- 提醒类约束的边际效用接近 0，因为 AI 已经声称"理解了"还是漏跑。

**v2 vs 替代方案**：

- vs "在 wrapup 模板里加 jq 检查"：仅在 commit 时检查，AI 可以选择性跳过 commit；driver 内部检查更靠谱。
- vs "在 superpowers skill 里加约束"：skill 也是文本约束；exit code 不是。
- vs "完全依赖 R9 evidence gate，不改 driver"：R9 只是脚本，必须由 driver / CI 调用才有效。R2 = R9 的接入点。

**核心理由**：done 判定的主体必须是机器，不是 AI。R2 不是"提醒 AI"，而是"取消 AI 的 done 自述权"。

#### 4.2.8 责任与优先级
- 优先级：**P0**（顺序 6，依赖 R9/R3/R4/R1/R10 先就绪）
- 责任：driver 工程层 + CI 工程层
- 落地阻塞：依赖 R9 已实现 `verify_task_done.py`

---

### R3：Single Source of Truth + 生成链（v2 修正根因）

> **v1 → v2 关键变化**：v1 把 R3 描述为"SPEC 完全没有机器可读源"。审核现场核对发现项目已有 `src/shared/contracts/api_routes.py` 和 `src/shared/contracts/api_routes.ts`，因此 v1 根因诊断错误。v2 修正为：**多真源 + 非生成 + 未强制消费**。解法不是"新建一个 yaml"，而是"选定唯一真源 + 把所有派生产物变成 generated + 用 R13 禁手改"。

#### 4.3.1 现场证据
- SPEC-A 路由总表是 markdown 表格（一份）。
- `src/shared/contracts/api_routes.py` 是 Python registry（第二份）。
- `src/shared/contracts/api_routes.ts` 是 TypeScript registry（第三份）。
- FastAPI runtime（main.py + routes/*.py）是事实上的第四份。
- 现场对比（§2.6）：declared rest 24 / actual registered 21 / missing 17 / double-prefix 9，证明四份之间没有任何强制对齐。
- 后端写成 `/api/projects/{id}/cost`（单数），SPEC 写的是 `/costs`（复数）；前端按 SPEC 写，测试按后端写——四份真源各自漂移。

#### 4.3.2 背景与根因（v2 修正）

**v1 错误根因**："SPEC 缺少 single source of truth 的机器可读形式"。
**v2 修正根因**：

1. **多真源**：项目已经有 4 处描述路由的地方，但没有一处被认定为唯一权威。
2. **非生成**：所有 4 份都是手工维护，互相不强约束。
3. **未强制消费**：即使 `api_routes.py` 是机器可读的，也没有任何 gate 在 runtime 层跑"declared = actual"对比；前端没有 SDK 强制消费它；smoke 不存在。
4. **markdown 不可执行**：散文形式的 SPEC-A 路由总表既不能被前后端 import，也不能被 lint 工具校验。

简言之：**registry 已经存在，但既不唯一也不被消费，等于不存在**。

#### 4.3.2.1 v2 现场对比数据

```text
normalized declared rest: 24       (api_routes.py)
normalized actual registered: 21   (FastAPI app.routes)
normalized missing: 17             (declared 但 runtime 不存在)
double-prefix suspected routes: 9  (runtime 有但被 main.py 双叠 prefix 污染)
```

这组数据是 v2 R3 的核心驱动证据：项目已经有 registry，但 runtime 层缺 17 条、多 9 条 double-prefix。任何只"新建一份 routes.yaml"而不解决"强制消费"的方案都无法阻断这种漂移。

#### 4.3.3 不改会怎样
- 每次新增 endpoint 都有概率引入命名偏差
- 每次 SPEC 修订（已经到 v3.18）都要靠人脑把 markdown 翻译成代码
- BDD 验收（SPEC-G）和 SPEC-A 之间也会出现同类裂缝（评审请验证此点）

#### 4.3.4 改什么（v2）

不是简单"新增一份 yaml"，而是**确立单一真源 + 建立完整生成链 + 用 R13 禁手改**：

1. 选定 `contracts/routes.yaml`（或 `docs/specs/routes.yaml`）作为唯一真源（single source of truth）。
2. 把所有派生产物全部变成生成物：
   - `contracts/routes.yaml` → `src/shared/contracts/api_routes.py`（**现有的手写文件改为生成**）
   - `contracts/routes.yaml` → `src/shared/contracts/api_routes.ts`（**现有的手写文件改为生成**）
   - `contracts/routes.yaml` → SPEC-A markdown 路由总表节
   - `contracts/routes.yaml` → OpenAPI route skeleton
   - `contracts/routes.yaml` → 前端 generated SDK（详见 R7）
   - `contracts/routes.yaml` → vite proxy 配置块（详见 R7）
3. 用 R13 强制 `make generate-contracts && git diff --exit-code` 检查 generated files 是否 up-to-date；任何手改 generated file 一律 CI 红。
4. 用 R5 contract test 强制 runtime `app.routes` 与 `routes.yaml` 一致。
5. 用 R8（已并入本节的 schema/style lint）控制命名风格漂移。

**关键差异**：v1 把 R3 当"新建一份 yaml"，v2 把 R3 当"建立 yaml → 派生 → 消费 → 校验 的完整闭环"。前者只解决"有没有真源"，后者解决"真源是否真正生效"。

#### 4.3.5 怎么改
**A. 新建 `docs/specs/routes.yaml`** 示例：

```yaml
version: v3.18
endpoints:
  - id: project.list
    method: GET
    path: /api/projects
    description: 列出所有项目
    request_schema: null
    response_schema: schemas/Project.list.json
    auth: required
    consumed_by_frontend: [ProjectListPage]

  - id: project.get
    method: GET
    path: /api/projects/{id}
    path_params:
      id: { type: string, format: uuid }
    response_schema: schemas/Project.detail.json
    consumed_by_frontend: [ProjectDetailPage]

  - id: project.advance
    method: POST
    path: /api/projects/{id}/advance
    request_schema: schemas/AdvanceRequest.json
    response_schema: schemas/Project.detail.json
    consumed_by_frontend: [PhaseDetail]

  # ... 共 25 条
```

**B. 校验脚本** `scripts/check_routes_yaml.py`：
- schema 校验（jsonschema）
- 路径风格校验（复数名词、kebab-case、`{id}` 而非 `:id`）
- 唯一性校验（path + method 不重复）
- ID 唯一性

**C. 把所有派生产物变成 generated**（v2 增强）：
- `scripts/gen_api_routes_py.py` 读 routes.yaml → 生成 `src/shared/contracts/api_routes.py`（替换现有手写）
- `scripts/gen_api_routes_ts.py` 读 routes.yaml → 生成 `src/shared/contracts/api_routes.ts`（替换现有手写）
- `scripts/render_spec_a.py` 读 routes.yaml → 生成 markdown 表格
- `scripts/gen_openapi_skeleton.py` 读 routes.yaml → 生成 OpenAPI 路径骨架
- `scripts/gen_frontend_sdk.ts` 读 routes.yaml → 生成 `src/frontend/src/api/generated.ts`（详见 R7）
- `scripts/gen_vite_proxy.ts` 读 routes.yaml → 生成 vite.config.ts proxy 段（详见 R7）
- 所有 generated 文件头部包含警告：`// AUTO-GENERATED FROM contracts/routes.yaml — DO NOT EDIT`
- 由 R13 强制 `make generate-contracts && git diff --exit-code` CI gate

#### 4.3.6 验收标准（v2 命令 + exit code）

- `python scripts/check_routes_yaml.py` → schema 校验 + 命名风格 lint（吸收 R8）→ exit 0
- `make generate-contracts` 后 `git diff --exit-code` → exit 0（generated files up-to-date）
- 25 个 endpoint 全部录入，与现行 FastAPI runtime `app.routes` 一致：
  - `python scripts/diff_routes_runtime.py` 报 `missing=0, double_prefix=0, unexpected=0` → exit 0
- contract test（R5）覆盖每个 endpoint
- markdown SPEC-A 路由总表节被替换为"自动生成警告 + 表格"
- 后续 R4/R5/R6/R7 都从 `contracts/routes.yaml` 读
- 故意手改 `src/shared/contracts/api_routes.py` 后跑 CI → R13 检查 exit 1

#### 4.3.7 为什么这么改

**vs 替代方案 1：直接用 OpenAPI YAML**
- 可行，但 OpenAPI 表达力过强（每个 endpoint 几十行），对 AI 生成成本高，且把"路由声明"和"schema 细节"绑在一起耦合度太高。
- routes.yaml 是 lightweight 子集，足够本场景，未来可平滑升级到 OpenAPI。

**vs 替代方案 2：保留 markdown 但加 lint**
- markdown 表格 lint 工具不成熟，且无法支撑 R7（前端 client SDK 自动生成）。
- 本质上 markdown 不是结构化数据，强行 lint 等于自造解析器，长期不划算。

**vs 替代方案 3：让后端 FastAPI 自动 export OpenAPI 作为真源**
- "代码即真源"会丢失"SPEC 先于代码"的意图。本项目流程是 SPEC-driven，不是 code-first。
- 反过来用 routes.yaml 校验 FastAPI 实际导出的 OpenAPI（见 R5）才是正确方向。

**核心理由**：把 SPEC 从"散文"升级为"合同"是 SPEC Coding 工作流的**核心基建**。R1/R4/R5/R6/R7/R8 都依赖这一份机器可读源。

#### 4.3.8 责任与优先级
- 优先级：**P0**（其他改进的依赖项）
- 责任：SPEC 工作流层
- 落地阻塞：无。但需要同步修订 SPEC-A 文档，建议与 SPEC v3.19 一同发布。

---

### R4：Harness 增加 SPEC 覆盖率维度（v2 扩展为 spec_item_coverage）

> **v1 → v2 关键变化**：v1 R4 只盯 endpoint coverage。审核指出 SPEC 不只有 endpoint（还有 BDD scenario / DB table / event type / error code / agent prompt），endpoint 只是 `item.type=api_route` 的一种。v2 把 R4 升级为通用 `spec_item_coverage`，详细落点见 R11。

#### 4.4.1 现场证据
- 当前 Harness 主指标：411 passed / 41 skipped
- 实际 SPEC-A 25 endpoint，**11 个完全没实现**
- 没实现的 endpoint 没有对应 TC，所以"没写过的东西不会失败"
- Harness 报"成功"，但产品维度严重缺失

#### 4.4.2 背景与根因
Harness 衡量的是"已写测试的通过率"，不是"SPEC 要求的覆盖率"。这是两个完全不同的指标：

- 已写测试通过率：分母是 AI 自己定义的子集
- SPEC 覆盖率：分母是产品声明的全集

当 AI 同时是"决定写哪些测试"和"执行测试"的主体时，前者会**系统性偏低估**——AI 倾向于跳过自己不确定的部分，而不是为它写 RED 测试。

**根因：Harness 缺少独立于 AI 自由度的"产品全集"分母**。

#### 4.4.3 不改会怎样
- 每次 SPEC 修订（v3.16/3.17/3.18 已经发生过多次）都可能新增 endpoint，但 AI 没补对应实现，Harness 不报警
- "411 passed" 的信号长期失真，许阳无法用它判断进度
- 最终所有 metric 都需要人工二次核对，Harness 自动化价值归零

#### 4.4.4 改什么
Harness 的"task done"判定中加入两个新指标：

- `spec_endpoint_coverage`：在 routes.yaml 中声明的 endpoint，多少个在 OpenAPI 实际暴露且 smoke 通过
- `spec_endpoint_unclaimed`：routes.yaml 中声明但代码未实现的 endpoint 列表

#### 4.4.5 怎么改
**A. 新增脚本** `scripts/spec_coverage.py`（v2 通用化结构）：

```python
# 输入：
#   contracts/spec_manifest.yaml          - SPEC 全集声明（详见 R11）
#   contracts/routes.yaml                 - 路由真源
#   http://localhost:8000/openapi.json    - 后端实际暴露
#   build/smoke_report.json               - smoke 结果
#   tests/eval/eval_report.json           - agent eval 结果
#   tests/integration/bdd_report.json     - BDD scenario 结果
# 输出：
#   build/spec_coverage.json
# {
#   "spec_items_declared": 123,
#   "spec_items_implemented": 123,
#   "spec_items_verified": 123,
#   "by_type": {
#     "api_route":     {"declared": 25, "implemented": 25, "verified": 25},
#     "bdd_scenario":  {"declared": 41, "implemented": 41, "verified": 40},
#     "db_table":      {"declared": 10, "implemented": 10, "verified": 10},
#     "event_type":    {"declared": 17, "implemented": 17, "verified": 16},
#     "error_code":    {"declared": 17, "implemented": 17, "verified": 17},
#     "agent_prompt":  {"declared": 13, "implemented": 13, "verified": 15}
#   },
#   "missing": [],
#   "stale_evidence": [],
#   "coverage_rate": 1.0
# }
```

任一 `coverage_rate < 1.0` 或 `missing != []` 或 `stale_evidence != []` → exit 1。
`stale_evidence` 检测项：报告 `generated_at` 早于 commit 时间 / `contract_hash` 与当前 yaml 不匹配。

Endpoint coverage 是其中一种 `item.type=api_route`，BDD scenario / agent eval / event type 等同样作为 SPEC 全集分母。

**B. Harness 判定升级**（HARNESS.md 修订）：

```
task done 必须同时满足：
  - tc_pass_rate == 1.0
  - spec_endpoint_coverage == 1.0
  - smoke_pass == 1.0
  - 任一指标 < 1.0 自动判定 NOT_DONE
```

**C. PROGRESS.md 与 dev log 中加入覆盖率字段**：

```
[2026-04-26] milestone-7
  tc: 411/411 (100%)
  spec_coverage: 14/25 (52%)  ← 新增，且 < 100% 时整体 NOT_DONE
  smoke: failed
  status: NOT_DONE
```

#### 4.4.6 验收标准
- 重放本次现场（411 passed + 14/25 spec coverage）→ Harness 必须判 NOT_DONE
- 修复后（25/25 spec coverage + smoke 全绿）→ Harness 判 DONE
- coverage 报告里能逐条列出 missing endpoint，AI 可基于此排期补实现

#### 4.4.7 为什么这么改

**vs 替代方案 1：靠人工对照 SPEC-A 表格**
- 现在就是这样，已被证明不可行（许阳是 product owner，不写代码，本次 AI 自己也没主动核对）。

**vs 替代方案 2：把"endpoint 实现度"用 BDD scenario 数量代替**
- BDD scenario 与 endpoint 是多对多关系，不是好的代理指标。
- BDD 自身也可能漏写场景，同样有"AI 自由度过大"问题。

**vs 替代方案 3：只在 release 阶段查覆盖率**
- 太晚。集成阶段就该报警，不然"集成阶段才发现 11 个 endpoint 没写"会反复发生。

**核心理由**：把"产品全集"作为独立分母引入 Harness，是阻断 AI 自由度系统性偏低估的唯一方法。本质上是给 AI 加一个"它无法绕过的客观标尺"。

#### 4.4.8 责任与优先级
- 优先级：**P0**
- 责任：Harness 工程层
- 落地阻塞：依赖 R3（routes.yaml）

---

### R5：测试金字塔补齐 integration / contract 层

#### 4.5.1 现场证据
- 411 个测试基本是 unit 层
- 没有任何测试做：启动真实 main.py app → httpx.get 真实路径 → 断言响应
- 因此 main.py 的双叠 prefix / 漏 include / vite proxy 缺失等装配错误**测试看不见**

#### 4.5.2 背景与根因
当前测试金字塔严重失衡：

```
当前形态：             理想形态：
                      
  [        ]             [E2E]
  [        ]            [Integration]
  [        ]           [    Unit     ]
  [  Unit  ]
```

unit 测试便宜、AI 容易写，所以 AI 倾向于把所有验证都堆在这一层。但 unit 测试**不验证装配**——而本次错漏 100% 是装配层错误。

**根因：测试金字塔失衡 + AI 倾向最低成本路径 = 装配层错误无人检查**。

#### 4.5.3 不改会怎样
- "TDD 已执行"无法保证"集成正确"
- 每次集成阶段都要靠 R1 smoke 兜底
- smoke 是粗粒度（路径存在 + 状态码正确），无法替代细粒度断言（响应字段、错误码、auth 行为）
- 复杂业务路径（FSM 跨阶段流转）的 bug 会漏到生产

#### 4.5.4 改什么
增加两层测试：

1. **Contract test**（轻、机械化）：从 routes.yaml 自动生成，每个 endpoint 至少 1 个"真启动 app + 打路径 + 断言路径存在"的测试
2. **Integration test**（中、人工 + AI 协作）：每个核心业务流（创建项目→推进阶段→查 cost）一个真启动 app + 多次调用 + 断言状态机正确转移的测试

#### 4.5.5 怎么改
**A. 新增 `tests/contract/` 目录**（v2 强约束："必须加载真实 main:app，禁止自建局部 FastAPI app"）：

```python
# tests/contract/test_routes_exist.py（自动生成）
import pytest
from fastapi.testclient import TestClient
# 关键：必须 import 真实的 main:app；任何 conftest fixture 自建局部 app 一律禁止
from src.backend.api.main import app

import yaml
routes = yaml.safe_load(open("contracts/routes.yaml"))["endpoints"]

@pytest.mark.parametrize("endpoint", routes, ids=[e["id"] for e in routes])
def test_endpoint_registered(endpoint):
    client = TestClient(app)
    method = endpoint["method"].lower()
    path = endpoint["path"].replace("{id}", "test-id-1")
    resp = getattr(client, method)(path)
    assert resp.status_code != 404, (
        f"{endpoint['id']} not registered: {method.upper()} {path}"
    )
    assert "/api/api/" not in path, "double-prefix detected"

def test_routes_diff_report():
    """生成 declared/runtime/missing/extra/mismatch 报告，用于 spec_coverage 消费。"""
    declared = {(e["method"], e["path"]) for e in routes}
    actual = set()
    for r in app.routes:
        if not hasattr(r, "methods"):
            continue
        for m in r.methods:
            if m not in {"HEAD", "OPTIONS"}:
                actual.add((m, r.path))
    report = {
        "declared": sorted(declared),
        "runtime": sorted(actual),
        "missing": sorted(declared - actual),
        "extra": sorted(actual - declared),
    }
    Path("build/contract_routes_report.json").write_text(json.dumps(report, indent=2))
    assert not report["missing"], f"declared but not in runtime: {report['missing']}"
    assert not report["extra"], f"runtime but not declared: {report['extra']}"
```

**A2. 引入 Schemathesis（v2 新增）**：基于 OpenAPI 自动生成 contract / property tests：

```bash
schemathesis run http://localhost:8000/openapi.json \
  --checks all \
  --hypothesis-max-examples 50 \
  --report build/schemathesis_report.json
```

**A3. 引入 Spectral（v2 新增）**：lint OpenAPI/YAML 风格（吸收 R8 + R3 命名规则）：

```bash
spectral lint contracts/routes.yaml --ruleset .spectral.yaml
spectral lint build/openapi.json --ruleset .spectral.yaml
```

**B. 新增 `tests/integration/` 目录**：

```python
# tests/integration/test_project_lifecycle.py
def test_create_project_and_advance():
    client = TestClient(app)
    r1 = client.post("/api/projects", json={"name": "test"})
    assert r1.status_code == 201
    pid = r1.json()["id"]
    r2 = client.post(f"/api/projects/{pid}/advance")
    assert r2.json()["state"] == "phase_2"
    # ...
```

**C. CI/Harness 把这两层与 unit 层并列**：

```bash
make test-unit        # 现有 411
make test-contract    # 新增，从 routes.yaml 自动生成
make test-integration # 新增，主要业务流
make test             # = unit + contract + integration
```

#### 4.5.6 验收标准
- contract 层覆盖 routes.yaml 中所有 endpoint（25/25）
- 重放本次现场：双叠 prefix → contract 测试报"路径不存在"或"路径重复"
- integration 层至少覆盖 3 条核心业务路径（创建项目、推进阶段、回退）
- 三层测试都接入 Harness pass-rate 报告

#### 4.5.7 为什么这么改

**vs 替代方案 1：只靠 R1 smoke**
- smoke 是黑盒、coarse-grained。无法验证"响应字段是否符合 schema"、"鉴权是否正确"。
- 必须有白盒 contract + integration 测试做细粒度断言。

**vs 替代方案 2：直接上 e2e（Playwright/Cypress）**
- e2e 慢、脆弱、维护成本高。
- contract + integration 是更高 ROI 的中间层。e2e 留给关键用户路径（如 1-2 条），而非每 endpoint。

**vs 替代方案 3：让 AI 在每个 unit 测试里也启动真实 app**
- 性能不可接受（411 个测试每次都启动 app）。
- 把"装配验证"集中在 contract 层是更合理的关注点分离。

**核心理由**：测试层级要匹配错误类型。本次错误是装配层，必须有装配层测试覆盖。这与 superpowers:test-driven-development 不冲突——TDD 仍然在每一层内部执行 RED-GREEN-REFACTOR，只是现在多了两层。

#### 4.5.8 责任与优先级
- 优先级：**P1**
- 责任：测试层（QA + AI 协作）
- 落地阻塞：依赖 R3（routes.yaml）做 contract 自动生成

---

### R6：Router 注册与 Prefix 单一来源

#### 4.6.1 现场证据
- main.py 5 处双叠 prefix（/api/system/api/system/status 等）
- 6 处装饰器风格不一致（routes/system.py 用绝对路径，routes/settings_bridge.py 用相对路径）
- preferences.py 写完了但 main.py 忘 include

#### 4.6.2 背景与根因
FastAPI 路由注册有两种风格：
- 风格 A（绝对路径）：装饰器 `@router.get("/api/system/status")`，main.py `include_router(router)`
- 风格 B（相对路径）：APIRouter `prefix="/api/system"`，装饰器 `@router.get("/status")`，main.py `include_router(router)`

混用风格 + 在 main.py 加二次 prefix → 双叠。
新增 router 文件时手动改 main.py import 列表 → 容易忘。

**根因：约定不统一 + 注册机制是手工 import**。

#### 4.6.3 不改会怎样
- 每次新加 endpoint 都有概率出现风格漂移和忘 include
- code review 必须每次重新审视 main.py 装配，浪费注意力
- 新人（或新 AI 实例）入场需要靠看现有代码学约定，约定不一致时学错的概率 50%

#### 4.6.4 改什么
1. 统一约定为风格 B（APIRouter 带 prefix + 装饰器用相对路径），与 routes/settings_bridge.py 对齐
2. main.py 改为遍历 routes/__init__.py 的导出列表，自动 include
3. 启动时 assert OpenAPI 中无 `/api/api/` 双叠子串

#### 4.6.5 怎么改
**A. 重构 routes/*.py 为统一风格**：

```python
# routes/system.py（修订）
from fastapi import APIRouter
router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")  # 相对路径
def status(): ...
```

**B. routes/__init__.py 自动收集**：

```python
# routes/__init__.py
from . import system, tasks, preferences, observability, cost, settings_bridge

ALL_ROUTERS = [
    system.router,
    tasks.router,
    preferences.router,
    observability.router,
    cost.router,
    settings_bridge.router,
]
```

**C. main.py 简化**：

```python
from src.backend.routes import ALL_ROUTERS

for r in ALL_ROUTERS:
    app.include_router(r)  # 不再加 prefix；prefix 由 router 自身声明

# 启动时自检
@app.on_event("startup")
def assert_no_double_prefix():
    paths = [r.path for r in app.routes]
    for p in paths:
        assert "/api/api/" not in p, f"Double prefix detected: {p}"
```

**D. 新增 `scripts/lint_fastapi_routes.py`**（v2 强化为独立 AST lint 脚本，不依赖 ruff 自定义规则）：

```python
# scripts/lint_fastapi_routes.py
# 三类硬约束（任一命中 exit 1）：
# 1. 禁止 include_router(..., prefix=...)   -- prefix 必须由 router 自身声明
# 2. 禁止 router decorator 使用绝对 /api/... 路径
#    （除非 router 本身无 prefix 且被 contracts/routes.yaml 显式 allowlist 豁免）
# 3. 禁止 runtime 出现 /api/api/ 或 /api/<seg>/api/ double-prefix pattern
#
# 输出：build/lint_fastapi_routes.json
# {
#   "violations": [
#     {"file": "src/backend/api/main.py", "line": 42,
#      "rule": "no_prefix_in_include_router",
#      "snippet": "app.include_router(system.router, prefix='/api/system')"}
#   ]
# }

import ast, json, re, sys
from pathlib import Path

VIOLATIONS = []

class IncludeRouterVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        if (isinstance(node.func, ast.Attribute)
                and node.func.attr == "include_router"):
            for kw in node.keywords:
                if kw.arg == "prefix":
                    VIOLATIONS.append({
                        "rule": "no_prefix_in_include_router",
                        "line": node.lineno,
                    })
        self.generic_visit(node)

# ... 启动时 assert + AST lint + contract diff 三者合用
```

启动期 assert（`main.py`）+ AST lint（CI required） + contract diff（R5）三层合用，单层失效不会让 double-prefix 漏出。

#### 4.6.6 验收标准
- main.py 的 include_router 调用全部不带 prefix
- 启动时 OpenAPI 无 `/api/api/` 子串
- 故意把某个 router 从 ALL_ROUTERS 移除 → contract 测试（R5）报"endpoint 缺失"

#### 4.6.7 为什么这么改

**vs 替代方案 1：保持双 prefix 风格但加文档**
- 文档驱动失败已有先例（SPEC 是散文也是文档驱动，结果 64% 错漏）
- 必须用代码层面的强约束。

**vs 替代方案 2：走 Pyramid/Flask blueprint 风格**
- 项目已选 FastAPI，重构框架不在 ROI 范围。

**vs 替代方案 3：完全自动扫描 routes/*.py 而不维护 __init__.py**
- 隐式注册的可读性差，AI 在调试时容易迷失。
- __init__.py 显式列表是最小成本的"显式 + 集中"。

**核心理由**：用代码结构本身阻断错误的可能性，而不是用 review 兜底。

#### 4.6.8 责任与优先级
- 优先级：**P1**
- 责任：实施层（代码重构 + 启动期 assert）
- 落地阻塞：无，但建议与 R5 同期完成（contract 测试覆盖才能验证不回归）

---

### R7：前端 API URL 自动生成（禁止手写）

#### 4.7.1 现场证据
- 前端 fetch 路径手写
- vite.config.ts 没配 dev proxy → /api/* 全部走 SPA 兜底
- 前端调用的 `/costs`（复数，按 SPEC）和后端实现的 `/cost`（单数）不一致

#### 4.7.2 背景与根因
前端开发者（或 AI）从 SPEC-A markdown 里手抄路径到 fetch 调用，这步翻译是无校验的。两次手抄就有 2 次出错机会（前端一次、后端一次）。

vite proxy 配置是另一个独立的人肉环节，没人写就没有。

**根因：前后端契约是"两端各抄一遍"，没有共享真源**。

#### 4.7.3 不改会怎样
- 每次 SPEC 修订都要前后端各自手改，对不上的概率持续存在
- 前端 dev 启动后路径访问失败的故障会重复出现
- 前后端独立演化，越走越偏

#### 4.7.4 改什么
1. 从 routes.yaml 生成 TypeScript API client SDK
2. 前端禁止直接 `fetch('/api/...')`，必须经 SDK
3. vite.config.ts 的 proxy 也从 routes.yaml 生成

#### 4.7.5 怎么改
**A. 新增 `scripts/gen_frontend_client.ts`**：

```ts
// 输入: docs/specs/routes.yaml
// 输出: src/frontend/src/api/generated.ts

export const apiClient = {
  project: {
    list: () => fetch('/api/projects').then(r => r.json()),
    get: (id: string) => fetch(`/api/projects/${id}`).then(r => r.json()),
    advance: (id: string) =>
      fetch(`/api/projects/${id}/advance`, { method: 'POST' }).then(r => r.json()),
    // ... 25 条
  },
};
```

**B. ESLint 规则**（v2 强化：禁止业务代码出现任何 `/api/` 字面量，不仅是裸 fetch）：

> v1 只禁 `fetch('/api/...')`，但项目已有 `apiClient.get(path)` 这种 generic wrapper，AI 仍可写 `apiClient.get('/api/projects')` 绕过。v2 直接禁所有 `/api/` 字符串字面量。

```json
// .eslintrc.json
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "Literal[value=/^\\/api(\\/|$)/]",
        "message": "Hard-coded /api path forbidden. Use generated SDK: api.project.list() / api.project.get(id)."
      },
      {
        "selector": "TemplateLiteral > TemplateElement[value.raw=/\\/api(\\/|$)/]",
        "message": "Hard-coded /api template literal forbidden. Use generated SDK."
      }
    ]
  },
  "overrides": [
    {
      "files": [
        "src/frontend/src/api/generated.ts",
        "src/frontend/src/api/__fixtures__/**",
        "tests/contract/**"
      ],
      "rules": { "no-restricted-syntax": "off" }
    }
  ]
}
```

**B2. 后端侧禁裸 path（防双向漂移）**：`scripts/lint_no_hardcoded_api_path.py` 扫描 `src/backend/api/main.py` 之外的代码不允许出现 `"/api/"` 字面量（`main.py` include_router 由 R6 lint 控制）。

**B3. 前端 SDK 调用风格强制为命名空间**：

```ts
// 禁止：
apiClient.get('/api/projects');
fetch('/api/projects');

// 允许：
api.project.list();
api.project.get(id);
api.project.advance(id);
```

理由：generated SDK 把"路径字符串"封装成方法名，路径变更时编译期报错；裸 path 调用在 runtime 才暴露。

**C. vite.config.ts 自动生成**：

```ts
// scripts/gen_vite_proxy.ts
// 读 routes.yaml，生成 vite.config.ts 的 server.proxy 段
proxy: {
  '/api': { target: 'http://localhost:8000', changeOrigin: true },
  '/ws': { target: 'ws://localhost:8000', ws: true },
}
```

**D. 提交前 hook**：routes.yaml 改动 → 强制重生成 generated.ts 和 vite.config.ts。

#### 4.7.6 验收标准
- 前端代码搜索 `fetch('/api/` 仅在 generated.ts 内出现
- 修改 routes.yaml 中某 endpoint 路径 → 重新生成后前端编译报错（如果引用了旧名字）
- vite dev 启动后所有 /api/* 路径正常代理到后端

#### 4.7.7 为什么这么改

**vs 替代方案 1：用 OpenAPI codegen（openapi-typescript）**
- 工具更重，且需要先有完整 OpenAPI YAML（而 routes.yaml 是更轻量的子集）
- 未来 routes.yaml 升级到 OpenAPI 时可平滑切换

**vs 替代方案 2：手动维护 frontend/api.ts，但加 lint 校验**
- 校验难度等同 R3 的"markdown 表格 lint"，不可行

**vs 替代方案 3：完全靠 contract 测试（R5）兜底**
- contract 测试只能在 CI 中发现错误，开发期间前端开发者已经写完一堆错误代码
- 在源头堵漏（自动生成）成本更低

**核心理由**：契约不应该被手抄两遍。代码生成是最稳的去重手段。

#### 4.7.8 责任与优先级
- 优先级：**P1**
- 责任：前端工具链 + SPEC 工作流
- 落地阻塞：依赖 R3

---

### R8：路径命名风格 lint（v2 已并入 R3 / R5 Spectral）

> **v1 → v2 关键变化**：审核指出 R8 不应作为独立高优先级工程项，应并入 R3 schema/style lint。v2 R8 降级为 P2，作用域为"长期风格收敛"，命令落点改为 Spectral 规则集（见 R5）。下文保留供历史参考，落地时不单独立项，与 R3/R5 同期实现。

#### 4.8.1 现场证据
- `/api/projects/{id}/cost` vs SPEC `/costs`：单复数不一致
- 装饰器 6 处风格不一致（已在 R6 处理）
- 假设其他 endpoint 也可能有 `userInfo` vs `user-info` 等大小写/连字符差异

#### 4.8.2 背景与根因
路径命名约定（kebab-case、复数名词、{id} 占位符）是 SPEC 心照不宣的规则，没有写在 SPEC 里，也没有任何机器校验。

**根因：约定靠默契，不靠 lint**。

#### 4.8.3 不改会怎样
- 风格漂移会随时间累积
- 老 endpoint 单数 + 新 endpoint 复数 → 前端开发者每次都要查一下，认知负担持续增加
- 重构时一致性降级风险高

#### 4.8.4 改什么
为 routes.yaml 增加一个 schema 校验脚本，覆盖路径命名规则。

#### 4.8.5 怎么改
**A. `scripts/check_routes_naming.py`**：

```python
import re

PATH_RULES = [
    # kebab-case，禁止 camelCase 和 snake_case
    (r'/[a-z]+([A-Z]|_)', "use kebab-case"),
    # 资源用复数名词
    # 通过白名单/黑名单维护例外
    # {id} 占位符格式统一
    (r'\{[a-z_]+\}', None),  # 必须匹配
]

def check(endpoint):
    path = endpoint["path"]
    # ...
```

**B. 接入 R3 的 routes.yaml 校验流程**：
- 任何不符规则的 endpoint → CI 红
- 已有的不符规则 endpoint 列入 `routes.yaml.legacy_exceptions` 白名单（暂时豁免，但禁止新增）

#### 4.8.6 验收标准
- 故意把某个 endpoint 改成 `/api/projectInfo` → CI 红
- 现有 25 endpoint 全部符合规则，或被显式列入豁免列表

#### 4.8.7 为什么这么改

**vs 替代方案 1：写在 SPEC 里靠 review 检查**
- 已经验证不可行（SPEC-A 是 markdown，靠 review 漏了 1 处）

**vs 替代方案 2：用 OpenAPI 的现有 linter（spectral）**
- 可行，但当前项目还没用 OpenAPI YAML
- routes.yaml 阶段先用轻量自检，未来切到 OpenAPI 时换 spectral

**核心理由**：风格一致性是 CI 该管的事，不该让 AI 每次靠记忆维持。

#### 4.8.8 责任与优先级
- 优先级：**P2**（不阻断本次故障，但防长期漂移；v2 已并入 R3 + R5 Spectral）
- 责任：SPEC 工作流层
- 落地阻塞：依赖 R3

---

### R9：Task Done Evidence Gate（v2 新增）

#### 4.9.1 现场证据
- §2.7 现场核对：driver `verifier` 阶段只跑 task card 的 `verification_commands`，没有任何全局 hard gate。
- §2.6 现场核对：411 passed pytest + 24/21/17/9 路由不一致同时存在，证明任务级测试通过 ≠ 全局合同满足。
- AI 在 wrapup 自述"已完成"时，没有任何工具会因为 evidence 缺失或过期而 exit 1。

#### 4.9.2 背景与根因
done 判定的主体长期是 AI 自身，导致：
1. AI 在符号空间通过验证的能力 + 倾向最低成本路径 → 系统性偏低估。
2. AGENTS.md 哲学（Business-Complete）没有任何工具承载。
3. 多份 evidence 散落各处（smoke / coverage / openapi diff / contract test），缺少统一聚合判定。

**根因**：缺少"以机器证据为唯一输入、以 exit code 为唯一输出"的统一 done 判定器。

#### 4.9.3 不改会怎样
- driver / CI 永远把"局部测试 PASS"当 done。
- AGENTS.md 哲学持续被理解但不执行。
- 与 R2 形成死锁：R2 想让 driver 调 done 判定，但没有判定器可调。

#### 4.9.4 改什么
新增 `scripts/verify_task_done.py`，作为整个项目的**唯一 done 判定器**。所有 driver / CI / wrapup hook 都必须调用它，不允许任何其他途径声明 done。

#### 4.9.5 怎么改

```bash
python scripts/verify_task_done.py --task-id SPEC-X-NNN
```

读取并验证以下 artifact（缺失 / 过期 / hash 不匹配 / 覆盖率不足任一项 → exit 1）：

| Artifact | 来源 | 检查 |
|---|---|---|
| `.verify/<task_id>.json` | task verifier 产物 | 存在 + status=pass |
| `build/spec_coverage.json` | R4/R11 | `coverage_rate==1.0` + `missing==[]` + `stale_evidence==[]` |
| `build/smoke_report.json` | R1 | `endpoints_fail==[]` + `contract_hash` 与当前 yaml 匹配 + 时间戳 ≥ 本次 commit |
| `build/openapi_diff.json` | R5 | `breaking_changes==[]` + `unexpected_routes==[]` |
| `build/contract_routes_report.json` | R5 | `missing==[] + extra==[]` |
| `build/lint_fastapi_routes.json` | R6 | `violations==[]` |
| `build/frontend_contract_report.json` | R7 | `hardcoded_api_paths==[]` |
| generated artifacts freshness metadata | R13 | `make generate-contracts && git diff --exit-code` 干净 |

输出：

```json
{
  "task_id": "SPEC-X-NNN",
  "decision": "done|not_done",
  "checks": {
    "spec_coverage": "pass",
    "smoke": "pass",
    "openapi_diff": "pass",
    "contract_routes": "pass",
    "lint_fastapi_routes": "pass",
    "frontend_contract": "pass",
    "generated_artifacts": "pass"
  },
  "failures": [],
  "evidence_freshness_ok": true
}
```

#### 4.9.6 验收标准（命令 + exit code）
- 缺少 `build/smoke_report.json` → exit 1
- `spec_coverage.coverage_rate < 1.0` → exit 1
- `generated_artifacts.stale != []` → exit 1
- `build/smoke_report.json` 时间戳早于本次 commit → exit 1（防复用旧报告）
- `contract_hash` 不匹配当前 `contracts/routes.yaml` → exit 1
- 全部满足 → exit 0

#### 4.9.7 为什么这么改
- vs "在 driver 里写 if/else 直接判断"：判定逻辑必须独立于 driver，便于 CI / wrapup hook 共享。
- vs "每个 evidence 各自 exit code"：聚合判定能给出统一报告，方便 fixer loop 识别问题点。
- vs "AI wrapup 自述贴证据"：把判定主体从 AI 换成机器是 v2 的核心命题。

#### 4.9.8 责任与优先级
- 优先级：**P0**（顺序 1，所有其他 P0 都依赖它就绪）
- 责任：工程层（脚本）
- 落地阻塞：依赖 R3 / R4 / R1 的 evidence 文件结构定型

---

### R10：Fault Injection Gate Test（v2 新增）

#### 4.10.1 现场证据
- 当前没有任何机制证明 R1/R5/R6/R7 的 gate 真能抓住已知错误类型。
- 本次事故后哪怕实施了 R1-R8，也无法保证下一次类似事故被捕获——因为"gate 写了但写错了"是常见失败模式。

#### 4.10.2 背景与根因
**根因**：检查器本身缺少检查器（mutation test / fault injection）。

#### 4.10.3 不改会怎样
- 实施了一堆 gate，但 gate 本身可能是 dead code 或 false positive 容忍度过高。
- 下次同类事故复发时才发现某个 gate 写错了。

#### 4.10.4 改什么
新增 `scripts/fault_injection_check.py`，定期注入已知错误，确认对应 gate 能红。

#### 4.10.5 怎么改

```bash
python scripts/fault_injection_check.py
```

注入用例集（v2 起点，需持续扩展）：

| ID | 注入操作 | 期望 fail 的 gate |
|---|---|---|
| FI-01 | 删除一个 router include | R5 contract test + R1 smoke |
| FI-02 | 在 main.py 给某 router 加 `prefix=` 制造 double prefix | R6 lint + R1 smoke |
| FI-03 | 把 `/costs` 改成 `/cost` | R5 contract test + R1 smoke |
| FI-04 | 在前端业务代码写裸 `/api/projects` | R7 ESLint |
| FI-05 | 删除 vite proxy block | R1 frontend proxy check |
| FI-06 | 删除某 endpoint 的 `response_model` | Schemathesis schema check |
| FI-07 | 手改 `src/shared/contracts/api_routes.py` | R13 `git diff --exit-code` |
| FI-08 | 把 `build/smoke_report.json` 时间戳改为昨天 | R9 stale_evidence 检测 |
| FI-09 | 把 `contract_hash` 改错 | R9 hash 不匹配检测 |
| FI-10 | 在 BDD 列表删除一个 scenario | R11 spec_item_coverage |

执行流程：
1. 在临时分支应用注入
2. 跑对应 gate
3. 期望 exit != 0；若 exit == 0，则该 gate 不合格
4. 回滚注入

任一注入未被对应 gate 捕获 → R10 exit 1，判定 gate 体系不合格。

#### 4.10.6 验收标准
- 全部注入用例都被对应 gate 捕获 → exit 0
- 任一未被捕获 → exit 1，并在 `build/fault_injection_report.json` 标记 `unguarded`
- CI 在每周定时跑一次 + 任意 gate 脚本变更时触发

#### 4.10.7 为什么这么改
- vs "靠人脑保证 gate 写对"：人脑保证是 v1 的失败模式。
- vs "每次事故后追加 gate"：被动模式；R10 是主动模式，能提前发现 dead gate。
- vs "100% mutation testing"：成本过高；R10 只覆盖已知事故模式 + 周期性扩展。

#### 4.10.8 责任与优先级
- 优先级：**P0**（顺序 5，必须在 R2 driver 接入前实现）
- 责任：QA 工程层
- 落地阻塞：依赖 R1/R5/R6/R7/R9/R13 各 gate 已就绪

---

### R11：SPEC Item Manifest（v2 新增；R4 的通用化落地）

#### 4.11.1 现场证据
- v1 R4 只盯 endpoint coverage，但 SPEC 还包含：
  - SPEC-A SPEC-1B：10 张 DB 表
  - SPEC-A SPEC-11A：17 个 event types
  - SPEC-A SPEC-13A：17 个 error codes
  - SPEC-D：12 phase
  - SPEC-G：BDD 验收 scenario
  - 各 agent prompt（src/backend/agents/）
- 当前没有任何机制保证这些非 endpoint 的 SPEC item 也被实现 + 验证。

#### 4.11.2 背景与根因
**根因**：Harness 分母是"已写测试 + endpoint"，不是"产品合同全集"。即使 R4 endpoint coverage 100%，BDD scenario / event type / error code 缺失仍会让 Harness 假绿。

#### 4.11.3 不改会怎样
- 修复 R4 后下次事故换个维度复发（比如某个 event type 没实现，FSM 卡住）。
- Harness 信号永远只覆盖 endpoint 维度。

#### 4.11.4 改什么
新增 `contracts/spec_manifest.yaml`，作为所有 SPEC item 的统一登记簿，drives `spec_coverage.json`。

#### 4.11.5 怎么改

```yaml
# contracts/spec_manifest.yaml
version: v3.18
spec_items:
  - id: SPEC-A-ROUTE-project.costs
    type: api_route
    source_doc: docs/specs/SPEC-A-contracts.md
    contract_ref: contracts/routes.yaml#project.costs
    required_gates:
      - route_registered
      - smoke_http
      - response_schema
      - frontend_consumer_or_explicit_none

  - id: SPEC-A-DB-projects
    type: db_table
    source_doc: docs/specs/SPEC-A-contracts.md#SPEC-1B
    contract_ref: src/shared/schemas/db/projects.json
    required_gates:
      - migration_applied
      - schema_diff_clean

  - id: SPEC-A-EVENT-phase.advanced
    type: event_type
    source_doc: docs/specs/SPEC-A-contracts.md#SPEC-11A
    contract_ref: src/shared/schemas/events/phase_advanced.json
    required_gates:
      - emitter_exists
      - subscriber_exists
      - schema_validated

  - id: SPEC-G-BDD-create-project-and-advance
    type: bdd_scenario
    source_doc: docs/specs/SPEC-G-bdd-acceptance.md
    contract_ref: tests/integration/features/project_lifecycle.feature
    required_gates:
      - scenario_passes
```

`spec_coverage.py` 读 manifest，对每个 item 检查 `required_gates` 是否全部通过。

#### 4.11.6 验收标准
- `python scripts/spec_coverage.py` 输出 `build/spec_coverage.json`，所有 SPEC 维度 coverage_rate==1.0 → exit 0
- 故意从 manifest 删除一个 BDD scenario id 但不删测试文件 → R11 报 `extra_implementation`
- 故意在 manifest 加一个未实现的 event_type → R11 报 `missing_implementation` + exit 1

#### 4.11.7 为什么这么改
- vs "只看 endpoint coverage"：维度太窄，本次只是 endpoint 暴露，下次可能在 event / DB 维度暴露。
- vs "在每个 SPEC 文档里嵌入 yaml frontmatter"：散布在 7 份 SPEC 里难维护，集中到 manifest 更清晰。
- vs "靠 BDD scenario 数量当代理指标"：BDD 自身可能漏写，需要独立的"产品全集"声明。

#### 4.11.8 责任与优先级
- 优先级：**P0**（顺序 3，与 R4 同期落地）
- 责任：SPEC 工作流层
- 落地阻塞：依赖 R3（routes.yaml 先就位作为 contract_ref 的一种）

---

### R12：Impact-Based Required Gates（v2 新增）

#### 4.12.1 现场证据
- §2.7 现场核对：CI required check 当前只跑 unit + tsc + frontend test，与本次事故的根因（装配层）完全错位。
- 全量跑所有 gate 成本过高（cold-start smoke 每次几分钟），但小改动（如改文档）跑全集是浪费。

#### 4.12.2 背景与根因
**根因**：CI gate 与变更类型解耦，导致要么覆盖不足（当前），要么过度（如果一刀切全跑）。

#### 4.12.3 改什么
按变更文件路径决定 PR 必跑哪些 gate。

#### 4.12.4 怎么改

```yaml
# .github/workflows/ci.yml 规则矩阵
gate_matrix:
  - paths: ["src/backend/api/**", "src/backend/routes/**"]
    required:
      - contract_routes_test  # R5
      - openapi_diff
      - smoke_cold_start      # R1
      - lint_fastapi_routes   # R6

  - paths: ["src/frontend/**"]
    required:
      - frontend_contract_check  # R7
      - frontend_no_raw_api_path # R7
      - frontend_build

  - paths: ["docker-compose*.yml", "Dockerfile*", "vite.config.ts"]
    required:
      - smoke_cold_start

  - paths: ["contracts/**"]
    required:
      - schema_lint            # R3
      - generated_artifacts_up_to_date  # R13
      - spec_coverage          # R4/R11

  - paths: ["docs/specs/**"]
    required:
      - spec_manifest_sync     # R11
      - generated_markdown_sync

  - paths: ["src/backend/agents/**", "config/prompts/**"]
    required:
      - eval_regression        # 已存在，§10.3
```

PR 命中任一规则 → 对应 gate 必跑且 required；最终 evidence-gate (R9) 聚合。

#### 4.12.5 验收标准
- 修改 `src/backend/api/main.py` → CI required check 包含 contract_routes / smoke / lint_fastapi_routes
- 仅修改 `README.md` → CI 只跑必要的快速检查
- 矩阵规则本身写在 `.github/required-gates.yaml`，CI 读它生成 required check 列表

#### 4.12.6 为什么这么改
- vs "全部 PR 都跑全集"：cold-start smoke 跑全集会让 CI 时间膨胀，开发者倾向跳过。
- vs "PR 作者自己选择跑哪些 gate"：无约束力，本次事故就是漏跑。
- vs "nightly 跑全集"：太晚，PR 合并后才发现问题。

#### 4.12.7 责任与优先级
- 优先级：**P1**（顺序 10）
- 责任：CI 工程层
- 落地阻塞：依赖 R1/R5/R6/R7/R9/R13 的 gate 命令已就绪

---

### R13：Generated Files 禁手改（v2 新增）

#### 4.13.1 现场证据
- §2.6 现场核对：`src/shared/contracts/api_routes.py` 是手工维护的，已经与 runtime 漂移（declared 24 / actual 21）。
- 任何"手写 + 生成"并行模式的最终结局都是漂移。

#### 4.13.2 背景与根因
**根因**：当文件既能手改也能被生成时，手改一定会发生（包括"先手改、忘 regen"和"故意保留某个手改"）。

#### 4.13.3 改什么
1. 所有 generated 文件头部强制警告标记。
2. CI 跑 `make generate-contracts && git diff --exit-code`；任何 diff 非空 → exit 1。
3. 提供清晰的"改 yaml → 重新生成"流程。

#### 4.13.4 怎么改

如果选 `contracts/routes.yaml` 作为真源，以下文件必须全部由脚本生成：

- `src/shared/contracts/api_routes.py`
- `src/shared/contracts/api_routes.ts`
- `docs/specs/SPEC-A-contracts.md` 的路由总表节
- `build/openapi_skeleton.yaml`
- `src/frontend/src/api/generated.ts`
- `src/frontend/vite.config.ts` 的 proxy 段

每个 generated 文件头部：

```python
# AUTO-GENERATED FROM contracts/routes.yaml
# DO NOT EDIT BY HAND. Run `make generate-contracts` after modifying the yaml.
# Source SHA: <yaml content sha256>
# Generator version: <generator script sha256>
```

CI 检查：

```bash
make generate-contracts
git diff --exit-code  # 如果非空 → 有人手改了 generated file 或忘记跑 generator
```

#### 4.13.5 验收标准
- 故意手改 `src/shared/contracts/api_routes.py` 提交 → CI exit 1
- 修改 `contracts/routes.yaml` 后忘跑 `make generate-contracts` → CI exit 1
- 修改 yaml 后跑 generator 后 commit → CI 通过

#### 4.13.6 为什么这么改
- vs "靠 code review 阻止手改"：人工 review 不可靠。
- vs "用 .gitattributes linguist-generated"：只影响显示，不阻断。
- vs "把 generated files 加入 .gitignore"：会让前端 / 后端开发者本地缺文件，不可行。

#### 4.13.7 责任与优先级
- 优先级：**P1**（顺序 11，与 R3 同期落地）
- 责任：CI + 工程层
- 落地阻塞：依赖 R3 选定真源 + generator 脚本就绪

---

### R14：禁用正常流程里的 `--no-verify`（v2 新增）

#### 4.14.1 现场证据
- `scripts/run_task_driver.py` 当前支持 `--no-verify` 参数；HARNESS.md §7.2 明确禁止 `git commit --no-verify`，但脚本层面没强制。
- AI 在被 verifier 卡住时，最低成本路径是绕过 verifier。

#### 4.14.2 背景与根因
**根因**：任何"调试用的逃生口"在自动驾驶 / CI 场景下都会被滥用。

#### 4.14.3 改什么
对 `--no-verify` 加环境变量门禁，并把 wrapup 状态强制标记为非 done。

#### 4.14.4 怎么改

```python
# scripts/run_task_driver.py
if args.no_verify and os.environ.get("AVS_UNSAFE_ALLOW_NO_VERIFY") != "1":
    print("ERROR: --no-verify requires AVS_UNSAFE_ALLOW_NO_VERIFY=1 (debug only).")
    sys.exit(2)

if args.no_verify:
    wrapup_status = "NOT_DONE_DEBUG_ONLY"
    # 不写入 PROGRESS.md / 不允许 evidence_gate 通过
```

CI 环境变量列表中禁止设置 `AVS_UNSAFE_ALLOW_NO_VERIFY`。

#### 4.14.5 验收标准
- `python scripts/run_task_driver.py --no-verify` → exit 2（无环境变量）
- `AVS_UNSAFE_ALLOW_NO_VERIFY=1 python scripts/run_task_driver.py --no-verify` → 允许运行但 wrapup 标记 `NOT_DONE_DEBUG_ONLY`
- CI 中即使有 commit 带 NOT_DONE_DEBUG_ONLY 标记 → R9 evidence_gate 检查到该标记 → exit 1

#### 4.14.6 为什么这么改
- vs "完全删除 --no-verify"：本地调试场景确实需要绕过 long-running gate；完全禁掉会逼 AI 去改 verifier 代码。
- vs "在文档里说不要用 --no-verify"：文档约束已被验证不可靠（HARNESS.md §7.2 已经禁止 `git commit --no-verify`，本次事故仍发生）。

#### 4.14.7 责任与优先级
- 优先级：**P1**（顺序 12）
- 责任：driver 工程层
- 落地阻塞：无

---

## 5. 改进项依赖图（v2 重画）

```text
contracts/routes.yaml   contracts/spec_manifest.yaml   (R3 + R11)
        |                       |
        v                       v
   make generate-contracts  (R13: generated artifacts up-to-date check)
        |
   +----+----+--------------+----------------+----------------+
   v         v              v                v                v
api_routes.py  api_routes.ts  SPEC-A md  OpenAPI skeleton  frontend SDK
   |          |              |                              |
   |          v              |                              v
   |   no raw /api lint     |                       Schemathesis / Spectral
   |       (R7)             |                              (R5)
   |                        |                              |
   v                        v                              v
FastAPI runtime app  ----> contract_routes_test (R5) -> contract_routes_report.json
   |                                |
   v                                v
lint_fastapi_routes (R6)     spec_coverage.py (R4 + R11) -> spec_coverage.json
   |                                |
   +----------+---------+-----------+
              |         |
              v         v
       smoke_cold_start.sh (R1)  -> smoke_report.json
                |
                v
      verify_task_done.py (R9) <--- fault_injection_check.py (R10) (周期验证 gate 有效)
                |
                v
   run_task_driver.py verifier 后调用 (R2)
                |
        exit != 0 ? --yes--> fixer loop --> 重跑 verifier + R9
                |
                no
                v
        DONE 才允许写入 PROGRESS.md 一行
```

关键变化（vs v1）：
1. **所有合同派生产物必须 generated**，不能手工同步（R13）。
2. **所有验证结果必须成为 artifact**（json with hash + timestamp），便于 R9 聚合判定。
3. **`verify_task_done.py` 是唯一 done gate**，不存在第二条声明 done 的路径。
4. **driver 负责打回修复**，不让 AI 在 wrapup 自述。
5. **R10 fault injection 周期性验证 gate 本身**，防止 dead gate。

### 5.1 落地建议顺序（v2）

- **第 1 周**：R3（contracts/routes.yaml + 生成链）+ R13（禁手改 CI）+ R11（spec_manifest.yaml）—— 真源与全集
- **第 2 周**：R4（spec_coverage）+ R1（smoke + hash metadata）+ R6（lint_fastapi_routes）—— 各 gate 命令
- **第 3 周**：R5（contract test 加载真实 app + Schemathesis/Spectral）+ R7（generated SDK + ban /api 字面量）—— 装配与前端
- **第 4 周**：R9（verify_task_done.py 聚合）+ R10（fault injection）—— 统一 done 判定 + gate 自验
- **第 5 周**：R2（driver 接入 R9）+ R12（CI Impact-Based required gates）+ R14（禁 --no-verify）—— 接入 driver / CI
- **第 6 周**：全量回归 + R10 注入用例集扩展 + Spectral 规则集完善

总周期约 6 周；其中 R3/R13/R11/R9 是关键路径，其他可并行。

---

## 6. 这次复盘的元教训（v2 重写，写进 memory）

> **TC PASS 只是"已写测试通过"，不是"SPEC 完成"。**
>
> **Task Done = SPEC 全集覆盖率 100% + 必需 runtime gates 通过 + 用户路径证据可复现。**
>
> AI 驱动开发的真正风险，不是 AI 不懂规则，而是 AI 可以选择低成本验证路径绕过真实世界。因此完成定义必须由 Harness 读取机器证据判定，而不是由 AI 在 wrapup 中自述。

三段式准确性来源：

1. **区分"测试通过率"和"SPEC 覆盖率"**：前者分母由 AI 自定义（系统性偏低估），后者分母由 SPEC 全集硬性给出（AI 无法影响）。本次事故 = 411/411 测试通过 + 14/25 endpoint 实现 + 全部 endpoint 在 runtime 漂移。
2. **"用户路径走通"必须具体化为 runtime gates 与可复现证据**：cold-start smoke / contract diff / openapi diff / frontend SDK consumer，每一条都必须有 artifact + hash + timestamp，AI 无法用自然语言"声称"。
3. **Done 判定的主体必须是 Harness，不是 AI**：这是 v2 与 v1 最根本的差异。v1 把"加强约束"理解为"加强提醒 AI"，v2 把"加强约束"理解为"取消 AI 的 done 自述权"。

### 6.1 v2 配套元教训（同时写进 memory）

- **任何"既能手改也能被生成"的文件，最终都会漂移**。Generator + `git diff --exit-code` 是唯一可靠模式。
- **任何 gate 都需要被 mutation test / fault injection 周期验证**，否则会出现"gate 写了但抓不到对应错误"的 dead gate。
- **检查器自身需要检查器**：规则不只针对业务代码，也针对工程基础设施。
- **所有"逃生口"在自动驾驶 / CI 场景下都会被滥用**：`--no-verify` / wrapup 自述 / "等下补测试"，如果不在工具层强制，AI 一定会走捷径。
- **多真源就是无真源**：项目已有 `api_routes.py/ts` 没能阻止本次事故，因为它们既不唯一也不被消费。"有"和"被强制消费"是两件事。

---

## 7. SPEC 写法结构（v2 新增）

以后 SPEC 不应只写自然语言验收标准。每个可实现条目必须有以下结构，确保 AI 在 task / test / implementation / evidence 各阶段都能稳定引用同一 ID。

### 7.1 稳定 ID

```yaml
id: SPEC-A-ROUTE-project.costs
```

要求：
- ID 不随章节标题、文档行号变化。
- task card / test / implementation / evidence 都引用这个 ID。
- ID 一旦发布不允许重命名；废弃用 `deprecated: true` 标记，新 ID 替代。

### 7.2 机器合同（API 条目示例）

```yaml
id: SPEC-A-ROUTE-project.costs
type: api_route
method: GET
path: /api/projects/{id}/costs
path_params:
  id:
    type: string
    format: uuid
response_schema: CostsResponse
allowed_status: [200, 401, 404, 422]
frontend_consumers:
  - CostPanel
```

### 7.3 验证映射

```yaml
required_gates:
  - route_registered
  - openapi_matches_contract
  - smoke_http_not_404
  - response_schema_conformance
  - frontend_sdk_usage
```

每个 `required_gate` 对应一个 `scripts/check_<gate>.py`，由 R9 evidence gate 聚合判定。

### 7.4 测试夹具 / 最小样例

```yaml
fixtures:
  path_params:
    id: demo_project_001
  seed:
    - scripts/seed_dev_db.py --scenario project_with_costs
```

没有 fixture 的 endpoint，smoke 只能验证"不 404"，不能验证业务正确性。因此 SPEC 必须声明最小可运行样例，让 R1 smoke 能跑出真实业务响应。

### 7.5 非 endpoint 类条目示例

```yaml
- id: SPEC-A-EVENT-phase.advanced
  type: event_type
  emitter: src/backend/engine/workflow_engine.py
  subscriber_examples:
    - src/backend/services/notifier.py
  schema_ref: src/shared/schemas/events/phase_advanced.json
  required_gates:
    - emitter_exists
    - schema_validated
    - subscriber_exists

- id: SPEC-G-BDD-create-and-advance
  type: bdd_scenario
  feature_file: tests/integration/features/project_lifecycle.feature
  required_gates:
    - scenario_passes
```

### 7.6 与 R3/R11 的关系

- R3 解决 `type=api_route` 这一种条目的 single source + 生成链。
- R11 解决其他条目类型（db_table / event_type / error_code / bdd_scenario / agent_prompt）的统一登记。
- 二者共享同一种结构（id / contract_ref / required_gates / fixtures），只是分母不同。

---

## 8. 复盘文档放行条件清单（v2 自检）

审核 §9 列出 10 条放行条件。本节是 v2 自检对照，每一条标记是否完成。

| # | 放行条件 | v2 状态 | 落点 |
|---:|---|:---:|---|
| 1 | 把 R2 从"修订 Verification Contract 文本"改为"修改 driver/verifier/CI 硬 gate" | ✅ | §4.2 已重写 |
| 2 | 修正 R3 根因：项目已有 `api_routes.py/ts`，真问题是多真源/非生成/未强制消费 | ✅ | §4.3.2 已修正 |
| 3 | 新增 R9：Task Done Evidence Gate | ✅ | §4.9 |
| 4 | 新增 R10：Fault Injection Gate Test | ✅ | §4.10 |
| 5 | 新增 R11：spec_manifest.yaml / spec_item_coverage | ✅ | §4.11 |
| 6 | 明确 generated files 禁手改 + `make generate && git diff --exit-code` | ✅ | §4.13 (R13) |
| 7 | 明确 `--no-verify` 在正常流程禁用 | ✅ | §4.14 (R14) |
| 8 | 每个 R 项的验收落到具体命令和 exit code | ✅ | R1/R2/R3/R4/R5/R6/R7/R9/R10/R11/R13/R14 验收节均有命令 + exit code |
| 9 | 明确 `run_task_driver.py` 改造点：verifier 后调 R9，失败进入 fixer loop | ✅ | §4.2.5 / §4.9.5 |
| 10 | 明确 CI required checks：按 R12 矩阵触发 | ✅ | §4.12 (R12) |

10/10 满足。v2 申请重新评审。

---

## 9. 评审 AI 的输出期望

请你在评审完成后给出：

1. **每条 R1-R14 的打分表**（按 §0.1 格式；R8 已并入 R3 可只标 deprecated）
2. **优先级矩阵 v2 的合理性**（§3 三档分组是否合理？依赖顺序是否正确？）
3. **依赖图 v2 的合理性**（§5 是否完整描述了 contract → generated → runtime → evidence gate → fixer loop 闭环？）
4. **元教训 v2 的措辞**（§6 三段式是否准确？v2 配套元教训是否还有遗漏？）
5. **R9 evidence gate 的 artifact 列表是否完整**（§4.9.5 表格是否还缺哪些证据？）
6. **R10 fault injection 注入用例集是否覆盖足够**（§4.10.5 表格是否还缺哪些已知事故模式？）
7. **本文哪一条根因诊断仍然是错的**（如果有）—— 这条最重要，不要客气
8. **v2 是否可以放行**进入 AGENTS / HARNESS / Spec Coding 机制改造阶段

---

## 10. v2 修订审计追溯（按审核反馈条目对应）

| 审核反馈位置 | v2 落点 |
|---|---|
| 审核 §1 "三层补丁" | §0.0 修订说明 + §3 优先级 |
| 审核 §2.1-2.5 现场证据 | §2.6 + §2.7 同步 |
| 审核 §3 R1 修订建议 | §4.1.6 验收硬化（hash + timestamp + driver/CI 接入） |
| 审核 §3 R2 重写建议 | §4.2 完全重写为 Driver/CI Enforcement |
| 审核 §3 R3 根因修正 | §4.3.2 修正 + §4.3.4 生成链 |
| 审核 §3 R4 通用化 | §4.4 + §4.11 R11 |
| 审核 §3 R5 强约束 | §4.5.5 必须加载真实 main:app + Schemathesis/Spectral |
| 审核 §3 R6 lint 脚本 | §4.6.5 D 段 lint_fastapi_routes.py |
| 审核 §3 R7 加强 | §4.7.5 B 段 ban 所有 /api/ 字面量 |
| 审核 §3 R8 并入 | §4.8 标记并入 R3 |
| 审核 §4 优先级矩阵 | §3 三档重排 |
| 审核 §5 依赖图 | §5 重画 |
| 审核 §6 R9-R14 | §4.9 - §4.14 |
| 审核 §7 SPEC 写法 | §7 |
| 审核 §8 元教训 | §6 重写三段式 |
| 审核 §9 放行条件 | §8 自检表 |

---

文档结束（v2）。
