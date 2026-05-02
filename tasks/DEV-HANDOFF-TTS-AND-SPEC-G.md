# AI-Video-System 开发交接文档

> **本文档身份**：交给另一个 AI 开发者的完整工作单
> **创建日期**：2026-04-25
> **创建人**：上游 AI（已完成 .env 配置、API 桥接、前端后端联调、3 个演示项目种子数据）
> **目标读者**：接手的 AI 开发者
> **任务范围**：TTS 接入 + SPEC-G BDD 验收剩余 9 张卡 + 历史测试修复

---

## 0. 接手 AI 必读（读完再动手）

### 0.1 项目一句话描述

一个 12 阶段 AI 视频制作系统。架构：确定性 FSM + 无状态 LLM Agent + SQLite + FastAPI 后端 + Vite React 前端。用户描述想做的视频 → AI 从写稿、配音、配乐、做图表到合成 MP4 全流程自动完成。

### 0.2 必读文件（按顺序）

| # | 文件 | 说明 |
|---|------|------|
| 1 | `HARNESS.md` | 全局开发约束（TDD 铁律、文件大小限制、命名规范、提交格式） |
| 2 | `AGENTS.md` | 决策权限矩阵、Superpowers 技能触发规则 |
| 3 | `CLAUDE.md` | 项目导航地图、SPEC 依赖顺序 |
| 4 | `PROGRESS.md` | 开发进度日志（当前基线：2059 passed, 9 failed, 1 skipped） |
| 5 | `tasks/REMAINING-WORK-PLAN.md` | 历史遗留的全项目 wave plan（本交接文档是其 SPEC-G 子集的更新版） |
| 6 | `tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md` | 23 个历史 unit test 失败的详细调查指引（优先级低于本文档的 SPEC-G 任务） |
| 7 | `tasks/SPEC-G/G-000-DECOMPOSITION-HANDOFF.md` | SPEC-G-000 的拆解方案（已全部完成，作为参考背景阅读） |
| 8 | `docs/specs/SPEC-G-bdd-acceptance.md` | SPEC-G BDD 验收规范（权威参考） |
| 9 | `~/.claude/projects/-Users-xyangryr/memory/MEMORY.md` | 用户偏好（许阳是 product owner，非程序员；用大白话沟通；TDD 要保留 RED-GREEN 证据链） |

### 0.3 不要做

- **不要**修改 `docs/specs/SPEC-*.md`（SPEC 是只读参考，HARNESS §1.2）
- **不要**修改 `HARNESS.md` / `CLAUDE.md` / `AGENTS.md`
- **不要**修改 `.env` 或任何密钥文件
- **不要**为了让测试通过而 `pytest.skip` / `xfail`
- **不要**跨任务范围做无关重构（HARNESS §13："Keep edits scoped to task intent"）
- **不要**跳过 TDD 流程——先写失败测试，再写最小实现（HARNESS §4）
- **不要**在 commit 中跳过 hook（`--no-verify`）

### 0.4 必须做

- **TDD 严格执行**：每张 task card → RED commit + GREEN commit（保留审计证据）
- **每个 commit body 格式**（HARNESS §9.3）：Files Changed / Verification / Decisions / Artifacts
- **每个 task 完成后**：PROGRESS.md 追加一行（HARNESS §9.2）
- **Git Worktree 隔离开发**：所有工作在新分支上进行

---

## 1. 当前基线状态

### 1.1 环境

| 项目 | 状态 |
|------|------|
| Python 虚拟环境 | `.venv` 已建，Python 3.11，含所有核心依赖（litellm, huey, fastapi, pydantic, numpy, jsonschema） |
| 前端 | pnpm + Vite + React，`src/frontend/` 可直接 `pnpm --filter frontend dev` |
| 数据库 | SQLite，路径 `data/db/dev.sqlite3`（由 `DATABASE_URL` 环境变量控制） |
| LLM | DeepSeek V4 Pro，通过 LiteLLM 的 `openai/deepseek-v4-pro` 调用，连通性已验证 |
| TTS | **完全 stub** —— 后端 `TTSProvider.synthesize()` 和前端 `AzureTTSProvider` 均返回 mock 数据 |

