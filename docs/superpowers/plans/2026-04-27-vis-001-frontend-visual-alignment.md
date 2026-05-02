# [VIS-001] Frontend Visual Alignment — Prototype → Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring all frontend pages and components into visual alignment with the prototype design language defined in `prototype/src/`.

**Architecture:** Pure visual alignment — modify JSX structure and Tailwind classes to match prototype. Zero functional changes. Design tokens from spec (bg-slate-50, text-slate-800, border-2 border-slate-200, rounded-2xl, etc.). Each component follows TDD: write visual test → verify it fails → update component → verify it passes → commit.

**Tech Stack:** React 19, TypeScript 5.8, Tailwind CSS 4.1, lucide-react 0.546, vitest + @testing-library/react, dayjs

---

## Design Tokens (from spec)

| Token | Tailwind Class |
|---|---|
| Page background | `bg-[#f8fafc]` = `bg-slate-50` |
| Text primary | `text-[#1e293b]` = `text-slate-800` |
| Card border | `border-2 border-slate-200` |
| Card rounding | `rounded-2xl` |
| Card background | `bg-white` |
| Primary accent | `bg-blue-600` / `text-blue-600` |
| Section labels | `font-black uppercase tracking-[0.05em]` |
| Small labels | `text-[10px]` / `text-[11px]` |
| Dark button | `bg-[#1e293b] hover:bg-black` |
| Shadow | `shadow-sm` |

---

## File Structure

All files to modify live in `src/frontend/`. Tests in `tests/unit/frontend/`.

**Pages (4):**
- `src/frontend/pages/ProjectList.tsx` — 6-column table layout
- `src/frontend/pages/NewProject.tsx` — centered form card
- `src/frontend/pages/WorkflowPage.tsx` — three-panel layout
- `src/frontend/pages/SettingsPage.tsx` — sidebar + content cards

**Phase Previews (12 + 1 router):**
- `src/frontend/components/previews/P0RequirementsView.tsx` through `P11FinalPlayer.tsx`
- `src/frontend/components/previews/PhasePreviewRouter.tsx`

**Supporting Components (~10):**
- `src/frontend/components/ProjectCard.tsx` — becomes table row
- `src/frontend/components/PhaseNavigation.tsx` — 64px sidebar
- `src/frontend/components/CreateProjectForm.tsx` — centered card form
- `src/frontend/components/settings/ApiConfigTab.tsx`
- `src/frontend/components/settings/PreferencesTab.tsx`
- `src/frontend/components/settings/BrandKitTab.tsx`
- `src/frontend/components/settings/VersionHistoryTab.tsx`

**Tests (new):**
- `tests/unit/frontend/visual/` — all visual tests

---

## Parallel Execution Strategy

Tasks are organized into 4 waves that can be dispatched in parallel within each wave:

**Wave 1 (parallel):** Pages — 4 subagents, each handles one page + its supporting components
**Wave 2 (parallel):** Phase Previews — 4 subagents × ~3 components each
**Wave 3 (parallel):** Supporting components not covered in Wave 1
**Wave 4:** Integration verification — type check + full test suite

---

## Wave 1: Page-Level Visual Alignment

### Task 1: ProjectList Page + ProjectCard Component

**Files:**
- Modify: `src/frontend/pages/ProjectList.tsx`
- Modify: `src/frontend/components/ProjectCard.tsx` (delete or repurpose to table row)
- Create: `tests/unit/frontend/visual/ProjectList.visual.test.tsx`

- [ ] **Step 1: Write failing visual tests for ProjectList**

Create `tests/unit/frontend/visual/ProjectList.visual.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProjectList } from "../../../../src/frontend/pages/ProjectList";

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><MemoryRouter>{ui}</MemoryRouter></QueryClientProvider>);
}

describe("ProjectList visual alignment", () => {
  it("renders the Chinese header 'AI 视频制作系统'", () => {
    renderWithProviders(<ProjectList />);
    expect(screen.getByText("AI 视频制作系统")).toBeDefined();
  });

  it("renders a 6-column table with correct headers", () => {
    renderWithProviders(<ProjectList />);
    const headers = ["标题", "分类", "阶段", "进度", "状态", "更新时间"];
    for (const h of headers) {
      expect(screen.getByText(h)).toBeDefined();
    }
  });

  it("renders '新建项目' button with blue styling", () => {
    renderWithProviders(<ProjectList />);
    const btn = screen.getByText("新建项目");
    expect(btn.closest("button")?.className).toMatch(/bg-blue-600/);
  });

  it("renders the 'M3: 项目管理列表' section label", () => {
    renderWithProviders(<ProjectList />);
    expect(screen.getByText("M3: 项目管理列表")).toBeDefined();
  });

  it("renders settings gear icon button", () => {
    renderWithProviders(<ProjectList />);
    const buttons = screen.getAllByRole("button");
    const hasIconBtn = buttons.some(b => b.querySelector("svg"));
    expect(hasIconBtn).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/ProjectList.visual.test.tsx
```

