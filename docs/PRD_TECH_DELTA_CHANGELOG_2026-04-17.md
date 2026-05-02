# PRD / TECH_PLAN 增量改动对照表（2026-04-17，v3.17-AudioMaster + P7A）

日期：2026-04-17
依据：`docs/BDD_DELTA_MOD_REQUIREMENTS_2026-04-17_phase4-8.md`
影响文件：
- `docs/PRD_v3.3_Web交互式视频制作系统.md`
- `docs/TECH_PLAN_v3.3.md`

本表列出本轮所有**增量改动**的具体位置、新增字段/产物/模块，以及对 SPEC-A..F / tasks 的下游增改提示。后续 SPEC 更新与 task 派生可按 **DELTA-ID** 逐条对齐。

---

## 1. PRD 改动总览（八条 PRD-DELTA）

| DELTA-ID | 所在章节 | 改动类型 | 关键新增字段 / 产物 / 交互 |
|---|---|---|---|
| PRD-DELTA-01 | §7.6 Phase 4 | 升级交付物 / 交互 / Gate | `phase_4/narration_master.mp3` + `.json`；主播放器 + 下载；Gate 新增主文件完整性、拼接校验 |
| PRD-DELTA-02 | §7.7 Phase 5 | 升级交付物 / 审核 / 交互 | `bgm_mix_preview_XX.mp3`；MusicFitReviewer 新增 3 项；默认试听改为混音预览 |
| PRD-DELTA-03 | §7.7 + §7.8.2 | 输出主文件 + 下游消费 | `bgm_mix_master.mp3` + `.json`；P6 输入改为 master；`project_state.master_audio_ref` 切换规则 |
| PRD-DELTA-04 | §7.8 Phase 6 | 拆双阶段交互 | `sfx_plan.json`（含 rationale/narrative_role）+ 加工分段 `sfx_applied_segments/seg_XX.mp3`；用户先确认全文布局再逐段试听 |
| PRD-DELTA-05 | §7.8 Phase 6 | 最终音频主文件 | `final_audio_with_bgm_sfx.mp3` + `.json`；后续阶段默认主音频源 |
| PRD-DELTA-06 | §7.9A（新增章节） | 新增子阶段 | P7A 分镜物料补充；三角色（Planner/Fetcher/Verifier）；`material_manifest.json` + `shot_material_bindings.json` + `verified_materials/` |
| PRD-DELTA-07 | §7.9A.3 | 图表子流程 | `chart_material` 含 chart_spec + axis_spec；识别→时间范围→抓数→验证→坐标轴→Shot 绑定 |
| PRD-DELTA-08 | §7.10 Phase 8 | 严格消费 P7A + 降级二分 | `MaterialReadinessCheck`；`render_failed` / `material_missing` / `material_unverified` 三类错误 |
| PRD 总览 | §7.1 / §7.1.1 | 总表 + 场景卡片 | P4/P5/P6 合并主音频行；新增 P7A 行；P4-P8 场景卡片升级 |

### 1.1 PRD 章节行号定位（改动点）

| DELTA-ID | 章节 | 主要修改/插入位置 |
|---|---|---|
| 总览 | §7.1 表 + §7.1.1 场景卡片表 | 新增 P7A 行 + P4-P8 升级描述 |
| PRD-DELTA-01 | §7.6.1 / §7.6.5 / §7.6.6 | 覆盖交付物、用户交互、Gate 4 |
| PRD-DELTA-02 | §7.7.1 / §7.7.4 / §7.7.5 / §7.7.6 | 覆盖交付物、MusicFitReviewer 检查、交互、Gate 5 |
| PRD-DELTA-03 | §7.7.1 / §7.7.2 / §7.7.6 / §7.8.2 | 主文件定义 + 基线切换 + P6 输入 |
| PRD-DELTA-04 | §7.8.1 / §7.8.3 / §7.8.4 / §7.8.5 / §7.8.6 | 三层产物、双 Step 执行、双层 Reviewer、两段交互、Gate 6 |
| PRD-DELTA-05 | §7.8.1 / §7.8.5 / §7.8.6 | 最终音频产物 + 下载 + 基线切换 |
| PRD-DELTA-06 | §7.9A.1-§7.9A.6（新增） | 新 Phase 7A 六节完整定义 |
| PRD-DELTA-07 | §7.9A.3 图表子流程段 | chart_material schema 与标准流程 |
| PRD-DELTA-08 | §7.10.1 / §7.10.2 / §7.10.3 / §7.10.4 | 前置变更 + 降级规则 + VisualReviewer 新增物料一致性 |