### 1.2 测试基线

```bash
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no
# 结果：2059 passed, 9 failed, 1 skipped
```

9 个 pre-existing 失败：
1. `test_spec_c_011.py::test_resolve_model_returns_five_role_defaults` — model config 相关
2. `test_spec_c_011.py::test_chat_completion_delegates_to_litellm_by_default` — litellm 默认调用
3. `test_spec_c_015.py::test_gatekeeper_uses_claude_model` — GateKeeper 模型选择
4. `test_spec_b_002.py::test_all_db_writes_live_under_repositories` — DB 写入集中化
5. 其余 5 个与 model config / LLM service / DB repository 相关（详见 `HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md`）

BDD 测试：
```bash
.venv/bin/python3 -m pytest tests/integration/bdd/ -v
# SPEC-G 已完成 9 张卡（G-000 系列 + G-001/002/003）
# 剩余 9 张卡的 BDD scenario 当前 FAIL
```

### 1.3 服务启动方式

```bash
# 后端
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
source .venv/bin/activate
uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
corepack enable && pnpm install && pnpm --filter frontend dev
```

---

## 2. 任务总览

| # | 任务 | 类型 | 优先级 | 预估复杂度 | 依赖 |
|---|------|------|--------|-----------|------|
| 1 | **字节跳动 TTS 接入** | 新功能开发 | P0 | L | 无 |
| 2 | SPEC-G-004 P6 SFX 编排接线 | BDD 修复 | P0 | M | G-000e, G-003 |
| 3 | SPEC-G-005 P8 Keyframe 编排接线 | BDD 修复 | P0 | M | G-000e |
| 4 | SPEC-G-006 P10 RoughCut 编排接线 | BDD 修复 | P0 | M | G-000e, G-002, G-005 |
| 5 | SPEC-G-007 P11 FinalCut 编排接线 | BDD 修复 | P0 | M | G-000e, G-006 |
| 6 | SPEC-G-008 PreferenceExtractor 修复 | BDD 修复 | P0 | S | 无 |
| 7 | SPEC-G-009 SafetyPolicy 返回格式对齐 | BDD 修复 | P0 | XS | 无 |
| 8 | SPEC-G-010 WorkflowPage 上下文对齐 | BDD+前端 | P1 | S | 无 |
| 9 | SPEC-G-011 Observability 断言格式对齐 | BDD 修复 | P1 | XS | G-001 |
| 10 | SPEC-G-012 Eval BDD Step 补齐 | BDD 修复 | P1 | M | 无 |
| 11 | 9 个历史 unit test 失败修复 | Bug 修复 | P2 | M | 无 |

---

## 3. 任务 1：字节跳动 TTS 接入（详细规格）

### 3.1 问题陈述

当前后端 `src/backend/services/tts_provider.py` 的 `TTSProvider.synthesize()` 是纯 stub——不调用任何 API，返回 mock 数据（`phase_4/seg_audio_xxxx.mp3`、假 duration）。

前端 `src/frontend/audio/providers/AzureTTSProvider.ts` 同样是 stub——返回 `base64:azure:...` 假数据。

字节跳动 OpenSpeech TTS 的 API 凭证已在 `.env` 中配置好：
```
BYTEDANCE_TTS_APP_ID=9061824843
BYTEDANCE_TTS_ACCESS_TOKEN=JDkdzY8awzQ_65UlrTzglP-ndxQ7Y9AH
BYTEDANCE_TTS_SECRET_KEY=eiUEr9CdvWmTw0-vS0A_tJZNMWRgleVB
```

### 3.2 API 信息

