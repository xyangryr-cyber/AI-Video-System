# Prototype Index — Components ↔ SPEC-E Cards ↔ Delta Tags

Snapshot date: 2026-04-17
Prototype root: `prototype/src/`

## File Sizes (lines)

| File | Lines |
|---|---|
| `src/App.tsx` | 31 |
| `src/types.ts` | 25 |
| `src/pages/NewProject.tsx` | 96 |
| `src/pages/ProjectList.tsx` | 151 |
| `src/pages/ProjectWorkflow.tsx` | 431 |
| `src/pages/Settings.tsx` | 193 |
| `src/components/PhaseViews.tsx` | 731 |

All files are within HARNESS §6 limits (300 lines max for TS). `PhaseViews.tsx` at 731 lines exceeds the 300-line limit — will require splitting when reimplementing in `src/frontend/`.

---

## Page Map

| Prototype File | SPEC-E Card(s) | Diff Summary | Tags |
|---|---|---|---|
| `src/App.tsx` | (routing — no single card) | Uses in-memory `useState` routing (`RouteType = 'list' \| 'new' \| 'workflow' \| 'settings'`); no URL history, no `<Link>`, no browser back/forward support. SPEC-E-002 AC-4 requires `browser navigates to /projects/{id}` (URL change). SPEC-E-003 AC-1 requires page load to trigger `GET /projects/{id}/state` (only meaningful with URL-based routing). Production frontend will use Next.js file-based routing per TECH_PLAN. | T2 |
| `src/types.ts` | E-001, E-015 | `Project` interface uses camelCase fields (`currentPhase`, `updatedAt`) vs SPEC-A snake_case (`current_phase`, `updated_at`). Adds `category: string` and `progress: number` (0-100) not present in `ProjectInfo` (SPEC-A-002). Status enum adds `'awaiting_user'` value not in `ProjectStatus` (current values: `'active' \| 'completed' \| 'archived'`). `PHASES` constant defines 13 entries (P0..P12) but `ProjectInfo.current_phase` is typed `0..11` in SPEC-A; prototype displays 13 tabs (P0..P12 = 13 phases). | T3 |
| `src/pages/ProjectList.tsx` | E-001 | Table layout (6 columns: title, category, phase, progress, status, updated_at) matches AC-1 field list. `updatedAt` displayed as relative time string (e.g. "10 分钟前") per AC-3. Progress shown as a blue bar (AC-2 visual). Status rendered with lucide-react icons (Play/Clock/CheckCircle/AlertCircle) + Chinese text — icons not mentioned in E-001 but consistent with general SPEC-E spirit (T1). Category column shows badge with `bg-slate-100` pill — SPEC-E lists category as plain text in AC-1 (T1). `progress` field is rendered as visual bar but read from `Project.progress` (0-100 integer) rather than computed as `current_phase / 12` — AC-2 says bar reflects `current_phase / 12`, so the data model diverges (T3). Data is mock (hard-coded `mockProjects` array); no `useProjects` hook, no WebSocket subscription (AC-5 missing, T2). Navigation is local-state push, not URL routing (T2). | T1 + T2 + T3 |
| `src/pages/NewProject.tsx` | E-002 | Two-field form (title + description textarea) matches AC-1. Client-side `description.length < 10` guard matches AC-2. On submit: 800ms `setTimeout` simulates API call, then calls `onNavigate('workflow', 'new_proj_123')` — no real `POST /api/projects` call (AC-3 missing, T2). Hardcodes destination project ID `'new_proj_123'` (T2). Phase navigation is not visible on this page, so AC-5 (P0 highlighted on arrival) cannot be verified here — it lives in `ProjectWorkflow.tsx`. Cancel button navigates to `'list'`. No `useCreateProject` hook. | T2 |
| `src/pages/ProjectWorkflow.tsx` | E-003, E-005, E-006, E-007, E-008, E-010, E-011, E-012, E-013 | Three-panel layout (left: phase nav sidebar; center: chat terminal + input; right: artifact preview + task ledger). Phase nav is a narrow 64px column with icon buttons P0..P12 — matches SPEC-E phase navigation concept (AC-3, AC-4 of E-003). Left sidebar also contains a "Veritas Ledger" button (ShieldCheck icon) opening a modal — this is the data verification surface, corresponding to E-006 (DataVerificationPanel), but rendered as a modal rather than a persistent sidebar panel (T2). Clicking Veritas shows factual data entries with `id`, `content`, `usage`, `source`, `link`, `verified`, `method` fields — `usage` and `link` fields not present in E-006 AC-2 schema (T3). Center panel shows a mock chat conversation (hardcoded messages) + sticky textarea for user feedback + "确认进入下一阶段" button — interaction is all local state (`isAwaitingUser`), no `POST /api/projects/{id}/chat` or event bus (T2). GateKeeper status line shows "所有准入审核已通过" (hardcoded, no real review_status from ProjectState, T2). Preference modal (shown inline in chat on phase advance) captures a learning rule with single/permanent scope radio — corresponds loosely to E-004 preferences tab but lives inside workflow page (T1 + T2). Right panel top = artifact preview area dispatching `renderPhaseView()` by `viewingPhaseIndex` — matches E-005 PhasePreviewRouter concept (AC-1). Right panel bottom = "Stage Monitor" task ledger with 3 hardcoded task rows (completed/running/pending) — maps to E-008 AgentActivityPanel concept but format is `(icon, label, agent/status)` not `[HH:MM:SS] [agent_name] [action] [result]` per E-008 AC-1 (T1 + T2). No `useProjectState` hook, no `GET /projects/{id}/state` fetch on load (E-003 AC-1 missing, T2). No ArtifactStatusBadge in phase nav items (E-007 AC-4 missing). No CandidateSelector component (E-010 missing). No ErrorToast/ErrorModal (E-009 missing). Phase count is 13 (P0..P12) vs SPEC-A `current_phase` 0..11 (T3). | T1 + T2 + T3 |
| `src/pages/Settings.tsx` | E-004 | Three tabs: "API 密钥配置", "模型与策略", "偏好全局快照". SPEC-E-004 AC-1 requires four tabs: API Config, Preferences, Brand Kit, Version History. Prototype is missing Brand Kit tab and Version History tab (T2 + T3). API Config tab reads model config from dropdowns (LLM engine, Intent Router model, TTS provider) — matches spirit of E-004 AC-2 but uses hardcoded options, no `GET /api/settings` call (T2). Temperature slider and max_attempts input in Models tab match E-004 AC-2 model_config editing concept. "偏好全局快照" tab renders a read-only monospace markdown snapshot (`snapshot.md`), shows "重新导出" button and "导出并下载 snapshot.md" link — corresponds to E-004 AC-3 Preferences tab but is read-only (no `PUT /api/settings/preferences` editing, T2). No version history or rollback (AC-5, AC-6, AC-7 missing, T2). Tabs labeled in Chinese vs English slugs in SPEC-E. | T1 + T2 |
| `src/components/PhaseViews.tsx` | E-005, E-011, E-012, E-013, E-014 | Contains 13 exported components (Phase0Requirements..Phase12Final). Key observations per phase: **P0**: 2×2 grid (主题/标题, 分类定位, 目标受众时长, 发布平台策略) + description textarea — matches E-005 SPEC-2.6 structured form view; adds `发布平台策略` (platform badges: Bilibili/Douyin) not in ProjectInfo schema (T3). **P1**: Outline segments rendered as numbered cards — matches E-005 rich text concept. **P2**: Two script paragraphs with `重写此段` button, FactChecker verified badge per data point, hover tooltip showing source and "FactChecker 验证通过" — matches E-006 data verification inline concept; inline `trust_level` display without DataVerificationPanel (T1 + T2). **P3**: Polished script with `Style Applied: 亲切科普型` badge + word count + duration (`2450字 / 预计 10分12秒`) — `style_applied` and word-count/duration metadata fields not in current SPEC-A PhaseState (T3). **P4**: Per-segment audio rows with Play button, mock waveform bars, CPS label, duration — matches E-011 MasterAudioPlayer intent (AC-1: waveform + play/pause + progress); Download button present (AC-2 ✓); no `master_audio_url` prop from API (T2); no WebSocket reload (E-011 AC-3 missing, T2); no `aria-label` (E-011 AC-5 missing, T1); segment list lacks skeleton state for missing master_audio (E-011 AC-6, T2). **P5**: Mood/energy curve bar chart + single BGM track with "Corporate Tech Cinematic" label, CC-BY badge, Ducking envelope info, Review Agent verdict badge; no multi-candidate A/B comparison grid (E-012 AC-1 missing, T2); no `preview_url` / `raw_bgm_url` dual audio entry points (E-012 AC-1, T3); no `fit_review` aggregate badge (E-012 AC-5, T2). **P6**: Two-part layout — full-text annotation with SFX tooltip hover (hover shows effect name + rationale) + per-segment mix preview rows; annotation tooltips include `rationale` and `effect` fields (maps to E-013 AC-1 annotation_spans); no `narrative_role` in tooltip (T3); no Step1 → Step2 → Step3 forced pipeline (E-013 AC-5, T2); no `user_confirmed_layout` gate (E-013 AC-2, T2); no WebSocket `segment.remixed` reload (E-013 AC-3, T2). **P7**: Storyboard timeline cards (S1E1, S1E2, S2E1, S3E1) with fields: `id`, `time`, `script`, `visualType` (B-Roll/Template), `visual`, `info`, `effect` — partial overlap with E-014 Shot×Material matrix; no `verification_status` 4-color cell grid (T2); no `MaterialDetailDrawer` (E-014 AC-2, T2); no `ChartMaterialConfirmCard` axis_spec confirmation (E-014 AC-3, T2); `"针对 {id} 提修改要求"` button matches feedback intent but maps to no API call (T2). **P8**: Reuses storyboard data with `assetStatus` ('not_needed'/'fetched') + `assetDetail` (need/action/data JSON) — asset sourcing result display, no equivalent in current SPEC-E cards beyond E-014 broadly. `assetStatus` enum values not in SPEC-A (T3). **P9**: Render status per storyboard item ('pending_broll'/'rendered') + thumbnail/video placeholder — keyframe gallery, corresponds to E-005 P9 thumbnail gallery component; `renderStatus` field not in SPEC-A PhaseState (T3). **P10**: B-Roll video list with `broll_gold_bars.mp4`, 15s duration, `matchLabel`, license `Pexels (CC0)` — corresponds to E-005 P9BrollGallery; no struct schema in SPEC-A (T3). **P11**: Dark video player placeholder with `00:00 / 10:25` timestamp + AV sync / Tracks Mixed metadata cards — matches E-005 P10VideoPlayer concept; AV sync tolerance "< 50ms" not in SPEC-A (T3). **P12**: Final delivery screen with download buttons (B站/Douyin variants) with codec+size labels (`1080P | H.264 | 180MB`, `竖屏 | 1080x1920 | 165MB`) + SRT subtitle download — corresponds to E-005 P11FinalPlayer (AC-5: player + covers + download ✓); platform/codec/filesize fields not in SPEC-A artifact schema (T3). | T1 + T2 + T3 |