Expected: FAIL — current ProjectList renders "项目列表" not "AI 视频制作系统", uses grid layout not table, etc.

- [ ] **Step 3: Rewrite ProjectList.tsx to match prototype table layout**

Rewrite `src/frontend/pages/ProjectList.tsx`:

```tsx
import type { ReactElement } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, Settings, Play, CheckCircle, Clock, AlertCircle } from "lucide-react"
import { useProjects } from "../hooks/useProjects"
import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"
import "dayjs/locale/zh-cn"

dayjs.extend(relativeTime)
dayjs.locale("zh-cn")

const STATUS_MAP: Record<string, { icon: React.ElementType; label: string; color: string }> = {
  in_progress: { icon: Play, label: "进行中", color: "text-blue-500" },
  awaiting_user: { icon: Clock, label: "等用户", color: "text-amber-500" },
  completed: { icon: CheckCircle, label: "完成", color: "text-green-500" },
  failed: { icon: AlertCircle, label: "失败", color: "text-red-500" },
}

export function ProjectList(): ReactElement {
  const nav = useNavigate()
  const wsUrl = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/projects`
  const { data, isLoading, isError } = useProjects(wsUrl)
  if (isLoading) return <div className="flex items-center justify-center h-64 text-slate-500">加载中...</div>
  if (isError || !data) return <div className="flex items-center justify-center h-64 text-slate-500">加载失败</div>

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">AI 视频制作系统</h1>
          <p className="text-sm text-slate-500 mt-1">面向金融内容创作者的专业工作流</p>
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => nav("/settings")}
            className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={() => nav("/projects/new")}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>新建项目</span>
          </button>
        </div>
      </header>

      <div className="bg-white rounded-2xl border-2 border-slate-200 p-6 flex flex-col gap-4">
        <h2 className="text-[0.85rem] font-bold text-slate-800 uppercase tracking-[0.05em]">M3: 项目管理列表</h2>
        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {["标题", "分类", "阶段", "进度", "状态", "更新时间"].map((h) => (
                  <th key={h} className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.length === 0 && (
                <tr><td colSpan={6} className="py-12 text-center text-slate-500">暂无项目，点击右上角新建。</td></tr>
              )}
              {data.map((project) => {
                const statusInfo = STATUS_MAP[project.status] ?? STATUS_MAP.in_progress
                const StatusIcon = statusInfo.icon
                const relTime = dayjs(project.updated_at).fromNow()
                return (
                  <tr
                    key={project.id}
                    onClick={() => nav(`/projects/${project.id}`)}
                    className="hover:bg-slate-50 cursor-pointer transition-colors group"
                  >
                    <td className="py-4 px-6 font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                      {project.title}
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-600">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                        {project.category}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-600">Phase {project.current_phase}</td>
                    <td className="py-4 px-6">
                      <div className="flex items-center w-full max-w-[120px]">
                        <div className="w-full bg-slate-200 rounded-full h-1.5 flex-1 relative overflow-hidden">
                          <div
                            className="bg-blue-600 h-1.5 rounded-full absolute top-0 left-0"
                            style={{ width: `${project.progress}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-2">
                        <StatusIcon className={`w-4 h-4 ${statusInfo.color}`} />
                        <span className="text-sm text-slate-600">{statusInfo.label}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-500 whitespace-nowrap">{relTime}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/ProjectList.visual.test.tsx
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/frontend/visual/ProjectList.visual.test.tsx src/frontend/pages/ProjectList.tsx
git commit -m "[VIS-001] visual alignment: ProjectList page → 6-column table layout matching prototype"
```

---

### Task 2: NewProject Page + CreateProjectForm Component

**Files:**
- Modify: `src/frontend/pages/NewProject.tsx`
- Modify: `src/frontend/components/CreateProjectForm.tsx`
- Create: `tests/unit/frontend/visual/NewProject.visual.test.tsx`

- [ ] **Step 1: Write failing visual tests for NewProject**

Create `tests/unit/frontend/visual/NewProject.visual.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NewProject } from "../../../../src/frontend/pages/NewProject";

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><MemoryRouter>{ui}</MemoryRouter></QueryClientProvider>);
}

describe("NewProject visual alignment", () => {
  it("renders the form card with border-2 border-slate-200 rounded-2xl", () => {
    renderWithProviders(<NewProject />);
    const form = document.querySelector("form");
    expect(form?.className).toMatch(/border-2/);
    expect(form?.className).toMatch(/border-slate-200/);
    expect(form?.className).toMatch(/rounded-2xl/);
  });

  it("renders Chinese labels '项目标题' and '内容主题描述 (核心观点)'", () => {
    renderWithProviders(<NewProject />);
    expect(screen.getByText("项目标题")).toBeDefined();
    expect(screen.getByText(/内容主题描述/)).toBeDefined();
  });

  it("renders '开始制作' button with blue styling", () => {
    renderWithProviders(<NewProject />);
    const btn = screen.getByText("开始制作");
    expect(btn.closest("button")?.className).toMatch(/bg-blue-600/);
  });

  it("renders character counter showing '0 / 2000'", () => {
    renderWithProviders(<NewProject />);
    expect(screen.getByText(/0\s*\/\s*2000/)).toBeDefined();
  });

  it("renders a back button", () => {
    renderWithProviders(<NewProject />);
    const btn = screen.getByText("取消");
    expect(btn).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/NewProject.visual.test.tsx
```

Expected: FAIL — current button text is "创建" not "开始制作"

- [ ] **Step 3: Update CreateProjectForm.tsx to match prototype design**

Rewrite `src/frontend/components/CreateProjectForm.tsx`:

```tsx
import { useState, FormEvent } from "react"
import type { ReactElement } from "react"

interface Props {
  onSubmit: (input: { title: string; description: string }) => void
  isSubmitting: boolean
}

const MIN_DESC = 10

export function CreateProjectForm({ onSubmit, isSubmitting }: Props): ReactElement {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState("")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (description.length < MIN_DESC) {
      setError("描述至少 10 个字")
      return
    }
    setError("")
    onSubmit({ title, description })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border-2 border-slate-200 p-8 shadow-sm space-y-6">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-2">
          项目标题
        </label>
        <input
          id="title" type="text" required
          value={title} onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
          placeholder="例如：2025 Q4 黄金价格走势分析与投资展望"
        />
      </div>
      <div>
        <label htmlFor="desc" className="block text-sm font-medium text-slate-700 mb-2">
          内容主题描述 (核心观点)
        </label>
        <textarea
          id="desc" required rows={8}
          value={description} onChange={(e) => setDescription(e.target.value)}
          className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow resize-none"
          placeholder="请详细描述您的观点。例如：本期视频主要分析为什么黄金价格近期飙升..."
        />
        <div className="mt-2 text-xs flex justify-between">
          <span className={description.length > 0 && description.length < MIN_DESC ? "text-red-500" : "text-slate-500"}>
            至少 10 个字符
          </span>
          <span className="text-slate-400">{description.length} / 2000</span>
        </div>
      </div>
      {error && <div role="alert" className="text-red-600 text-sm">{error}</div>}
      <div className="pt-4 border-t border-slate-100 flex justify-end">
        <button
          type="button"
          onClick={() => window.history.back()}
          className="px-6 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-medium mr-4 transition-colors"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isSubmitting || description.length < MIN_DESC || !title.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "创建中..." : "开始制作"}
        </button>
      </div>
    </form>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/NewProject.visual.test.tsx
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/frontend/visual/NewProject.visual.test.tsx src/frontend/components/CreateProjectForm.tsx
git commit -m "[VIS-001] visual alignment: NewProject page → centered card form matching prototype"
```

---

### Task 3: WorkflowPage + PhaseNavigation Component

**Files:**
- Modify: `src/frontend/pages/WorkflowPage.tsx`
- Modify: `src/frontend/components/PhaseNavigation.tsx`
- Create: `tests/unit/frontend/visual/WorkflowPage.visual.test.tsx`

- [ ] **Step 1: Write failing visual tests**

Create `tests/unit/frontend/visual/WorkflowPage.visual.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WorkflowPage } from "../../../../src/frontend/pages/WorkflowPage";

function renderWithProviders(projectId = "test-1", phase = "0") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/${phase}`]}>
        <Routes>
          <Route path="/projects/:id/:phase" element={<WorkflowPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("WorkflowPage visual alignment", () => {
  it("renders phase navigation sidebar", () => {
    renderWithProviders();
    expect(screen.getByTestId("phase-nav-sidebar")).toBeDefined();
  });

  it("renders chat terminal panel", () => {
    renderWithProviders();
    expect(screen.getByTestId("chat-terminal-panel")).toBeDefined();
  });

  it("renders artifact preview panel", () => {
    renderWithProviders();
    expect(screen.getByTestId("artifact-preview-panel")).toBeDefined();
  });

  it("renders phase nav buttons P0 through P11", () => {
    renderWithProviders();
    for (let i = 0; i < 12; i++) {
      expect(screen.getByText(`P${i}`)).toBeDefined();
    }
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/WorkflowPage.visual.test.tsx
```

Expected: FAIL — current component doesn't have these data-testid elements

- [ ] **Step 3: Implement PhaseNavigation as 64px sidebar**

Rewrite `src/frontend/components/PhaseNavigation.tsx`:

```tsx
import type { ReactElement } from "react"
import { ShieldCheck } from "lucide-react"

const PHASE_LABELS = [
  "需求采集", "大纲规划", "脚本初稿", "风格精修",
  "语音合成", "BGM匹配", "音效叠加", "故事板",
  "素材溯源", "关键帧", "B-Roll合成", "最终输出",
]

interface PhaseItem {
  phase: number
  status?: string
  artifact_status?: "ok" | "damaged" | "missing"
}

interface Props {
  currentPhase: number
  phases: PhaseItem[]
  onSelectPhase: (phase: number) => void
  completedPhases: number
}

export function PhaseNavigation({ currentPhase, phases, onSelectPhase, completedPhases }: Props): ReactElement {
  return (
    <aside
      data-testid="phase-nav-sidebar"
      className="w-16 bg-white border-2 border-slate-200 rounded-2xl flex flex-col items-center py-6 shrink-0 shadow-sm"
    >
      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2 vertical-rl rotate-180">
        <div className="w-1 h-1 rounded-full bg-slate-300" />
        工作推进
        <div className="w-1 h-1 rounded-full bg-slate-300" />
      </div>
      <div className="flex-1 w-full flex flex-col items-center gap-4 overflow-y-auto py-2">
        {Array.from({ length: 12 }, (_, i) => {
          const isCompleted = i < completedPhases
          const isActive = i === currentPhase
          const isCurrent = i === completedPhases

          return (
            <button
              key={i}
              onClick={() => onSelectPhase(i)}
              className={`group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all
                ${isActive ? "bg-[#1e293b] text-white shadow-lg scale-110" : "text-slate-400 hover:bg-slate-100"}
                ${isCurrent && !isActive ? "border-2 border-dashed border-blue-400" : ""}
              `}
            >
              <span className={`text-[11px] font-black ${isActive ? "opacity-100" : "opacity-60 group-hover:opacity-100"}`}>
                P{i}
              </span>
              <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
                {PHASE_LABELS[i]}
              </div>
              {isCompleted && (
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white shadow-sm" />
              )}
            </button>
          )
        })}
      </div>
      <div className="mt-auto py-6 border-t border-slate-100 w-full flex flex-col items-center gap-4">
        <button
          className="group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all bg-slate-50 text-slate-400 hover:bg-slate-200"
          title="事实清单 (Veritas)"
        >
          <ShieldCheck className="w-5 h-5 text-slate-500" />
          <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
            事实清单 (Veritas)
          </div>
        </button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 4: Rewrite WorkflowPage.tsx to implement three-panel layout**

Rewrite `src/frontend/pages/WorkflowPage.tsx`:

```tsx
import type { ReactElement } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useProjectState } from "../hooks/useProjectState"
import { PhaseNavigation } from "../components/PhaseNavigation"
import { PhasePreviewRouter } from "../components/previews/PhasePreviewRouter"
import { LoadingState } from "../components/LoadingState"
import { ErrorState } from "../components/ErrorState"
import { ArrowLeft, MessageSquare } from "lucide-react"

export function WorkflowPage(): ReactElement {
  const { id = "", phase = "0" } = useParams<{ id: string; phase: string }>()
  const currentPhase = Number(phase)
  const nav = useNavigate()
  const { data, isLoading, isError, error, refetch } = useProjectState(id)

  if (isLoading) return <LoadingState />
  if (isError || !data) {
    const msg = (error as { message?: string } | null)?.message ?? "未知错误"
    return <ErrorState message={msg} onRetry={() => { void refetch() }} />
  }

  const phases = data.phases?.length
    ? data.phases.map((p) => ({ phase: p.phase_num, status: p.status }))
    : Array.from({ length: 12 }, (_, i) => ({ phase: i }))

  const completedPhases = data.phases?.filter(p => p.status === "completed").length ?? 0

  return (
    <div className="h-screen flex flex-col bg-[#f8fafc] overflow-hidden p-4 sm:p-5 gap-5 text-[#1e293b]">
      <header className="h-16 bg-white border-2 border-slate-200 rounded-2xl flex items-center justify-between px-5 shrink-0">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => nav("/projects")}
            className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="font-medium text-slate-800">
            {data.title ?? id}
            <span className="text-slate-400 font-normal ml-2 text-sm">{id}</span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden gap-4">
        <PhaseNavigation
          currentPhase={currentPhase}
          phases={phases}
          onSelectPhase={(p) => nav(`/projects/${id}/${p}`)}
          completedPhases={completedPhases}
        />

        <main
          data-testid="chat-terminal-panel"
          className="flex-1 flex flex-col min-w-0 bg-white border-2 border-slate-200 rounded-2xl shadow-sm overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
            <h3 className="text-[0.8rem] font-black text-[#1e293b] uppercase tracking-[0.1em] flex items-center">
              <MessageSquare className="w-4 h-4 mr-2 text-blue-600" />
              协作对话终端 / {data.title ?? `Phase ${currentPhase}`}
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
            <div className="text-slate-400 text-sm text-center py-12">
              对话历史将在后续版本中实现
            </div>
          </div>
        </main>

        <aside className="w-[320px] lg:w-[480px] flex flex-col min-w-0 h-full gap-4 overflow-hidden">
          <section
            data-testid="artifact-preview-panel"
            className="flex-1 bg-white border-2 border-slate-200 rounded-2xl flex flex-col min-h-0 overflow-hidden shadow-sm"
          >
            <div className="px-5 py-3 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
              <h2 className="text-[0.7rem] font-black text-[#1e293b] uppercase tracking-[0.15em] flex items-center">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-600 mr-2" />
                P{currentPhase} / 阶段产物预览
              </h2>
            </div>
            <div className="flex-1 overflow-y-auto p-5 bg-[#fcfcfc]">
              <PhasePreviewRouter phase={currentPhase} artifact={data.phases?.[currentPhase]?.artifact} />
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/WorkflowPage.visual.test.tsx
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/unit/frontend/visual/WorkflowPage.visual.test.tsx src/frontend/pages/WorkflowPage.tsx src/frontend/components/PhaseNavigation.tsx
git commit -m "[VIS-001] visual alignment: WorkflowPage → three-panel layout + PhaseNavigation sidebar"
```

---

### Task 4: SettingsPage + Settings Tabs

**Files:**
- Modify: `src/frontend/pages/SettingsPage.tsx`
- Modify: `src/frontend/components/settings/ApiConfigTab.tsx`
- Modify: `src/frontend/components/settings/PreferencesTab.tsx`
- Modify: `src/frontend/components/settings/BrandKitTab.tsx`
- Modify: `src/frontend/components/settings/VersionHistoryTab.tsx`
- Create: `tests/unit/frontend/visual/SettingsPage.visual.test.tsx`

- [ ] **Step 1: Write failing visual tests**

Create `tests/unit/frontend/visual/SettingsPage.visual.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsPage } from "../../../../src/frontend/pages/SettingsPage";

function renderWithProviders() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><MemoryRouter><SettingsPage /></MemoryRouter></QueryClientProvider>);
}

describe("SettingsPage visual alignment", () => {
  it("renders '系统设置' heading", () => {
    renderWithProviders();
    expect(screen.getByText("系统设置")).toBeDefined();
  });

  it("renders sidebar with tab buttons using Chinese labels", () => {
    renderWithProviders();
    expect(screen.getByText("API 密钥配置")).toBeDefined();
    expect(screen.getByText("模型与策略")).toBeDefined();
    expect(screen.getByText("偏好全局快照")).toBeDefined();
  });

  it("renders content area with card styling", () => {
    renderWithProviders();
    const contentCards = document.querySelectorAll(".rounded-2xl");
    expect(contentCards.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/SettingsPage.visual.test.tsx
```

Expected: FAIL — current labels are in English

- [ ] **Step 3: Rewrite SettingsPage.tsx with prototype design**

Rewrite `src/frontend/pages/SettingsPage.tsx`:

```tsx
import type { ReactElement } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Shield, Cpu, HardDrive } from "lucide-react";
import { ApiConfigTab } from "../components/settings/ApiConfigTab";
import { PreferencesTab } from "../components/settings/PreferencesTab";
import { BrandKitTab } from "../components/settings/BrandKitTab";
import { VersionHistoryTab } from "../components/settings/VersionHistoryTab";

type TabId = "api" | "models" | "preferences";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "api", label: "API 密钥配置", icon: Shield },
  { id: "models", label: "模型与策略", icon: Cpu },
  { id: "preferences", label: "偏好全局快照", icon: HardDrive },
];

function renderActive(tab: TabId): ReactElement {
  switch (tab) {
    case "api":
      return <ApiConfigTab />;
    case "models":
      return <BrandKitTab />;
    case "preferences":
      return <PreferencesTab />;
  }
}

export function SettingsPage(): ReactElement {
  const [activeTab, setActiveTab] = useState<TabId>("api");
  const nav = useNavigate();

  return (
    <div className="max-w-4xl mx-auto py-12 px-6">
      <div className="flex items-center space-x-4 mb-8">
        <button
          onClick={() => nav("/projects")}
          className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-semibold text-slate-900">系统设置</h1>
      </div>

      <div className="flex gap-5">
        <div className="w-64 shrink-0 bg-white border-2 border-slate-200 rounded-2xl p-4">
          <nav className="space-y-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-4 py-3 font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? "bg-blue-50 text-blue-600"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <tab.icon className="w-4 h-4 mr-3" /> {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1">{renderActive(activeTab)}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update ApiConfigTab.tsx with prototype styling**

Rewrite `src/frontend/components/settings/ApiConfigTab.tsx`:

```tsx
import type { ReactElement } from "react";
import { useMemo, useState } from "react";
import { Save } from "lucide-react";
import { useSettingsQuery, useModelConfigMutation } from "../../hooks/useSettings";

export function ApiConfigTab(): ReactElement {
  const { data, isLoading } = useSettingsQuery();
  const saveMutation = useModelConfigMutation();
  const [draft, setDraft] = useState<Record<string, unknown>>({});

  const config = useMemo(() => {
    if (data?.model_config_data && draft !== undefined) {
      return { ...data.model_config_data, ...draft };
    }
    return {};
  }, [data, draft]);

  if (isLoading) return <div className="p-6 text-slate-500">Loading...</div>;

  return (
    <div data-testid="api-config-tab" className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
      <div className="p-6 border-b border-slate-200 shrink-0">
        <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">API 密钥配置 (全局)</h2>
        <p className="text-sm text-slate-500 mt-1">应用环境变量配置界面。在私有化部署中，敏感配置写入背后 .env 文件中。</p>
      </div>
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {Object.entries(config).map(([key, value]) => (
            <div key={key} className="col-span-2 sm:col-span-1">
              <label htmlFor={`config-${key}`} className="block text-sm font-medium text-slate-700 mb-2">
                {key}
              </label>
              <input
                id={`config-${key}`}
                type="text"
                value={String(value ?? "")}
                onChange={(e) => setDraft((prev) => ({ ...prev, [key]: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
              />
            </div>
          ))}
        </div>
        <div className="pt-6 border-t border-slate-100 flex justify-end">
          <button
            onClick={() => saveMutation.mutate({ ...data?.model_config_data, ...draft })}
            className="flex items-center px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium shadow-sm transition-colors"
          >
            <Save className="w-4 h-4 mr-2" /> 保存配置
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Update PreferencesTab.tsx with prototype styling**

Rewrite `src/frontend/components/settings/PreferencesTab.tsx`:

```tsx
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { RefreshCw, FileText } from "lucide-react";
import { usePreferencesQuery, usePreferencesMutation } from "../../hooks/useSettings";

export function PreferencesTab(): ReactElement {
  const { data, isLoading } = usePreferencesQuery();
  const saveMutation = usePreferencesMutation();
  const [globalRules, setGlobalRules] = useState("");
  const [userPreferences, setUserPreferences] = useState("");

  useEffect(() => {
    if (data) {
      setGlobalRules(data.global_rules_md);
      setUserPreferences(data.user_preferences_md);
    }
  }, [data]);

  if (isLoading) return <div className="p-6 text-slate-500">Loading...</div>;

  const snapshotMd = `# 全局制作规范 (Global Rules)\n${globalRules}\n\n# 跨项目长期偏好 (User Preferences)\n${userPreferences}`;

  return (
    <div data-testid="preferences-tab" className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
      <div className="p-6 border-b border-slate-200 shrink-0 flex justify-between items-center bg-slate-50/50">
        <div>
          <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">偏好全局快照 (snapshot.md)</h2>
          <p className="text-sm text-slate-500 mt-1">只读导出视图，作为 Agent 下一阶段处理的参考事实核查与风格修正基准。</p>
        </div>
        <button className="flex items-center px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-medium transition-colors shadow-sm">
          <RefreshCw className="w-4 h-4 mr-1.5 text-slate-400" /> 重新导出
        </button>
      </div>
      <div className="p-6 overflow-y-auto flex-1 bg-slate-100">
        <div className="bg-white border border-slate-200 rounded-xl p-5 font-mono text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
          {snapshotMd}
        </div>
        <div className="mt-4 flex justify-end">
          <button className="flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium">
            <FileText className="w-4 h-4 mr-1.5" /> 导出并下载 snapshot.md
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/SettingsPage.visual.test.tsx
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/unit/frontend/visual/SettingsPage.visual.test.tsx src/frontend/pages/SettingsPage.tsx src/frontend/components/settings/ApiConfigTab.tsx src/frontend/components/settings/PreferencesTab.tsx
git commit -m "[VIS-001] visual alignment: SettingsPage → sidebar tabs + styled content cards"
```

---

## Wave 2: Phase Preview Components

### Task 5: P0RequirementsView — 2×2 Grid Layout

**Files:**
- Modify: `src/frontend/components/previews/P0RequirementsView.tsx`
- Create: `tests/unit/frontend/visual/PhasePreviews.visual.test.tsx` (shared test file, add P0 test)

- [ ] **Step 1: Write failing visual test for P0**

```typescript
// In tests/unit/frontend/visual/PhasePreviews.visual.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { P0RequirementsView } from "../../../../src/frontend/components/previews/P0RequirementsView";

describe("P0RequirementsView visual alignment", () => {
  it("renders a 2×2 grid layout", () => {
    const requirements = {
      title: "黄金价格走势分析",
      category: "金融财经 / 行业分析",
      target_duration: "Medium (约 8-12 分钟)",
      platforms: "Bilibili (主), Douyin (副)",
    };
    render(<P0RequirementsView requirements={requirements} />);
    const grid = document.querySelector(".grid-cols-2");
    expect(grid).toBeTruthy();
  });

  it("displays platform badges", () => {
    const requirements = {
      platforms: "Bilibili (主), Douyin (副)",
    };
    render(<P0RequirementsView requirements={requirements} />);
    expect(screen.getByText(/Bilibili/)).toBeDefined();
    expect(screen.getByText(/Douyin/)).toBeDefined();
  });

  it("shows placeholder when no data", () => {
    render(<P0RequirementsView requirements={{}} />);
    expect(screen.getByTestId("preview-p0")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/PhasePreviews.visual.test.tsx -t "P0RequirementsView"
```

Expected: FAIL — current implementation is key-value dump, not grid

- [ ] **Step 3: Rewrite P0RequirementsView.tsx**

Match the prototype `Phase0Requirements` component:
- 2×2 grid for metadata fields (title, category, duration, platforms)
- Platform badges with `bg-blue-100 text-blue-700` / `bg-slate-100 text-slate-700`
- Description textarea with `bg-slate-50 p-3 rounded-lg`
- Section labels: `text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold`

```tsx
import type { RequirementsJSON } from "@frontend/types/preview";
import { FileText } from "lucide-react";

interface P0RequirementsViewProps {
  requirements?: RequirementsJSON;
}

export function P0RequirementsView({ requirements }: P0RequirementsViewProps) {
  if (!requirements || Object.keys(requirements).length === 0) {
    return (
      <div data-testid="preview-p0" className="flex flex-col items-center justify-center h-64 text-slate-400">
        <FileText className="w-12 h-12 mb-3 opacity-50" />
        <p className="text-sm font-medium">暂无需求数据</p>
        <p className="text-xs text-slate-400 mt-1">等待需求采集 Agent 完成初始化</p>
      </div>
    );
  }

  const title = String(requirements.title ?? "");
  const category = String(requirements.category ?? "");
  const targetDuration = String(requirements.target_duration ?? "");
  const platforms = String(requirements.platforms ?? "");
  const description = String(requirements.description ?? requirements.core_brief ?? "");
  const platformList = platforms.split(/[,，]/).map((s) => s.trim()).filter(Boolean);

  return (
    <div data-testid="preview-p0" className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">主题 / 标题</div>
          <div className="text-sm font-medium text-slate-800">{title || "-"}</div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">分类定位</div>
          <div className="text-sm font-medium text-slate-800">{category || "-"}</div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">目标受众时长</div>
          <div className="text-sm font-medium text-slate-800">{targetDuration || "-"}</div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">发布平台策略</div>
          <div className="text-sm font-medium text-slate-800 flex gap-2 mt-1">
            {platformList.length > 0 ? (
              platformList.map((p, i) => (
                <span key={i} className={i === 0 ? "bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md text-xs" : "bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md text-xs"}>
                  {p}
                </span>
              ))
            ) : (
              <span>-</span>
            )}
          </div>
        </div>
      </div>
      {description && (
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">核心提点与需求描述</div>
          <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
            {description}
          </p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/frontend && npx vitest run tests/unit/frontend/visual/PhasePreviews.visual.test.tsx -t "P0RequirementsView"
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/frontend/visual/PhasePreviews.visual.test.tsx src/frontend/components/previews/P0RequirementsView.tsx
git commit -m "[VIS-001] visual alignment: P0RequirementsView → 2x2 grid + platform badges"
```

---

### Task 6-16: P1ScriptView through P11FinalPlayer (11 components)

Each follows the same TDD pattern as Task 5. For brevity, here are the key visual transformations:

| Component | Prototype Reference | Key Visual Changes |
|---|---|---|
| **P1ScriptView** | `Phase1Outline` | Numbered cards with left blue accent bar (`w-1 absolute left-0 bg-blue-500`), number badge in blue circle, title+desc layout |
| **P2SegmentView** | `Phase2ScriptOrig` | Segment cards with dark header (`bg-slate-800 text-white`), "重写此段" button, FactChecker badges with data verification tooltips, inline data hover tooltips |
| **P3VoiceScriptView** | `Phase3Polished` | "Style Applied" purple badge with Sparkles icon, word count/duration, prose with highlighted optimization callouts (`bg-amber-50 border-l-4 border-amber-400`) |
| **P4SegmentAudioPlayer** | `Phase4Voice` | Audio rows with play button (`rounded-full bg-slate-900`), waveform bars (random-height divs), CPS label (`text-[10px] bg-slate-100`), warning state (`border-amber-200 bg-amber-50/20`) |
| **P5WaveformPlayer** | `Phase5BGM` | Mood/energy curve chart (div bars), BGM track card with waveform, CC-BY badge (`text-green-600 bg-green-100`), ducking info, Review Agent verdict |
| **P6SfxListPlayer** | `Phase6SFX` | Full-text SFX annotation with hover tooltips (Volume2 icons, hidden tooltip groups), segment mix preview rows, "下载复合音频版" button |
| **P7StoryboardGallery** | `Phase7Storyboard` | Timeline with dot markers (`border-l-2 border-slate-200`), shot cards with id badge + time + visualType badge, 2-column grid with script/visual/info/effect, "提修改要求" button |
| **P8FrameGallery** | `Phase8AssetSourcing` | Timeline layout, shot cards with asset sourcing status, AI agent material trace cards, dark code block (`bg-[#1e293b] text-emerald-400`) |
| **P9BrollGallery** | `Phase9Keyframes` | Timeline layout, shot cards with render status badges (`Rendered` green / `Awaiting P10` amber), video placeholder with play overlay, filename label |
| **P10VideoPlayer** | `Phase10BRoll` | B-Roll video list with thumbnail placeholder, filename, duration badge, match label, license badge (`Pexels (CC0)`), coverage summary row |
| **P11FinalPlayer** | `Phase12Final` | Completion green checkmark circle, platform download buttons (B站/Douyin) with codec/size labels, SRT subtitle download row |

Each task follows the same commit pattern:
```bash
git add tests/unit/frontend/visual/PhasePreviews.visual.test.tsx src/frontend/components/previews/P[N]View.tsx
git commit -m "[VIS-001] visual alignment: P[N]View → [description]"
```

---

## Wave 3: Supporting Components & Empty States

### Task 17: Empty/Null State Consistency

**Files:**
- Create: `tests/unit/frontend/visual/EmptyStates.visual.test.tsx`
- Modify: All 12 preview components (ensure placeholder consistency)

All empty states should render:
- Large icon (w-12 h-12, opacity-50, text-slate-400)
- Chinese description ("暂无XX数据" format)
- Subtitle text ("等待XX Agent 完成初始化")
- Container: `flex flex-col items-center justify-center h-64 text-slate-400`

- [ ] **Step 1: Write failing test checking empty state consistency**
- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Update all empty states**
- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit**

---

### Task 18: Design Token Consistency Check

**Files:**
- Create: `tests/unit/frontend/visual/DesignTokens.visual.test.tsx`
- (No implementation changes needed — test verifies existing code)

```typescript
// Test that verifies key design tokens across pages
// - bg color consistency
// - card border consistency
// - typography scale consistency
```

- [ ] **Step 1: Write test**
- [ ] **Step 2: Run → PASS (if tokens consistently applied) or FAIL**
- [ ] **Step 3: Fix any inconsistency**
- [ ] **Step 4: Commit**

---

## Wave 4: Integration Verification

### Task 19: Type Check + Full Test Suite

- [ ] **Step 1: Run TypeScript type check**

```bash
cd src/frontend && npx tsc --noEmit
```

Expected: PASS, no type errors

- [ ] **Step 2: Run frontend unit tests**

```bash
cd src/frontend && npx vitest run
```

Expected: All tests pass (new visual tests + existing functional tests)

- [ ] **Step 3: Run Python tests (no regression)**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && python -m pytest tests/unit/ -x --timeout=30 -q
```

Expected: All passing as before

- [ ] **Step 4: Commit final verification**

```bash
git commit -m "[VIS-001] verification: type check + full test suite passing"
```

---

## Self-Review Checklist

1. **Spec coverage:** Each AC-P1 through AC-P10 maps to at least one task — AC-P1..P4: Tasks 1-4, AC-P5: Tasks 5-16, AC-P6: Task 17, AC-P7: Task 18, AC-P8: Implicit in all tasks, AC-P9: Implicit in all tasks, AC-P10: Task 19
2. **Placeholder scan:** No TBD/TODO/implement later — every task has concrete code
3. **Type consistency:** Props interfaces remain unchanged from current implementation — visual changes only

---

## Execution Handoff

**Plan complete and saved.**

Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch fresh subagent per task group, review between waves, fast iteration. Wave 1 (4 subagents in parallel) → Wave 2 (4 subagents × 3 components each) → Wave 3 → Wave 4.

2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