| 项目 | 值 |
|------|-----|
| 接口地址 | `https://openspeech.bytedance.com/api/v1/tts` |
| 请求方式 | POST |
| 认证方式 | Header: `Authorization: Bearer;{access_token}` |
| 请求格式 | JSON body，含 `appid`、`text`、`voice` 等参数 |
| 响应格式 | JSON，含 base64 编码的音频数据 |
| 官方文档 | https://www.volcengine.com/docs/6561/79820 |

### 3.3 实现方案

**后端**（主战场）：

新建 `src/backend/services/bytedance_tts_provider.py`：

```python
class ByteDanceTTSProvider(TTSProvider):
    """真实调用字节跳动 OpenSpeech TTS API 的 Provider。

    继承 TTSProvider（抽象基类），实现 synthesize() 方法：
    1. 从 os.environ 读取 BYTEDANCE_TTS_APP_ID / ACCESS_TOKEN / SECRET_KEY
    2. 构造 HTTP POST 请求到 https://openspeech.bytedance.com/api/v1/tts
    3. Authorization header: "Bearer;{access_token}"
    4. Body: {"appid": "...", "text": "...", "voice": "...", ...}
    5. 将响应中的 base64 音频解码为 mp3 文件，保存到 data/audio/{project_id}/
    6. 返回 {"audio_path": "...", "duration_seconds": ..., "sample_rate": ...}
    """
```

需要做的事：
1. 确认 `requests` 库是否在 requirements.txt 中（用于 HTTP 调用）。如不在，用 `urllib.request`（标准库，无需额外依赖）实现 HTTP 调用
2. 参考 `tts_provider.py` 的返回格式，保持接口兼容
3. `voice_params` 映射：将 `voice_id`、`style`、`rate_wpm`、`pitch`、`volume` 等参数映射到字节跳动 API 的对应字段
4. SSML 支持：如果传入了 `ssml_tags`，用 SSML 格式发送而非纯文本
5. 错误处理：网络失败 / API 返回错误时，fallback 到 stub 行为（返回 mock 数据 + 记录 error log），不阻断流水线

**注入点**：找到所有创建 `TTSProvider()` 实例的地方，改为 `ByteDanceTTSProvider()`。主要在：
- `src/backend/agents/tts_agent.py:33` — `self._provider = provider or TTSProvider()` → 改为 `ByteDanceTTSProvider()`

**前端**（轻量改动）：

前端 `AzureTTSProvider` 是 stub，但前端的音频播放实际上是通过后端 API 获取音频文件 URL 来播放的（而非前端直接调 TTS API）。所以前端改动较小：
- 检查 `src/frontend/components/phase4/MasterAudioPlayer.tsx` 和 `P4SegmentAudioPlayer.tsx` 是否通过后端 API 获取音频
- 如音频 URL 是硬编码的 stub 路径，改为指向正确的后端路由

### 3.4 TDD 路径

1. **RED**：在 `tests/unit/services/` 新建 `test_bytedance_tts_provider.py`
   - Mock `urllib.request.urlopen` 或 `requests.post`
   - AC-1: `synthesize()` 返回的 `audio_path` 指向真实文件路径（非 stub 的 `phase_4/seg_audio_xxxx.mp3`）
   - AC-2: HTTP 请求的 Authorization header 包含正确的 token
   - AC-3: 环境变量缺失时优雅降级（不抛异常，fallback 到 stub 行为）
   - AC-4: API 返回错误时优雅降级
   - AC-5: 支持中文字符（text 参数含中文时正确编码）
2. Commit: `[FEAT-TTS] RED: ByteDanceTTSProvider tests`
3. **GREEN**：实现 `ByteDanceTTSProvider` 类
4. Commit: `[FEAT-TTS] GREEN: ByteDanceTTSProvider implementation`
5. **REFACTOR**：注入到 TTSAgent，更新前端音频播放路径
6. Commit: `[FEAT-TTS] REFACTOR: wire ByteDanceTTSProvider into TTSAgent + frontend`