---

## 2. TECH_PLAN 改动总览（八条 TECH-DELTA）

**全部集中在新增章节 §23（v3.17-AudioMaster + P7A 补丁集）**，分节如下：

| DELTA-ID | 所在节 | 改动类型 | 关键新增模块 / 数据结构 |
|---|---|---|---|
| TECH-DELTA-01 | §23.A | schema + 依赖重写 | `MasterAudioArtifact` schema（3 种 kind）；`project_state.master_audio_ref` |
| TECH-DELTA-02 | §23.B | 模块 + Reviewer 升级 | `AudioMixPreviewService` / `BgmMixRenderer`；MusicFitReviewer 新增 3 项 L1 检查 |
| TECH-DELTA-03 | §23.C | 数据结构分两层 + 模块 | `sfx_layout_plan.json` / `sfx_mix_segments.json`；`ScriptAnnotationViewModel` / `SfxSegmentMixService` / `FinalAudioAssembler` |
| TECH-DELTA-04 | §23.D | Reviewer 拆双层 | `SfxLayoutReviewer` / `SfxMixReviewer`；反馈协议 layout_feedback / mix_feedback |
| TECH-DELTA-05 | §23.E | FSM + 三角色 | `phase_7a` FSM 态；`StoryboardAssetPlanner` / `MaterialFetcher` / `MaterialVerifier`；`material_manifest.json` / `shot_material_bindings.json` schema |
| TECH-DELTA-06 | §23.F | Contract | `chart_material` schema（含 chart_spec + axis_spec）；`TemplateProps` 扩展 |
| TECH-DELTA-07 | §23.G | 前置检查 + 降级二分 | `MaterialReadinessCheck`；三类 `error_code`；KeyframeRenderAgent 出站白名单 |
| TECH-DELTA-08 | §23.H | 前端 State + 下载协议 | `MasterAudioView` / `AnnotationSpan` / `ShotMaterialBindingView`；`GET /artifacts/master_audio` |
| 验收 | §23.9 | 验收门禁 | 10 条集成/单测断言（按 DELTA-ID 映射） |

---

## 3. SPEC 层增改提示（按 SPEC-A..F 分组）

> 以下仅为下游映射提示，具体 AC 条目与 task 粒度在 SPEC 与 tasks 目录维护。

### SPEC-A（contracts / schema / types）

- 新增 `src/shared/schemas/audio_master.schema.json` → 对应 TECH-DELTA-01
- 扩展 `project_state.schema.json` 增加 `master_audio_ref` 字段 → TECH-DELTA-01
- 新增 `sfx_layout_plan.schema.json` + `sfx_mix_segments.schema.json` → TECH-DELTA-03
- 新增 `material_manifest.schema.json` + `shot_material_bindings.schema.json` → TECH-DELTA-05
- 新增 `chart_material.schema.json`（含 axis_spec 子 schema）→ TECH-DELTA-06
- API：新增 `GET /api/projects/{id}/artifacts/master_audio?phase={4|5|6}` → TECH-DELTA-08
- FSM 枚举：新增 `phase_7a` 态 → TECH-DELTA-05
- 新增错误码 `material_missing` / `material_unverified` / `render_failed`（若已有保持一致）→ TECH-DELTA-07

### SPEC-B（infra / storage / worker）

