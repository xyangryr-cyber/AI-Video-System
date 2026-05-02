# SPEC-GAPFIX — Phase 2 错漏全量修复

> 目标: 修复验收报告中全部 33 项错漏，使系统通过 7 项成功标准
> 设计依据: `docs/superpowers/specs/2026-04-26-spec-gaps-fix-design.md`
> 验收报告: `docs/superpowers/specs/2026-04-27-acceptance-report-spec-gaps-fix.md`
> 执行计划: `docs/superpowers/plans/2026-04-27-phase2-gapfix-plan.md`

## 依赖关系

```
Phase 1 (合约层) → Phase 2 (路由层) → Phase 3 (前端层) / Phase 4 (WebSocket)
                                            ↓
                                       Phase 5 (集成层) / Phase 6 (媒体渲染)
                                            ↓
                                       Phase 7 (长期一致性)
```

## Task Card 索引

### Phase 1: 合约层 (4 cards)
| ID | 描述 | 优先级 |
|----|------|--------|
| [GAPFIX-001](GAPFIX-001-event-types-py.md) | event_types.py — 17 种 WS 事件枚举 | P0 |
| [GAPFIX-002](GAPFIX-002-event-types-ts.md) | event_types.ts — TypeScript 版本 | P0 |
| [GAPFIX-003](GAPFIX-003-error-codes-py.md) | error_codes.py — 17 个 EVID_ 错误码映射 | P0 |
| [GAPFIX-004](GAPFIX-004-error-codes-ts.md) | error_codes.ts — TypeScript 版本 | P0 |

### Phase 2: 路由层 (9 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-005](GAPFIX-005-system-py-prefix.md) | system.py — prefix + 移除 POST /api/projects | P0 | GAPFIX-003 |
| [GAPFIX-006](GAPFIX-006-observability-py-prefix.md) | observability.py — prefix 修复 | P0 | — |
| [GAPFIX-007](GAPFIX-007-cost-py-prefix.md) | cost.py — prefix + costs 复数 | P0 | — |
| [GAPFIX-008](GAPFIX-008-projects-py-new.md) | projects.py — 新建 CRUD router (17 endpoints) | P0 | GAPFIX-005 |
| [GAPFIX-009](GAPFIX-009-tasks-py-prefix.md) | tasks.py — prefix 修复 | P0 | — |
| [GAPFIX-010](GAPFIX-010-preferences-py-prefix.md) | preferences.py — prefix 修复 | P0 | — |
| [GAPFIX-011](GAPFIX-011-main-py-router-jsonlog.md) | main.py — router 去 prefix + JSON 日志 | P0 | 005-010 |
| [GAPFIX-012](GAPFIX-012-error-handler-middleware.md) | error_handler.py — EVID_ 异常中间件 | P0 | GAPFIX-003 |
| [GAPFIX-013](GAPFIX-013-route-alignment-test.md) | 路由对齐集成测试 | P0 | GAPFIX-011 |

### Phase 3: 前端层 (4 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-014](GAPFIX-014-remove-api-v1-prefix.md) | 删除 /api/v1/ 前缀 (8 文件 13 处) | P0 | GAPFIX-011 |
| [GAPFIX-015](GAPFIX-015-vite-proxy-config.md) | vite.config.ts proxy 配置 | P0 | — |
| [GAPFIX-016](GAPFIX-016-types-events-sync.md) | types/events.ts 同步 EventType | P0 | GAPFIX-002 |
| [GAPFIX-017](GAPFIX-017-apiclient-refactor.md) | apiClient 重构 — 消除字面量 | P0 | GAPFIX-014 |

### Phase 4: WebSocket (2 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-018](GAPFIX-018-connection-manager.md) | ConnectionManager — 连接池 + broadcast | P0 | GAPFIX-001 |
| [GAPFIX-019](GAPFIX-019-event-bus-callback.md) | event_bus 回调注入 + WS 集成测试 | P0 | GAPFIX-018 |

### Phase 5: 集成层 (6 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-020](GAPFIX-020-preflight-real-checkers.md) | preflight — 真实检查器 | P1 | GAPFIX-011 |
| [GAPFIX-021](GAPFIX-021-hard-claims-verification.md) | hard claims 验证阻断 | P1 | — |
| [GAPFIX-022](GAPFIX-022-gate-registry-init.md) | gate_registry 显式绑定 | P1 | — |
| [GAPFIX-023](GAPFIX-023-tasktype-docstring-fix.md) | TaskType docstring "8 → 17" | P2 | — |
| [GAPFIX-024](GAPFIX-024-agent-call-log-redact.md) | agent_call_log + redact hook | P1 | — |
| [GAPFIX-025](GAPFIX-025-sqlite-backup-script.md) | SQLite 备份脚本 | P1 | — |

