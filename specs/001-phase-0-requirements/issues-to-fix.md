# Phase 0 待修复问题清单

**日期**: 2026-05-02
**来源**: T040 全量测试运行结果 (31/46 pass)

---

## 1. Schema 字段名不匹配

### 1.1 `target_duration` 缺失

| 项目 | 内容 |
|------|------|
| **影响测试** | `TestUS1HappyPath`, `TestFullPhase0HappyPath` |
| **现象** | `artifact_data.target_duration is missing` |
| **原因** | 测试期望 `target_duration`，实际 artifact 使用 `target_duration_seconds` |
| **修复方向** | 更新测试断言：`target_duration_seconds` 替换 `target_duration`，或添加别名映射 |

### 1.2 `clarification_needed` 缺失

| 项目 | 内容 |
|------|------|
| **影响测试** | `TestUS3ClarificationFlow` |
| **现象** | `artifact_data.clarification_needed is missing` |
| **原因** | RequirementsAgent 输出中未包含该字段，或字段名不一致 |
| **修复方向** | 确认 RequirementsAgent 是否输出此字段，更新 schema 或测试 |

### 1.3 `clarified_topic` LLM 输出类型错误

| 项目 | 内容 |
|------|------|
| **影响测试** | `TestAC1RequirementsAgentOutputFields` |
| **现象** | `Input should be a valid string [type=string_type, input_value={'domain': 'Finance', ...}, input_type=dict]` |
| **原因** | LLM 将 `clarified_topic` 输出为 dict 而非 string |
| **修复方向** | 调整 prompt 模板，强制 `clarified_topic` 为纯文本字符串；或放宽 Pydantic schema 接受 string|dict |

---

## 2. HTTP 状态码与错误码不一致

### 2.1 空标题返回 422 而非 400

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_create_project_empty_title_returns_400` |
| **现象** | 期望 400，实际返回 422 (Pydantic 校验) |
| **修复方向** | 更新测试期望为 422（FastAPI 默认行为）；或添加自定义异常处理器统一为 400 |

### 2.2 短描述未被 API 拦截

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_create_project_short_description_returns_400` |
| **现象** | 期望 400，实际返回 201（短描述直接创建成功） |
| **修复方向** | 确认 API 是否应对短描述拒绝；如果需要拦截，在路由层或 Pydantic schema 添加 `min_length` |

### 2.3 Gate 阻塞返回 200 而非 409/422

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_advance_before_artifact_is_blocked`, `test_advance_before_artifact_returns_gate_blocked` |
| **现象** | 期望 409 或 422，实际返回 `200 {"status":"gate_failed","error_code":"EVID_2001"}` |
| **修复方向** | 统一 Gate 阻塞的 HTTP 语义——要么改成 409/422 响应码，要么更新测试接受 200+gate_failed |

### 2.4 错误码格式不匹配

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_get_state_nonexistent_project_returns_404`, `test_get_artifact_invalid_phase_returns_404` |
| **现象** | 期望 `NOT_FOUND` / `INVALID_PHASE`，实际返回 `EVID_1002` |
| **修复方向** | 统一错误码体系——要么更新测试使用 `EVID_1002` 等实际错误码，要么将后端错误码映射为语义化标识 |

---

## 3. LLM 行为不确定性问题

### 3.1 Revise 消息被路由为 Clarify

| 项目 | 内容 |
|------|------|
| **影响测试** | `TestUS2ReviseFlow`, `TestUS2RegenerateFlow` |
| **现象** | 发送 revise/regenerate 消息后，Router 返回 `action: "clarify"` 而非 `revise`/`regenerate` |
| **原因** | 项目处于初始 clarify 阶段时，Router 优先触发 clarify 而非 revise |
| **修复方向** | 测试需确保项目已完成初始 clarify 后再发送 revise 消息；或 Router 逻辑调整优先级 |

---

## 4. 异步时序问题

### 4.1 Artifact 生成超时

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_regenerate_via_chat_creates_fresh_artifact`, `test_advance_returns_200_with_status_field` |
| **现象** | 等待 45-60s 后 artifact 仍未就绪 |
| **原因** | LLM 调用异步执行，测试轮询超时不足以覆盖 agent 处理时间 |
| **修复方向** | 增加测试轮询超时或添加 mock/fast-path 模式加速测试 |

---

## 5. WebSocket 事件类型缺失

### 5.1 `ws.connected` 未在已知事件类型中

| 项目 | 内容 |
|------|------|
| **影响测试** | `test_websocket_events_received_on_project_create` |
| **现象** | 收到 `ws.connected` 事件，但 `VALID_WS_EVENT_TYPES` 中未包含 |
| **修复方向** | 将 `ws.connected` 加入已知事件类型集合 |

---

## 修复优先级建议

| 优先级 | 类别 | 影响范围 | 估计工作量 |
|--------|------|----------|------------|
| **P0** | 1.1 字段名不匹配 | 2 个集成测试 | 10 分钟 |
| **P0** | 2.4 错误码格式 | 2 个合约测试 | 15 分钟 |
| **P0** | 5.1 WebSocket 事件类型 | 1 个合约测试 | 5 分钟 |
| **P1** | 2.3 Gate HTTP 语义 | 2 个测试 | 30 分钟（需确认意图） |
| **P1** | 1.3 LLM 输出类型 | 1 个单元测试 | 20 分钟（prompt 调整） |
| **P2** | 2.1 空标题 422/400 | 1 个合约测试 | 5 分钟 |
| **P2** | 2.2 短描述校验 | 1 个合约测试 | 15 分钟（需确认需求） |
| **P2** | 3.1 LLM 路由优先级 | 2 个集成测试 | 1 小时（需调整测试流程） |
| **P3** | 1.2 clarification_needed 字段 | 1 个集成测试 | 需调研 |
| **P3** | 4.1 异步超时 | 2 个测试 | 30 分钟 |

> **注**: P0 为纯测试侧修正（字段名/枚举值同步），不改业务逻辑。P1 涉及 API 语义或 prompt 调整，需确认意图后修改。P2/P3 为测试流程优化或需调研项。