### 3.5 Allowed Files

- `src/backend/services/bytedance_tts_provider.py`（新建）
- `src/backend/agents/tts_agent.py`（仅改默认 provider 注入）
- `src/frontend/audio/providers/`（如需要新建 ByteDanceTTSProvider.ts）
- `src/frontend/components/phase4/`（如音频路径需调整）
- `tests/unit/services/test_bytedance_tts_provider.py`（新建）

### 3.6 Forbidden Files

- `.env`（密钥文件，不动）
- `docs/specs/SPEC-*.md`
- `HARNESS.md` / `CLAUDE.md` / `AGENTS.md`

### 3.7 Verification Commands

```bash
.venv/bin/python3 -m pytest tests/unit/services/test_bytedance_tts_provider.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/services/bytedance_tts_provider.py
.venv/bin/mypy src/backend/services/bytedance_tts_provider.py
```

---

## 4. 任务 2-10：SPEC-G BDD 验收剩余 9 张卡

### 4.1 SPEC-G 背景

SPEC-G 是 BDD 验收测试层——用 Gherkin feature 文件定义 12 个阶段的用户可见行为，step definitions 调用编排层（WorkflowEngine → Dispatcher → Huey task → Agent）验证端到端行为。

当前完成 9/18 张卡（G-000 系列基础设施 + G-001 DB fixture + G-002 P4 TTS 接线 + G-003 P5 BGM 接线）。

剩余 9 张卡按依赖关系和优先级排列如下。

### 4.2 卡 1：SPEC-G-008 PreferenceExtractor 边缘情况修复

- **文件**：`tasks/SPEC-G/G-008-preference-extractor-edge-cases.md`
- **复杂度**：S（约 50 行改动）
- **依赖**：无
- **核心改动**：`src/backend/agents/preference_extractor.py` — `extract()` 在无匹配时返回 `{"nothing_found": True, "candidates": []}` 而非 `None`
- **BDD 场景**：`preferences.feature` + `preferences-2.feature`（2 个 scenario）
- **建议首先做**——独立、简单、无依赖

### 4.3 卡 2：SPEC-G-009 SafetyPolicy 返回值格式对齐

- **文件**：`tasks/SPEC-G/G-009-safety-policy-return-format.md`
- **复杂度**：XS（约 20 行改动）
- **依赖**：无
- **核心改动**：`tests/integration/bdd/steps/safety_steps.py` — 适配 `(PolicyDecision, str)` tuple 返回值
- **BDD 场景**：`safety.feature`（1 个 scenario）
- **建议第二位做**——最简单、无依赖

### 4.4 卡 3：SPEC-G-004 P6 SFX 编排层接线

- **文件**：`tasks/SPEC-G/G-004-p6-sfx-orchestration-wiring.md`
- **复杂度**：M（约 100 行改动）
- **依赖**：G-000e, G-001, G-003
- **核心改动**：`tests/integration/bdd/steps/phase6_steps.py` — 从直接调 SFXAgent 改为通过 WorkflowEngine 编排层
- **BDD 场景**：`phase6.feature`（3 个 scenario）
- **注意**：文件可能超过 400 行（HARNESS §6 限制），必要时拆分为子模块

### 4.5 卡 4：SPEC-G-005 P8 Keyframe 编排层接线

- **文件**：`tasks/SPEC-G/G-005-p8-keyframe-orchestration-wiring.md`
- **复杂度**：M（约 100 行改动）
- **依赖**：G-000e, G-001
- **并行**：可与 G-002/003/004 并行（P8 与 P4-P6 音频链无数据依赖）
- **核心改动**：`tests/integration/bdd/steps/phase8_steps.py`
- **BDD 场景**：`phase8.feature`（2 个 scenario）