### Phase 6: 媒体渲染 (3 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-026](GAPFIX-026-brand-kit-overlay.md) | brand_kit_overlay — 真实 Remotion | P1 | — |
| [GAPFIX-027](GAPFIX-027-whisper-alignment.md) | Whisper 强制对齐 | P1 | — |
| [GAPFIX-028](GAPFIX-028-voice-direction-pacemap.md) | voice_direction PACE_MAP 5 级 | P1 | — |

### Phase 7: 长期一致性 (5 cards)
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-029](GAPFIX-029-routes-sdk-generation.md) | routes SDK 生成脚本 | P2 | GAPFIX-011 |
| [GAPFIX-030](GAPFIX-030-enum-sync-scripts.md) | 枚举同步脚本 | P2 | GAPFIX-001,003 |
| [GAPFIX-031](GAPFIX-031-spec-coverage-check.md) | check_spec_coverage.py | P2 | Phase 1-6 |
| [GAPFIX-032](GAPFIX-032-phase-preview-components.md) | 12 Phase preview 组件补全 | P2 | GAPFIX-016 |
| [GAPFIX-033](GAPFIX-033-remotion-preview-composition.md) | Remotion PreviewComposition 真实接入 | P2 | — |

## 执行顺序

1. **Phase 1 必须先完成** — 合约是所有上层代码的地基
2. **Phase 2 紧随其后** — 路由修复是最危险的变更，必须仔细验证
3. **Phase 3 + Phase 4 可并行** — 前端和 WebSocket 相互独立
4. **Phase 5 + Phase 6 可并行** — 集成层和媒体渲染相互独立
5. **Phase 7 最后执行** — 代码生成依赖所有上层实现稳定

### Phase 8: 运行时连通性修复 (15 cards) — 第四轮扫描
| ID | 描述 | 优先级 | 依赖 |
|----|------|--------|------|
| [GAPFIX-034](GAPFIX-034-main-tsx-msw-startup.md) | main.tsx 启动 MSW worker | P0 | — |
| [GAPFIX-035](GAPFIX-035-vite-proxy-env-var.md) | vite.config.ts proxy 环境变量 | P0 | — |
| [GAPFIX-036](GAPFIX-036-projectlist-websocket-relative.md) | ProjectList.tsx WebSocket 相对路径 | P0 | — |
| [GAPFIX-037](GAPFIX-037-get-projects-list.md) | GET /api/projects 实现 | P0 | — |
| [GAPFIX-038](GAPFIX-038-get-project-state.md) | GET /api/projects/{id}/state 实现 | P0 | — |
| [GAPFIX-039](GAPFIX-039-cors-env-var.md) | CORS allow_origins 环境变量 | P2 | — |
| [GAPFIX-040](GAPFIX-040-preferences-confirm.md) | POST preferences/confirm 实现 | P1 | GAPFIX-038 |
| [GAPFIX-041](GAPFIX-041-missing-backend-routes.md) | 3 个缺失后端路由 | P1 | — |
| [GAPFIX-042](GAPFIX-042-e2e-playwright-infra.md) | E2E Playwright 基础设施 | P1 | — |
| [GAPFIX-043](GAPFIX-043-smoke-test.md) | 应用冒烟测试 | P1 | Phase 1 |
| [GAPFIX-044](GAPFIX-044-ci-container-check.md) | CI 容器连通性验证 | P1 | Phase 1 |
| [GAPFIX-045](GAPFIX-045-brandkit-apiclient.md) | brandKit.ts 改用 apiClient | P2 | — |
| [GAPFIX-046](GAPFIX-046-docker-compose-align.md) | docker-compose 服务命名统一 | P2 | — |
| [GAPFIX-047](GAPFIX-047-env-example.md) | .env.example 完善 | P2 | — |
| [GAPFIX-048](GAPFIX-048-http-integration-tests.md) | 前后端 HTTP 集成测试 | P2 | GAPFIX-037,038 |

## 关键约束

- **所有命令使用 `.venv/bin/python3 -m pytest`**，禁止裸 `pytest`
- **每卡独立 commit**，格式 `[SPEC-GAPFIX-NNN] <描述>`
- **TDD 硬约束** (HARNESS §4): RED → GREEN → REFACTOR → COMMIT
- **TDD 例外**: config 文件 (vite.config.ts)、docstring、one-shot 脚本
- **每 Phase 完成后**: 运行验证门禁 + 全量 pytest 防回归