- SQLite 迁移：`projects` 表新增 `master_audio_ref` 字段 → TECH-DELTA-01
- 存储目录规范：新增 `phase_5/bgm_candidates/`、`phase_6/sfx_applied_segments/`、`phase_7a/verified_materials/`、`phase_7a/chart_materials/` → TECH-DELTA-02/03/05/06
- Huey worker：P7A 新增 fetch/verify 任务类型 → TECH-DELTA-05
- 出站网关：KeyframeRenderAgent 限流白名单配置 → TECH-DELTA-07

### SPEC-C（backend core / services / reviewers）

- 新增服务：`NarrationMasterAssembler`、`AudioMixPreviewService`、`BgmMixRenderer`、`SfxSegmentMixService`、`FinalAudioAssembler` → TECH-DELTA-01/02/03
- Reviewer 升级：`MusicFitReviewer` 新增 3 项 L1；`SFXReviewer` 拆为 `SfxLayoutReviewer` + `SfxMixReviewer` → TECH-DELTA-02/04
- 新增 Reviewer：`MaterialReadinessReviewer` → TECH-DELTA-05
- 新增前置检查：`MaterialReadinessCheck`（P8 启动前）→ TECH-DELTA-07

### SPEC-D（pipeline phases）

- Gate 4 增加主文件完整性/拼接校验 → TECH-DELTA-01
- Gate 5 增加混音预览/主文件/基线切换 → TECH-DELTA-02
- Gate 6 增加布局层 + 加工分段 + 最终主文件 → TECH-DELTA-03/04
- 新增 Gate 7A → TECH-DELTA-05/06
- Gate 8 增加 material readiness 前置 → TECH-DELTA-07
- FSM 新增 phase_7a 边 + 回跳边（P8 → P7A）→ TECH-DELTA-05/07

### SPEC-E（frontend UI）

- P4 UI：主播放器 + 下载 + 分段精修 → PRD-DELTA-01 / TECH-DELTA-08
- P5 UI：混音预览播放器 + 候选比较 + 确认后主播放器 → PRD-DELTA-02/03 / TECH-DELTA-08
- P6 UI：全文脚本标注视图 + 编号片段试听 + 最终音频 → PRD-DELTA-04/05 / TECH-DELTA-08
- P7A UI：Shot × Material 矩阵 + chart 时间范围/axis_spec 确认卡 → PRD-DELTA-06/07 / TECH-DELTA-08
- 新增类型：`MasterAudioView` / `AnnotationSpan` / `ShotMaterialBindingView` → TECH-DELTA-08

### SPEC-F（media render）

- `TemplateProps` 扩展 `chart_material` 字段 → TECH-DELTA-06
- 渲染输入校验：冲突时以 `chart_material` 为准 → TECH-DELTA-06
- KeyframeRenderAgent 禁用外部出站（白名单）+ 降级策略二分 → TECH-DELTA-07

---

## 4. 下一步建议

1. 按 SPEC-A..F 分组将上述增改项落入对应 SPEC 文档（v3.17 修订表章节）
2. 按 DELTA-ID 派生 task cards：
   - A 层先行：schema + migration 任务
   - C 层并行：5 个新服务 + 2 个新 Reviewer + 拆分 SFXReviewer
   - D 层：Gate / FSM 升级
   - E 层：四阶段 UI contract 实现
   - F 层：模板 props 扩展 + 出站白名单
3. 集成测试用 §23.9 的 10 条验收门禁作为基准
4. BDD feature 文件按本轮新增场景补入 e2e 验收（已在 BDD 层完成，无需重做）

---

## 5. 约定

- 本次改动在文档中统一标注 `v3.17-AudioMaster` 或 `v3.17-P7A`，便于 grep 定位
- 对应 PRD 原文中以 blockquote 形式给出增强说明，保留 v3.15/v3.16 既有内容
- TECH_PLAN 所有新增内容封闭于 §23 章节，不干扰 §22 之前的既有结构

> 本文档是 SPEC / task 增改的"索引表"，不替代 SPEC 本身。每项落地后在对应 SPEC 的 v3.17 修订表中打勾。