### 4.6 卡 5：SPEC-G-006 P10 RoughCut 编排层接线

- **文件**：`tasks/SPEC-G/G-006-p10-roughcut-orchestration-wiring.md`
- **复杂度**：M（约 80 行改动）
- **依赖**：G-000e, G-001, G-002, **G-005**（P10 依赖 P4 音频 + P8 关键帧产物）
- **核心改动**：`tests/integration/bdd/steps/phase10_steps.py`
- **BDD 场景**：`phase10.feature`（1 个 scenario）

### 4.7 卡 6：SPEC-G-007 P11 FinalCut 编排层接线

- **文件**：`tasks/SPEC-G/G-007-p11-finalcut-orchestration-wiring.md`
- **复杂度**：M（约 80 行改动）
- **依赖**：G-000e, G-001, **G-006**（P11 依赖 P10 粗剪产物）
- **核心改动**：`tests/integration/bdd/steps/phase11_steps.py`
- **BDD 场景**：`phase11.feature`（2 个 scenario）

### 4.8 卡 7：SPEC-G-010 WorkflowPage 上下文状态对齐

- **文件**：`tasks/SPEC-G/G-010-workflow-page-context.md`
- **复杂度**：S（约 50 行改动）
- **依赖**：无
- **优先级**：P1
- **核心改动**：前端 `src/frontend/components/WorkflowPage.tsx` 或 BDD step `navigation_steps.py`
- **BDD 场景**：`navigation.feature`（1 个 scenario）
- **注意**：需要判断是前端缺实现还是 BDD assertion 过严

### 4.9 卡 8：SPEC-G-011 Observability 断言格式对齐

- **文件**：`tasks/SPEC-G/G-011-observability-assertion-fix.md`
- **复杂度**：XS（约 15 行改动）
- **依赖**：G-001
- **优先级**：P1
- **核心改动**：`tests/integration/bdd/steps/observability_steps.py` — assertion 格式匹配 SUT 实际返回
- **BDD 场景**：`observability.feature`（2 个 scenario）

### 4.10 卡 9：SPEC-G-012 Eval BDD Step Definitions 补齐

- **文件**：`tasks/SPEC-G/G-012-eval-step-definitions.md`
- **复杂度**：M（约 120 行新 step definitions）
- **依赖**：无
- **优先级**：P1
- **核心改动**：`tests/eval/bdd/steps/classification_steps.py` — 补齐 6 个缺失的 step definitions
- **BDD 场景**：6 个 eval scenario（由 `AVS_EVAL_MODE=1` 控制，不在日常 CI loop 中）

---

## 5. 任务 11：9 个历史 Unit Test 失败修复（可选）

### 5.1 背景

这 9 个 pre-existing 失败与 SPEC-G 无关，是更早的基线问题。详细调查指引在 `tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md` 中。

### 5.2 失败清单

```
tests/unit/backend-core/test_spec_c_011.py::TestAC4ConfigChangeAppliesNewModel::test_resolve_model_returns_five_role_defaults
tests/unit/backend-core/test_spec_c_011.py::TestAC5AllCallsThroughLlmService::test_chat_completion_delegates_to_litellm_by_default
tests/unit/backend-core/test_spec_c_015.py::TestAC8GatekeeperUsesClaudeModel::test_gatekeeper_uses_claude_model
tests/unit/infra/test_spec_b_002.py::TestAC4DbWritesCentralizedInRepositoryLayer::test_all_db_writes_live_under_repositories
（其余 5 个见 HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md 的完整列表）
```

### 5.3 建议

- **优先级 P2**——不阻塞 SPEC-G BDD 验收，不影响 TTS 接入
- **强烈建议在 SPEC-G 全部完成后修复**，否则后续开发者无法分辨"我改坏了"和"本来就坏"
- 每 cluster 修复独立 commit
- 修复前读 `HARNESS.md` §4 TDD 和 `AGENTS.md` 排障铁律