---

## Delta Tag Definitions

- **T1 — visual only**: tailwind tokens, layout, copy, icon set. Becomes a new "组件视觉与原型一致" AC on the existing SPEC-E card. No contract change.
- **T2 — interaction**: navigation, state machine, reactive hooks. May or may not require contract change; evaluate per row.
- **T3 — contract change**: new field, new event, new endpoint, renamed field, additional enum value. Goes into `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` (Task 14).

---

## T3 Summary (Contract Drift Inventory)

For Task 14 sizing. Each row = one discrete contract change to evaluate for adopt/reject/defer.

| # | Source | Current SPEC-A Shape | Prototype Addition / Change |
|---|---|---|---|
| T3-01 | `src/types.ts` `Project` | `ProjectInfo`: `project_id`, `title`, `description`, `current_phase` (0..11), `status` ('active'\|'completed'\|'archived') | Adds `category: string`, `progress: number` (0-100 independent from phase), `updatedAt: string` (relative time); renames field to camelCase; adds status `'awaiting_user'` |
| T3-02 | `src/types.ts` `PHASES` | `ProjectInfo.current_phase` range `0..11` (12 phases) | Prototype defines 13 phases (P0..P12) and `currentPhase` tracks up to 12; off-by-one in phase count |
| T3-03 | `src/pages/ProjectList.tsx` | `Project.progress` derived as `current_phase / 12` per E-001 AC-2 | Prototype stores `progress` as independent integer field (25, 15, 100) not derived from phase |
| T3-04 | `src/pages/ProjectWorkflow.tsx` Veritas modal | E-006 `DataPoint`: `value`, `source`, `trust_level`, `timestamp`, FactChecker notes | Veritas entries add `id` (F1/F2/F3), `usage` (e.g. "S2E1 / P4 / P6"), `link` (URL), `method` (verification method string); no `trust_level` enum |
| T3-05 | `src/components/PhaseViews.tsx` `Phase0Requirements` | No platform field in `ProjectInfo` or P0 artifact | Adds `发布平台策略` as a list of platforms (Bilibili, Douyin) with primary/secondary tags |
| T3-06 | `src/components/PhaseViews.tsx` `Phase3Polished` | `PhaseState` has no style or duration metadata | Adds `style_applied` string ("亲切科普型"), word count, and duration estimate (`2450字 / 预计 10分12秒`) to polished script artifact |
| T3-07 | `src/components/PhaseViews.tsx` `Phase5BGM` | E-012: `preview_url` + `raw_bgm_url` dual audio per candidate | Prototype shows single BGM track; no `preview_url`/`raw_bgm_url` dual entry, no A/B candidate grid |
| T3-08 | `src/components/PhaseViews.tsx` `Phase6SFX` | E-013 `annotation_spans`: `rationale` + `narrative_role` per span | Prototype tooltip shows `effect` name + `rationale` but not `narrative_role`; missing field |
| T3-09 | `src/components/PhaseViews.tsx` `Phase8AssetSourcing` | No asset sourcing status in SPEC-A | Adds `assetStatus` enum ('not_needed'\|'fetched') + `assetDetail` struct (need, action, data) per storyboard shot |
| T3-10 | `src/components/PhaseViews.tsx` `Phase9Keyframes` | No render status in SPEC-A PhaseState | Adds `renderStatus` enum ('pending_broll'\|'rendered') + `fileName` per keyframe shot |
| T3-11 | `src/components/PhaseViews.tsx` `Phase10BRoll` | No B-Roll metadata in SPEC-A | Adds B-Roll item struct: `fileName`, `duration` (seconds), `matchLabel`, `license` (e.g. "Pexels (CC0)") |
| T3-12 | `src/components/PhaseViews.tsx` `Phase11RoughCut` | No AV sync spec in SPEC-A | Adds AV sync tolerance "< 50ms" and tracks-mixed description as displayed metadata |
| T3-13 | `src/components/PhaseViews.tsx` `Phase12Final` | No per-platform delivery spec in SPEC-A artifact | Adds platform variants: `platform` (Bilibili/Douyin), `resolution`, `codec`, `aspect_ratio`, `file_size_mb` per download |