---

## 6. 推荐执行顺序

```
Phase 1 — 快速 wins（独立、简单，建立 momentum）
  ├── 任务 2: SPEC-G-008 PreferenceExtractor（S, 无依赖）
  ├── 任务 3: SPEC-G-009 SafetyPolicy（XS, 无依赖）
  └── 任务 9: SPEC-G-011 Observability（XS, 仅依赖 G-001 ✓）

Phase 2 — TTS 接入（核心功能，独立于 BDD）
  └── 任务 1: 字节跳动 TTS 接入（L, 无依赖）

Phase 3 — BDD 编排层接线（5 张卡，按依赖顺序）
  ├── 任务 4: SPEC-G-004 P6 SFX（M, 依赖 G-003 ✓）
  ├── 任务 5: SPEC-G-005 P8 Keyframe（M, 可与 P6 并行）
  ├── 任务 6: SPEC-G-006 P10 RoughCut（M, 等 P8 完成）
  └── 任务 7: SPEC-G-007 P11 FinalCut（M, 等 P10 完成）

Phase 4 — 收尾
  ├── 任务 8: SPEC-G-010 WorkflowPage（S, P1）
  ├── 任务 10: SPEC-G-012 Eval Steps（M, P1）
  └── 任务 11: 9 个历史 unit test 修复（M, P2, 可选）
```

---

## 7. 关键文件速查

| 文件 | 作用 | 可否修改 |
|------|------|---------|
| `src/backend/services/tts_provider.py` | TTS 抽象基类（当前 stub） | 否（只读参考） |
| `src/backend/services/bytedance_tts_provider.py` | **TTS 接入——在此新建** | 是 |
| `src/backend/agents/tts_agent.py` | P4 TTS Agent（入口：`TTSAgent.__init__(provider=...)`） | 是（仅 provider 注入） |
| `src/frontend/audio/providers/BaseTTSProvider.ts` | 前端 TTS 抽象基类 | 否（只读参考） |
| `src/frontend/audio/providers/AzureTTSProvider.ts` | 前端 Azure TTS（当前 stub） | 参考，可新建 ByteDance 版 |
| `src/backend/engine/workflow_engine.py` | 工作流引擎（394 行） | 否（只读，用其 API） |
| `src/backend/engine/dispatcher.py` | 任务调度器（120 行） | 否（只读，G-000 已改完） |
| `src/backend/workers/tasks.py` | 6 个 phase huey task 函数 | 否（只读，G-000d 已实现） |
| `tests/integration/bdd/conftest.py` | BDD 共享 fixture（bdd_db_conn 等） | 是 |
| `tests/integration/bdd/steps/phase{4-11}_steps.py` | 各阶段 BDD step definitions | 是（按 allowed_files） |
| `tests/integration/bdd/features/*.feature` | Gherkin feature 文件 | 否（只读） |
| `config/model_config.json` | 5 角色 → 模型映射 | 否（已配好 DeepSeek V4 Pro） |
| `.env` | API 密钥 | **绝对不可修改** |

---

## 8. 每张卡的完成判据

每张卡完成后必须满足：

- [ ] 该卡所有 AC 对应的 BDD scenario 从 FAIL → PASS
- [ ] `pytest tests/unit/ -q` 通过数不降（≥ 2059 passed）
- [ ] `ruff check` 通过（涉及的文件）
- [ ] `mypy` 通过（涉及的文件）
- [ ] `python3 scripts/contracts/verify_no_skip_stubs.py` exit 0
- [ ] commit body 按 HARNESS §9.3 格式（Files Changed / Verification / Decisions / Artifacts）
- [ ] PROGRESS.md 追加一行
- [ ] 每个 commit 使用 `[SPEC-G-NNN]` 或 `[FEAT-TTS]` 前缀

---

## 9. 最终完成判据（全部任务完成后）

- [ ] 字节跳动 TTS 可生成真实音频文件（非 stub），P4 阶段能听到人声旁白
- [ ] SPEC-G BDD 验收：18/18 张卡全部 DONE（当前 9/18）
- [ ] `pytest tests/integration/bdd/ -v` 全部 feature 文件至少核心 scenario PASS
- [ ] `pytest tests/unit/ -q` 通过数 ≥ 2059（不降）
- [ ] 9 个历史 unit test 失败修复为 0（如选择了 Phase 4）
- [ ] 前端可正常启动、项目列表可加载、创建项目可走通
- [ ] PROGRESS.md 有完整的 commit 记录

---

## 10. 异常路径

| 情况 | 接手 AI 应做 |
|------|------------|
| 字节跳动 TTS API 返回认证失败 | 检查 token 是否过期（token 有时效性），向许阳确认是否需要刷新凭证 |
| TTS API 不可达（网络问题） | 实现 fallback 到 stub 行为（不阻断流水线），记录 error log |
| 某个 SPEC-G 卡修了 3 次仍不过 | 停止，分析根因是新问题还是 SPEC/代码设计缺陷，写反馈给许阳 |
| 修改 BDD step 文件后发现 unit test 回归 | 立即 `git revert`，重新调查。BDD step 不应影响 unit test |
| 发现需要修改 forbidden_files 中的文件 | 停止，向许阳申请 red-light 批准（HARNESS §12） |
| huey 库行为与预期不符 | 检查 huey 版本（`pip show huey`），参考 G-000-DECOMPOSITION-HANDOFF.md 的 known issues |

---

## 附录 A：ByteDance TTS API 请求示例

```python
import json
import urllib.request

app_id = "9061824843"
access_token = "JDkdzY8awzQ_65UlrTzglP-ndxQ7Y9AH"
text = "欢迎使用AI视频制作系统"
voice = "zh_female_qingxin"  # 或其他音色

body = json.dumps({
    "appid": app_id,
    "text": text,
    "voice": voice,
    "format": "mp3",
    "rate": 160,       # 语速 (words per minute)
    "volume": 1.0,     # 音量 (0.0-1.0)
    "pitch": 0.0,      # 音调 (-12 to 12)
}).encode("utf-8")

req = urllib.request.Request(
    "https://openspeech.bytedance.com/api/v1/tts",
    data=body,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{access_token}",
    },
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    # result["audio"] 是 base64 编码的音频数据
```

## 附录 B：项目目录结构要点

```
AI-Video-System/
├── src/
│   ├── backend/
│   │   ├── agents/         # 12 个 phase 的 AI agent（只读参考）
│   │   ├── api/main.py     # FastAPI 入口（已配好 CORS + 所有路由）
│   │   ├── api/routes/     # v1.py（项目 CRUD）+ settings_bridge.py（配置）
│   │   ├── engine/         # 工作流引擎 + 调度器（只读）
│   │   ├── services/       # TTS provider + LLM service（TTS 在此新建）
│   │   └── workers/        # Huey 异步任务
│   ├── frontend/           # React + Vite
│   │   ├── audio/          # TTS 接口 + 厂商实现
│   │   ├── components/     # 各 phase 的 UI 组件
│   │   └── hooks/          # API hooks
│   └── shared/             # 跨层类型 + Schema
├── tests/
│   ├── unit/               # 单元测试（2059 passed）
│   ├── integration/bdd/    # BDD 验收测试（主战场）
│   └── eval/bdd/           # Eval BDD 测试
├── config/model_config.json  # 模型角色映射
├── .env                      # API 密钥（已配置）
└── tasks/SPEC-G/             # SPEC-G 任务卡（详细规格）
```

---

*文档版本：v1.0*
*关联文档：`docs/AI-Video-System 使用说明书.md`（已同步更新配置章节）*
*许阳需求：完成 TTS 接入 + 补齐所有遗留开发任务*