**Total T3 count: 13**

---

## Cards Without a Prototype Surface

These SPEC-E cards have no direct corresponding prototype file or component. They proceed unmodified without visual reference from the prototype.

| Card | Reason |
|---|---|
| E-003 (State Recovery) | Prototype has no real API call on load; state recovery logic is entirely absent. Card drives `useProjectState` hook and loading/error states — no prototype surface to compare against. |
| E-007 (Artifact Status Badge) | Phase nav items in prototype show no `artifact_status` badge (ok/damaged/missing). The badge component does not exist in the prototype. |
| E-008 (Agent Activity Panel) | Prototype "Stage Monitor" shows 3 hardcoded task rows but format (`icon + label + agent/status`) differs from E-008 AC-1 `[HH:MM:SS] [agent_name] [action] [result]`. Real-time WebSocket events, pagination, and reconnect gap-fill are entirely absent. |
| E-009 (Error UX Map) | No error states, toasts, or modals exist anywhere in the prototype. The 3-tier ERROR_UX_MAP and all error components have no prototype surface. |
| E-010 (CandidateSelector) | No candidate selection UI exists in the prototype. P4/P5/P6/P8/P9 phases show single-track outputs with no A/B comparison or two-step confirmation flow. |
| E-011 (P4 Master Player) | P4 shows per-segment dry audio rows, but no top-level master waveform player, no `master_audio_url` prop, no WebSocket `master_audio.updated` subscription, no a11y attributes. |
| E-012 (P5 Mix Preview + Master) | P5 shows a single BGM track; no dual `preview_url`/`raw_bgm_url` per candidate, no A/B/C comparison grid, no Phase5MasterPlayer, no `fit_review` aggregate badge. |
| E-013 (P6 Annotation + Final Audio) | P6 annotation hover shows `rationale`+`effect` but lacks `narrative_role`. Step1→Step2→Step3 forced pipeline (`user_confirmed_layout` gate, `segment.remixed` WebSocket) is entirely absent. |
| E-014 (P7A Shot×Material Matrix) | P7 shows a linear storyboard timeline, not the Shot×Material matrix grid with 4-color `verification_status`. No `MaterialDetailDrawer`, no `ChartMaterialConfirmCard` axis_spec confirmation, no P7A-specific components. |
| E-015 (Frontend Types) | Type files (`audio_master.ts`, `annotation_span.ts`, `shot_material_binding.ts`, `chart_material.ts`) do not exist in the prototype. This is a pure implementation task with no prototype reference. |

---

## Notes on `PhaseViews.tsx` Split Requirement

`PhaseViews.tsx` at 731 lines exceeds HARNESS §6 300-line limit. When reimplementing in `src/frontend/`, this file must be split into individual files per SPEC-E-005's `allowed_files` list (13 separate component files under `src/frontend/components/previews/`). The 13 prototype exports map directly to the 13 allowed files in E-005.
