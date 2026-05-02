# Wave 3a Frontend Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1 frontend shell (list/create/recover/error/event/candidate flows) — the minimum UI surface that unblocks user-facing demo of the pipeline, backed by MSW fixtures (no real backend).

**Architecture:** React 19 + Tailwind 4 components. Server state via React Query, client/WS state via Zustand. Routing via react-router-dom v6. Each component has vitest tests; pytest stubs become subprocess wrappers calling vitest to satisfy the task-card pytest contract.

**Tech Stack:** Vite 6, TypeScript 5.8 (strict), Vitest 2 + @testing-library/react 16 + jsdom, MSW 2.6.6, react-router-dom 6, dayjs, sonner, mock-socket, zustand, @tanstack/react-query.

**Spec:** `docs/superpowers/specs/2026-04-17-wave-3a-frontend-shell-design.md`

**Wave 3a covers:** E-001 + E-100 (merged), E-002, E-003, E-007, E-008, E-009, E-010 + 1 foundation task.

**Deferred:** E-004 / E-005 / E-006 (superseded by E-102) / E-101..E-105 → Wave 3b. E-011..E-015 → Wave 3c.

---

## File Structure

### Task 0 — Shell Foundation
- Modify: `src/frontend/package.json` (add 6 deps)
- Modify: `src/frontend/vitest.setup.ts` (add queryClient test reset, mock-socket bootstrap)
- Create: `src/frontend/api/client.ts`
- Create: `src/frontend/lib/queryClient.ts`
- Create: `src/frontend/store/index.ts`
- Create: `src/frontend/hooks/useWebSocket.ts`
- Create: `src/frontend/App.tsx`
- Create: `src/frontend/main.tsx` (or update existing entry)
- Create: `src/frontend/pages/AppRouter.tsx`
- Create: `tests/unit/frontend/api/client.test.ts`
- Create: `tests/unit/frontend/lib/queryClient.test.ts`
- Create: `tests/unit/frontend/store/index.test.ts`
- Create: `tests/unit/frontend/hooks/useWebSocket.test.ts`

### Task 1 — ProjectList + ProjectCard (E-001 + E-100 merged)
- Create: `src/frontend/types/project.ts` (re-exports + view adapter)
- Create: `src/frontend/hooks/useProjects.ts`
- Create: `src/frontend/components/ProjectCard.tsx`
- Create: `src/frontend/pages/ProjectList.tsx`
- Create: `tests/unit/frontend/hooks/useProjects.test.tsx`
- Create: `tests/unit/frontend/components/ProjectCard.test.tsx`
- Create: `tests/unit/frontend/pages/ProjectList.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_001.py` (stub → wrapper)
- Modify: `tests/unit/frontend/test_spec_e_100.py` (stub → wrapper)

### Task 2 — NewProject Wizard (E-002)
- Create: `src/frontend/hooks/useCreateProject.ts`
- Create: `src/frontend/components/CreateProjectForm.tsx`
- Create: `src/frontend/pages/NewProject.tsx`
- Create: `tests/unit/frontend/components/CreateProjectForm.test.tsx`
- Create: `tests/unit/frontend/pages/NewProject.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_002.py` (stub → wrapper)
- Modify: `src/frontend/pages/AppRouter.tsx` (add `/projects/new` route)
- Modify: `tests/fixtures/api/projects/_index.json` (ensure POST /projects fixture)
- Create: `tests/fixtures/api/projects/create_response.json`

### Task 3 — State Recovery (E-003)
- Create: `src/frontend/types/project_state.ts` (view adapter)
- Create: `src/frontend/hooks/useProjectState.ts`
- Create: `src/frontend/components/PhaseNavigation.tsx`
- Create: `src/frontend/components/LoadingState.tsx`
- Create: `src/frontend/components/ErrorState.tsx`
- Create: `src/frontend/pages/WorkflowPage.tsx`
- Create: `tests/unit/frontend/hooks/useProjectState.test.tsx`
- Create: `tests/unit/frontend/pages/WorkflowPage.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_003.py` (stub → wrapper)
- Modify: `src/frontend/pages/AppRouter.tsx` (add `/projects/:id` + `/projects/:id/phases/:phase` routes)

### Task 4 — ArtifactStatusBadge (E-007)
- Create: `src/frontend/components/ArtifactStatusBadge.tsx`
- Create: `src/frontend/hooks/useArtifactStatus.ts`
- Create: `tests/unit/frontend/components/ArtifactStatusBadge.test.tsx`
- Modify: `src/frontend/components/PhaseNavigation.tsx` (integrate badge)
- Modify: `tests/unit/frontend/test_spec_e_007.py` (stub → wrapper)

### Task 5 — AgentActivityPanel (E-008)
- Create: `src/frontend/types/events.ts`
- Create: `src/frontend/hooks/useEventStream.ts`
- Create: `src/frontend/components/ActivityEventRow.tsx`
- Create: `src/frontend/components/AgentActivityPanel.tsx`
- Create: `tests/unit/frontend/hooks/useEventStream.test.tsx`
- Create: `tests/unit/frontend/components/AgentActivityPanel.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_008.py` (stub → wrapper)
- Modify: `src/frontend/mocks/handlers.ts` (add GET /events handler)
- Create: `tests/fixtures/api/events/list_response.json`

### Task 6 — Error UX Map (E-009)
- Create: `src/frontend/types/errors.ts`
- Create: `src/frontend/utils/errorUxMap.ts`
- Create: `src/frontend/hooks/useErrorHandler.ts`
- Create: `src/frontend/components/errors/TechnicalDetails.tsx`
- Create: `src/frontend/components/errors/ErrorToast.tsx`
- Create: `src/frontend/components/errors/ErrorModal.tsx`
- Create: `tests/unit/frontend/utils/errorUxMap.test.ts`
- Create: `tests/unit/frontend/components/errors/ErrorToast.test.tsx`
- Create: `tests/unit/frontend/components/errors/ErrorModal.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_009.py` (stub → wrapper)

### Task 7 — CandidateSelector (E-010)
- Create: `src/frontend/types/candidates.ts`
- Create: `src/frontend/hooks/useCandidateSelection.ts`
- Create: `src/frontend/components/CandidateCard.tsx`
- Create: `src/frontend/components/CandidateSelector.tsx`
- Create: `tests/unit/frontend/hooks/useCandidateSelection.test.tsx`
- Create: `tests/unit/frontend/components/CandidateSelector.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_010.py` (stub → wrapper)

### Task 8 — PROGRESS.md + Task Card Sync
- Modify: `PROGRESS.md` (append Wave 3a entry)
- Modify (one line each): `tasks/SPEC-E/E-001..E-010/E-100.md` (mark status=DONE)

---

## Task 0: Shell Foundation

**Files:**
- Modify: `src/frontend/package.json`
- Modify: `src/frontend/vitest.setup.ts`
- Modify: `src/frontend/tsconfig.json` (if path aliases insufficient)
- Create: `src/frontend/api/client.ts`
- Create: `src/frontend/lib/queryClient.ts`
- Create: `src/frontend/store/index.ts`
- Create: `src/frontend/hooks/useWebSocket.ts`
- Create: `src/frontend/App.tsx`
- Create: `src/frontend/pages/AppRouter.tsx`

- [ ] **Step 1: Add dependencies**

Modify `src/frontend/package.json` dependencies + devDependencies:

```json
{
  "dependencies": {
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "lucide-react": "0.546.0",
    "motion": "12.23.24",
    "@tanstack/react-query": "^5.59.0",
    "zustand": "^5.0.2",
    "react-router-dom": "^6.28.0",
    "dayjs": "^1.11.13",
    "sonner": "^1.7.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "6.5.0",
    "@testing-library/react": "16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "19.0.0",
    "@types/react-dom": "19.0.0",
    "@vitejs/plugin-react": "5.0.4",
    "autoprefixer": "10.4.21",
    "eslint": "9.14.0",
    "jsdom": "25.0.1",
    "mock-socket": "^9.3.1",
    "msw": "2.6.6",
    "tailwindcss": "4.1.14",
    "@tailwindcss/vite": "4.1.14",
    "typescript": "5.8.3",
    "vite": "6.2.0",
    "vitest": "2.1.8"
  }
}
```

- [ ] **Step 2: Install deps and verify**

Run (from worktree root):
```bash
cd src/frontend && pnpm install 2>&1 | tail -10
```

Expected: "Lockfile is up to date" or "Packages: +N" with no errors. Verify with:
```bash
pnpm ls @tanstack/react-query zustand react-router-dom dayjs sonner mock-socket | head -10
```
Expected: all 6 listed with resolved versions.

- [ ] **Step 3: Write failing test for apiClient**

Create `tests/unit/frontend/api/client.test.ts`:

```typescript
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { server } from "@frontend/mocks/server";
import { apiClient } from "@frontend/api/client";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("apiClient", () => {
  it("GET returns parsed JSON body for 2xx", async () => {
    const data = await apiClient.get<{ project_id: string }>("/api/v1/projects");
    expect(data.project_id).toBe("proj_001");
  });

  it("throws ApiError with code on 4xx", async () => {
    server.use(
      (await import("msw")).http.get("/api/v1/nope", () =>
        new Response(JSON.stringify({ error_code: "EVID_4001", message: "not found" }), {
          status: 404, headers: { "content-type": "application/json" }
        })
      )
    );
    await expect(apiClient.get("/api/v1/nope")).rejects.toMatchObject({
      error_code: "EVID_4001",
      status: 404,
    });
  });

  it("POST serializes JSON body and sends content-type header", async () => {
    let captured: Request | null = null;
    server.use(
      (await import("msw")).http.post("/api/v1/echo", async ({ request }) => {
        captured = request.clone();
        return Response.json({ ok: true });
      })
    );
    await apiClient.post("/api/v1/echo", { a: 1 });
    expect(captured!.headers.get("content-type")).toContain("application/json");
    expect(await captured!.json()).toEqual({ a: 1 });
  });
});
```

- [ ] **Step 4: Run test to verify it fails**

```bash
cd src/frontend && pnpm vitest run api/client.test.ts 2>&1 | tail -15
```
Expected: FAIL with `Cannot find module '@frontend/api/client'` or similar import error.

- [ ] **Step 5: Implement apiClient**

Create `src/frontend/api/client.ts`:

```typescript
export interface ApiError {
  error_code: string
  message: string
  status: number
  details?: unknown
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers["content-type"] = "application/json"
  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let parsed: Partial<ApiError> = {}
    try { parsed = await res.json() } catch { /* non-json error */ }
    const err: ApiError = {
      error_code: parsed.error_code ?? `HTTP_${res.status}`,
      message: parsed.message ?? res.statusText,
      status: res.status,
      details: parsed.details,
    }
    throw err
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body: unknown) => request<T>("PUT", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
}
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd src/frontend && pnpm vitest run api/client.test.ts 2>&1 | tail -15
```
Expected: 3 passed.

- [ ] **Step 7: Write failing test for queryClient**

Create `tests/unit/frontend/lib/queryClient.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { createQueryClient } from "@frontend/lib/queryClient";

describe("createQueryClient", () => {
  it("returns a QueryClient with test-friendly defaults", () => {
    const qc = createQueryClient();
    const defaults = qc.getDefaultOptions();
    expect(defaults.queries?.retry).toBe(false);
    expect(defaults.queries?.staleTime).toBe(0);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
  });
});
```

- [ ] **Step 8: Run failing test**

```bash
cd src/frontend && pnpm vitest run lib/queryClient.test.ts 2>&1 | tail -10
```
Expected: FAIL with module-not-found.

- [ ] **Step 9: Implement queryClient**

Create `src/frontend/lib/queryClient.ts`:

```typescript
import { QueryClient } from "@tanstack/react-query"

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        refetchOnWindowFocus: false,
      },
    },
  })
}
```

- [ ] **Step 10: Run test — GREEN**

```bash
cd src/frontend && pnpm vitest run lib/queryClient.test.ts 2>&1 | tail -5
```
Expected: 1 passed.

- [ ] **Step 11: Write failing test for Zustand store**

Create `tests/unit/frontend/store/index.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore, resetAppStore } from "@frontend/store";

describe("app store", () => {
  beforeEach(() => resetAppStore());

  it("starts empty", () => {
    expect(useAppStore.getState().events).toEqual([]);
  });

  it("pushEvent appends", () => {
    useAppStore.getState().pushEvent({
      id: "e1", type: "phase.advanced", project_id: "p1",
      timestamp: "2026-04-17T10:00:00Z", payload: {},
    });
    expect(useAppStore.getState().events).toHaveLength(1);
    expect(useAppStore.getState().events[0].id).toBe("e1");
  });

  it("caps event buffer at 50", () => {
    for (let i = 0; i < 60; i++) {
      useAppStore.getState().pushEvent({
        id: `e${i}`, type: "x", project_id: "p",
        timestamp: "2026-04-17T10:00:00Z", payload: {},
      });
    }
    expect(useAppStore.getState().events).toHaveLength(50);
    expect(useAppStore.getState().events[0].id).toBe("e10");
  });
});
```

- [ ] **Step 12: Run failing test**

```bash
cd src/frontend && pnpm vitest run store/index.test.ts 2>&1 | tail -5
```
Expected: FAIL module-not-found.

- [ ] **Step 13: Implement store**

Create `src/frontend/store/index.ts`:

```typescript
import { create } from "zustand"

export interface AgentEvent {
  id: string
  type: string
  project_id: string
  timestamp: string
  payload: Record<string, unknown>
}

interface AppState {
  events: AgentEvent[]
  pushEvent: (evt: AgentEvent) => void
  clearEvents: () => void
}

const MAX_EVENTS = 50

export const useAppStore = create<AppState>((set) => ({
  events: [],
  pushEvent: (evt) =>
    set((s) => ({ events: [...s.events, evt].slice(-MAX_EVENTS) })),
  clearEvents: () => set({ events: [] }),
}))

export function resetAppStore(): void {
  useAppStore.setState({ events: [] })
}
```

- [ ] **Step 14: Run test — GREEN**

```bash
cd src/frontend && pnpm vitest run store/index.test.ts 2>&1 | tail -5
```
Expected: 3 passed.

- [ ] **Step 15: Write failing test for useWebSocket**

Create `tests/unit/frontend/hooks/useWebSocket.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { Server } from "mock-socket";
import { useWebSocket } from "@frontend/hooks/useWebSocket";

describe("useWebSocket", () => {
  let mockServer: Server;
  const URL = "ws://localhost:8000/ws/proj_001";

  beforeEach(() => { mockServer = new Server(URL); });
  afterEach(() => { mockServer.stop(); });

  it("receives messages and calls onMessage", async () => {
    const onMessage = vi.fn();
    const { unmount } = renderHook(() => useWebSocket(URL, { onMessage }));
    await vi.waitFor(() => expect(mockServer.clients().length).toBe(1));
    act(() => { mockServer.emit("message", JSON.stringify({ type: "phase.advanced" })); });
    await vi.waitFor(() => expect(onMessage).toHaveBeenCalledOnce());
    expect(onMessage.mock.calls[0][0]).toMatchObject({ type: "phase.advanced" });
    unmount();
  });

  it("skips when enabled=false", () => {
    const onMessage = vi.fn();
    renderHook(() => useWebSocket(URL, { onMessage, enabled: false }));
    expect(mockServer.clients().length).toBe(0);
  });
});
```

- [ ] **Step 16: Run failing test**

```bash
cd src/frontend && pnpm vitest run hooks/useWebSocket.test.ts 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 17: Implement useWebSocket**

Create `src/frontend/hooks/useWebSocket.ts`:

```typescript
import { useEffect, useRef } from "react"

export interface WebSocketOptions {
  onMessage?: (data: unknown) => void
  onOpen?: () => void
  onClose?: () => void
  enabled?: boolean
}

export function useWebSocket(url: string, opts: WebSocketOptions = {}): void {
  const { onMessage, onOpen, onClose, enabled = true } = opts
  const ref = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled) return
    const ws = new WebSocket(url)
    ref.current = ws
    ws.onopen = () => onOpen?.()
    ws.onmessage = (e) => {
      try { onMessage?.(JSON.parse(e.data)) }
      catch { onMessage?.(e.data) }
    }
    ws.onclose = () => onClose?.()
    return () => { ws.close() }
  }, [url, enabled, onMessage, onOpen, onClose])
}
```

- [ ] **Step 18: Run test — GREEN**

```bash
cd src/frontend && pnpm vitest run hooks/useWebSocket.test.ts 2>&1 | tail -5
```
Expected: 2 passed.

- [ ] **Step 19: Create AppRouter skeleton**

Create `src/frontend/pages/AppRouter.tsx` (routes filled in as tasks land):

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"

export function AppRouter(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<div data-testid="placeholder-list" />} />
        <Route path="*" element={<div>404</div>} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 20: Create App.tsx with providers**

Create `src/frontend/App.tsx`:

```tsx
import { QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { AppRouter } from "./pages/AppRouter"
import { createQueryClient } from "./lib/queryClient"

const queryClient = createQueryClient()

export function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}
```

- [ ] **Step 21: Run full type check**

```bash
cd src/frontend && pnpm tsc 2>&1 | tail -10
```
Expected: 0 errors.

- [ ] **Step 22: Run all Task 0 tests**

```bash
cd src/frontend && pnpm vitest run api lib store hooks/useWebSocket 2>&1 | tail -15
```
Expected: 9 passed (3 apiClient + 1 queryClient + 3 store + 2 useWebSocket).

- [ ] **Step 23: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System.wt-wave3a
git add src/frontend/package.json src/frontend/api src/frontend/lib src/frontend/store src/frontend/hooks/useWebSocket.ts src/frontend/App.tsx src/frontend/pages/AppRouter.tsx tests/unit/frontend/api tests/unit/frontend/lib tests/unit/frontend/store tests/unit/frontend/hooks/useWebSocket.test.ts
git commit -m "[SPEC-E-FOUNDATION] shell infra: apiClient, queryClient, Zustand store, useWebSocket, App/Router skeletons"
```

---

## Task 1: ProjectList + ProjectCard (E-001 + E-100 merged)

**Files:**
- Create: `src/frontend/types/project.ts`
- Create: `src/frontend/hooks/useProjects.ts`
- Create: `src/frontend/components/ProjectCard.tsx`
- Create: `src/frontend/pages/ProjectList.tsx`
- Create: `tests/unit/frontend/components/ProjectCard.test.tsx`
- Create: `tests/unit/frontend/hooks/useProjects.test.tsx`
- Create: `tests/unit/frontend/pages/ProjectList.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_001.py`
- Modify: `tests/unit/frontend/test_spec_e_100.py`
- Modify: `src/frontend/pages/AppRouter.tsx`
- Modify: `tests/fixtures/api/projects/list_response.json` (ensure `latest_reached_phase` present)

**Required fixture shape** — confirm `list_response.json` contains at least 2 items with `latest_reached_phase` (one equal, one differing from `current_phase`). If missing, adjust fixture (allowed via Task 1).

- [ ] **Step 1: Write failing test for ProjectCard (AC-1..AC-3, AC-5 rendering)**

Create `tests/unit/frontend/components/ProjectCard.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectCard } from "@frontend/components/ProjectCard";

const base = {
  id: "proj_001",
  title: "黄金价格走势分析",
  category: "行业分析",
  current_phase: 2,
  latest_reached_phase: 2,
  progress: 25,
  status: "in_progress",
  updated_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
};

describe("ProjectCard", () => {
  it("AC-1 renders title, category, current_phase, progress, status, updated_at", () => {
    render(<ProjectCard project={base} onClick={vi.fn()} />);
    expect(screen.getByText("黄金价格走势分析")).toBeInTheDocument();
    expect(screen.getByText("行业分析")).toBeInTheDocument();
    expect(screen.getByText(/P2/)).toBeInTheDocument();
    expect(screen.getByText(/25%/)).toBeInTheDocument();
    expect(screen.getByText(/in_progress/i)).toBeInTheDocument();
    expect(screen.getByText(/分钟前/)).toBeInTheDocument();
  });

  it("AC-2 progress bar width reflects progress/100", () => {
    render(<ProjectCard project={{ ...base, progress: 75 }} onClick={vi.fn()} />);
    const bar = screen.getByTestId("progress-bar-fill");
    expect(bar).toHaveStyle({ width: "75%" });
  });

  it("AC-3 updated_at renders as relative time", () => {
    render(<ProjectCard project={base} onClick={vi.fn()} />);
    expect(screen.getByText(/分钟前/)).toBeInTheDocument();
  });

  it("E-100 AC-1 shows rollback badge when latest_reached_phase > current_phase", () => {
    render(
      <ProjectCard
        project={{ ...base, current_phase: 2, latest_reached_phase: 5 }}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/回退 3 阶段/)).toBeInTheDocument();
  });

  it("E-100 AC-3 hides badge when current_phase === latest_reached_phase", () => {
    render(<ProjectCard project={base} onClick={vi.fn()} />);
    expect(screen.queryByText(/回退/)).toBeNull();
  });

  it("E-100 AC-2 click invokes onClick with project id", async () => {
    const onClick = vi.fn();
    render(<ProjectCard project={base} onClick={onClick} />);
    await userEvent.click(screen.getByRole("article"));
    expect(onClick).toHaveBeenCalledWith("proj_001");
  });
});
```

- [ ] **Step 2: Run failing test**

```bash
cd src/frontend && pnpm vitest run components/ProjectCard.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 3: Create types/project.ts**

Create `src/frontend/types/project.ts`:

```typescript
import type { ProjectInfo } from "../../shared/types/project_state"

export type ProjectListItem = ProjectInfo

export function rollbackDelta(p: ProjectListItem): number {
  return p.latest_reached_phase - p.current_phase
}
```

Note: this file imports from `src/shared/types/project_state.ts` (already written by Wave 2 containing `latest_reached_phase`). Verify via:

```bash
grep -c "latest_reached_phase" src/shared/types/project_state.ts
```
Expected: >= 1.

- [ ] **Step 4: Implement ProjectCard**

Create `src/frontend/components/ProjectCard.tsx`:

```tsx
import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"
import "dayjs/locale/zh-cn"
import { rollbackDelta, type ProjectListItem } from "../types/project"

dayjs.extend(relativeTime)
dayjs.locale("zh-cn")

interface Props {
  project: ProjectListItem
  onClick: (id: string) => void
}

export function ProjectCard({ project, onClick }: Props): JSX.Element {
  const delta = rollbackDelta(project)
  const relTime = dayjs(project.updated_at).fromNow()
  return (
    <article
      role="article"
      className="p-4 border rounded-lg cursor-pointer hover:shadow"
      onClick={() => onClick(project.id)}
    >
      <div className="flex justify-between">
        <h3 className="font-semibold">{project.title}</h3>
        {delta > 0 && (
          <span className="text-orange-600 text-xs bg-orange-100 px-2 py-1 rounded">
            回退 {delta} 阶段
          </span>
        )}
      </div>
      <div className="text-sm text-gray-600 mt-1">{project.category}</div>
      <div className="text-xs mt-2">P{project.current_phase} · {project.status}</div>
      <div className="mt-2 h-2 bg-gray-200 rounded">
        <div
          data-testid="progress-bar-fill"
          className="h-2 bg-blue-500 rounded"
          style={{ width: `${project.progress}%` }}
        />
      </div>
      <div className="text-xs text-gray-500 mt-2">{project.progress}% · {relTime}</div>
    </article>
  )
}
```

- [ ] **Step 5: Run test — GREEN**

```bash
cd src/frontend && pnpm vitest run components/ProjectCard.test.tsx 2>&1 | tail -10
```
Expected: 6 passed.

- [ ] **Step 6: Write failing test for useProjects (AC-5 WS refresh)**

Create `tests/unit/frontend/hooks/useProjects.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, beforeEach, afterEach, afterAll, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Server } from "mock-socket";
import React from "react";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useProjects } from "@frontend/hooks/useProjects";

const WS_URL = "ws://localhost:8000/ws/projects";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function wrapper(qc = createQueryClient()) {
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useProjects", () => {
  it("returns fixture-backed project list", async () => {
    const { result } = renderHook(() => useProjects(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.length).toBeGreaterThan(0);
    expect(result.current.data![0]).toHaveProperty("latest_reached_phase");
  });

  it("AC-5: WS phase.advanced event invalidates cache within 6s", async () => {
    const mockWs = new Server(WS_URL);
    const qc = createQueryClient();
    const { result } = renderHook(() => useProjects(WS_URL), { wrapper: wrapper(qc) });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const t0 = performance.now();
    act(() => {
      mockWs.emit("message", JSON.stringify({
        type: "phase.advanced", project_id: "proj_001",
        timestamp: new Date().toISOString(), payload: { phase: 5 },
      }));
    });
    await waitFor(() => {
      expect(qc.getQueryState(["projects"])?.dataUpdateCount).toBeGreaterThan(1);
    }, { timeout: 6000 });
    const elapsed = performance.now() - t0;
    expect(elapsed).toBeLessThan(6000);
    mockWs.stop();
  });
});
```

- [ ] **Step 7: Run failing test**

```bash
cd src/frontend && pnpm vitest run hooks/useProjects.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 8: Implement useProjects**

Create `src/frontend/hooks/useProjects.ts`:

```typescript
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "../api/client"
import { useWebSocket } from "./useWebSocket"
import type { ProjectListItem } from "../types/project"

const REFRESH_EVENTS = new Set(["phase.advanced", "status.changed", "project.updated"])

export function useProjects(wsUrl?: string) {
  const qc = useQueryClient()
  const query = useQuery({
    queryKey: ["projects"],
    queryFn: () => apiClient.get<ProjectListItem[]>("/api/v1/projects"),
  })

  useWebSocket(wsUrl ?? "", {
    enabled: !!wsUrl,
    onMessage: (data) => {
      const evt = data as { type?: string }
      if (evt?.type && REFRESH_EVENTS.has(evt.type)) {
        qc.invalidateQueries({ queryKey: ["projects"] })
      }
    },
  })

  return query
}
```

- [ ] **Step 9: Verify list_response.json shape**

Ensure fixture is an array and items carry required fields:
```bash
node -e 'const f=require("./tests/fixtures/api/projects/list_response.json"); const a=Array.isArray(f)?f:[f]; console.log(JSON.stringify(a[0],null,2))' | head -20
```
If `list_response.json` is a single-object `ProjectInfo`, adapt the handler or wrap as `[obj, obj2]`. Fix by replacing fixture body with a 3-item array; ensure at least one has `latest_reached_phase > current_phase`.

Expected minimum:
```json
[
  {"id":"proj_001","title":"黄金价格走势分析","category":"行业分析","current_phase":2,"latest_reached_phase":5,"progress":25,"status":"in_progress","updated_at":"..."},
  {"id":"proj_002","title":"十五五规划解读","category":"政策解读","current_phase":1,"latest_reached_phase":1,"progress":10,"status":"awaiting_user","updated_at":"..."},
  {"id":"proj_003","title":"AI 行业周报","category":"行业分析","current_phase":8,"latest_reached_phase":8,"progress":70,"status":"completed","updated_at":"..."}
]
```

- [ ] **Step 10: Ensure handler maps GET /api/v1/projects → list_response.json as array**

Check `src/frontend/mocks/handlers.ts`. If it currently returns the single-item fixture, change to return the array. Also verify `tests/fixtures/api/projects/_index.json` maps `list_response.json` with `{"schema": "project_state.ProjectInfo", "list": true}`.

- [ ] **Step 11: Run useProjects test — GREEN**

```bash
cd src/frontend && pnpm vitest run hooks/useProjects.test.tsx 2>&1 | tail -10
```
Expected: 2 passed.

- [ ] **Step 12: Write failing test for ProjectList page**

Create `tests/unit/frontend/pages/ProjectList.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { ProjectList } from "@frontend/pages/ProjectList";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ProjectList page", () => {
  it("AC-4 renders fixture projects with distinct progress/status/time", async () => {
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <ProjectList />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getAllByRole("article").length).toBeGreaterThanOrEqual(3));
    expect(screen.getByText(/黄金价格走势分析/)).toBeInTheDocument();
    expect(screen.getByText(/十五五规划解读/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 13: Run failing test**

```bash
cd src/frontend && pnpm vitest run pages/ProjectList.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 14: Implement ProjectList page**

Create `src/frontend/pages/ProjectList.tsx`:

```tsx
import { useNavigate } from "react-router-dom"
import { useProjects } from "../hooks/useProjects"
import { ProjectCard } from "../components/ProjectCard"

export function ProjectList(): JSX.Element {
  const nav = useNavigate()
  const { data, isLoading, isError } = useProjects("ws://localhost:8000/ws/projects")
  if (isLoading) return <div>加载中...</div>
  if (isError || !data) return <div>加载失败</div>
  return (
    <div className="p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">项目列表</h1>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded"
          onClick={() => nav("/projects/new")}
        >
          新建项目
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((p) => (
          <ProjectCard key={p.id} project={p} onClick={(id) => nav(`/projects/${id}`)} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 15: Wire ProjectList into AppRouter**

Modify `src/frontend/pages/AppRouter.tsx`:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ProjectList } from "./ProjectList"

export function AppRouter(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="*" element={<div>404</div>} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 16: Run ProjectList test — GREEN**

```bash
cd src/frontend && pnpm vitest run pages/ProjectList.test.tsx 2>&1 | tail -5
```
Expected: 1 passed.

- [ ] **Step 17: Rewrite pytest wrappers**

Modify `tests/unit/frontend/test_spec_e_001.py`:

```python
"""Tests for [SPEC-E-001] Project List Page (pytest wraps vitest)."""
import subprocess
from pathlib import Path
import pytest

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"

def _vitest(test_file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT, capture_output=True, text=True, timeout=180,
    )

class TestAC1RendersAllProjectFields:
    def test_renders_all_project_fields(self):
        r = _vitest("components/ProjectCard.test.tsx", "AC-1 renders title")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

class TestAC2ProgressBarReflectsPhase:
    def test_progress_bar_reflects_phase(self):
        r = _vitest("components/ProjectCard.test.tsx", "AC-2 progress bar")
        assert r.returncode == 0, r.stdout + r.stderr

class TestAC3UpdatedAtRelativeTime:
    def test_updated_at_displays_relative_time(self):
        r = _vitest("components/ProjectCard.test.tsx", "AC-3 updated_at")
        assert r.returncode == 0, r.stdout + r.stderr

class TestAC4MultipleProjectsDifferentPhases:
    def test_multiple_projects_different_phases(self):
        r = _vitest("pages/ProjectList.test.tsx", "AC-4 renders fixture")
        assert r.returncode == 0, r.stdout + r.stderr

class TestAC5UpdatedAtRefreshesOnWsEvent:
    def test_updated_at_refreshes_on_ws_event(self):
        r = _vitest("hooks/useProjects.test.tsx", "AC-5:")
        assert r.returncode == 0, r.stdout + r.stderr
```

Modify `tests/unit/frontend/test_spec_e_100.py`:

```python
"""Tests for [SPEC-E-100] 项目列表自动打开最新阶段 (pytest wraps vitest)."""
import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"

def _vitest(test_file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT, capture_output=True, text=True, timeout=180,
    )

class TestShowsPhaseBadge:
    def test_shows_phase_diff_badge_when_phases_differ(self):
        r = _vitest("components/ProjectCard.test.tsx", "E-100 AC-1 shows rollback")
        assert r.returncode == 0, r.stdout + r.stderr

class TestClickNavigates:
    def test_clicks_card_routes_to_latest_reached_phase(self):
        r = _vitest("components/ProjectCard.test.tsx", "E-100 AC-2 click invokes")
        assert r.returncode == 0, r.stdout + r.stderr

class TestHidesBadgeWhenEqual:
    def test_hides_badge_when_phases_equal(self):
        r = _vitest("components/ProjectCard.test.tsx", "E-100 AC-3 hides badge")
        assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 18: Run pytest wrappers**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_001.py tests/unit/frontend/test_spec_e_100.py -v 2>&1 | tail -15
```
Expected: 8 passed (5 for E-001 + 3 for E-100).

- [ ] **Step 19: Commit**

```bash
git add src/frontend/types/project.ts src/frontend/hooks/useProjects.ts src/frontend/components/ProjectCard.tsx src/frontend/pages/ProjectList.tsx src/frontend/pages/AppRouter.tsx tests/unit/frontend/components/ProjectCard.test.tsx tests/unit/frontend/hooks/useProjects.test.tsx tests/unit/frontend/pages/ProjectList.test.tsx tests/unit/frontend/test_spec_e_001.py tests/unit/frontend/test_spec_e_100.py tests/fixtures/api/projects/list_response.json src/frontend/mocks/handlers.ts
git commit -m "[SPEC-E-001][SPEC-E-100] ProjectList + ProjectCard with rollback badge + WS refresh"
```

---

## Task 2: NewProject Wizard (E-002)

**Files:**
- Create: `src/frontend/hooks/useCreateProject.ts`
- Create: `src/frontend/components/CreateProjectForm.tsx`
- Create: `src/frontend/pages/NewProject.tsx`
- Create: `tests/unit/frontend/components/CreateProjectForm.test.tsx`
- Create: `tests/unit/frontend/pages/NewProject.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_002.py`
- Modify: `src/frontend/pages/AppRouter.tsx`
- Modify: `src/frontend/mocks/handlers.ts` (add POST /api/v1/projects)
- Create: `tests/fixtures/api/projects/create_response.json`

- [ ] **Step 1: Write failing form test**

Create `tests/unit/frontend/components/CreateProjectForm.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateProjectForm } from "@frontend/components/CreateProjectForm";

describe("CreateProjectForm", () => {
  it("AC-1 shows title and description inputs", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByLabelText(/标题/)).toBeInTheDocument();
    expect(screen.getByLabelText(/描述/)).toBeInTheDocument();
  });

  it("AC-2 blocks submit when description < 10 chars", async () => {
    const onSubmit = vi.fn();
    render(<CreateProjectForm onSubmit={onSubmit} isSubmitting={false} />);
    await userEvent.type(screen.getByLabelText(/标题/), "Test");
    await userEvent.type(screen.getByLabelText(/描述/), "太短");
    await userEvent.click(screen.getByRole("button", { name: /创建/ }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/至少 10 个字/)).toBeInTheDocument();
  });

  it("AC-3 submits with title+description when valid", async () => {
    const onSubmit = vi.fn();
    render(<CreateProjectForm onSubmit={onSubmit} isSubmitting={false} />);
    await userEvent.type(screen.getByLabelText(/标题/), "Test Project");
    await userEvent.type(screen.getByLabelText(/描述/), "这是一个长度足够的项目描述");
    await userEvent.click(screen.getByRole("button", { name: /创建/ }));
    expect(onSubmit).toHaveBeenCalledWith({
      title: "Test Project",
      description: "这是一个长度足够的项目描述",
    });
  });
});
```

- [ ] **Step 2: Run — RED**

```bash
cd src/frontend && pnpm vitest run components/CreateProjectForm.test.tsx 2>&1 | tail -5
```
Expected: FAIL module-not-found.

- [ ] **Step 3: Implement CreateProjectForm**

Create `src/frontend/components/CreateProjectForm.tsx`:

```tsx
import { useState, FormEvent } from "react"

interface Props {
  onSubmit: (input: { title: string; description: string }) => void
  isSubmitting: boolean
}

const MIN_DESC = 10

export function CreateProjectForm({ onSubmit, isSubmitting }: Props): JSX.Element {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState("")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (description.length < MIN_DESC) {
      setError(`描述至少 10 个字`)
      return
    }
    setError("")
    onSubmit({ title, description })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-xl">
      <div>
        <label htmlFor="title" className="block text-sm mb-1">标题</label>
        <input
          id="title" type="text" required
          value={title} onChange={(e) => setTitle(e.target.value)}
          className="border rounded px-3 py-2 w-full"
        />
      </div>
      <div>
        <label htmlFor="desc" className="block text-sm mb-1">描述</label>
        <textarea
          id="desc" required rows={4}
          value={description} onChange={(e) => setDescription(e.target.value)}
          className="border rounded px-3 py-2 w-full"
        />
      </div>
      {error && <div role="alert" className="text-red-600 text-sm">{error}</div>}
      <button
        type="submit" disabled={isSubmitting}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {isSubmitting ? "创建中..." : "创建"}
      </button>
    </form>
  )
}
```

- [ ] **Step 4: Run — GREEN**

```bash
cd src/frontend && pnpm vitest run components/CreateProjectForm.test.tsx 2>&1 | tail -5
```
Expected: 3 passed.

- [ ] **Step 5: Write failing page test (AC-4, AC-5 via MSW fixture)**

Create `tests/fixtures/api/projects/create_response.json`:

```json
{
  "id": "proj_new_001",
  "title": "New Project",
  "category": "pending_classification",
  "current_phase": 0,
  "latest_reached_phase": 0,
  "progress": 0,
  "status": "in_progress",
  "updated_at": "2026-04-17T10:00:00Z"
}
```

Create `tests/unit/frontend/pages/NewProject.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { NewProject } from "@frontend/pages/NewProject";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("NewProject page", () => {
  it("AC-4 navigates to /projects/:id after success", async () => {
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter initialEntries={["/projects/new"]}>
          <Routes>
            <Route path="/projects/new" element={<NewProject />} />
            <Route path="/projects/:id" element={<div>workflow page {window.location.pathname}</div>} />
            <Route path="/projects/:id/phases/:phase" element={<div data-testid="phase-landing">phase-landing</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await userEvent.type(screen.getByLabelText(/标题/), "Ok");
    await userEvent.type(screen.getByLabelText(/描述/), "这是一个长度足够的项目描述");
    await userEvent.click(screen.getByRole("button", { name: /创建/ }));
    await screen.findByTestId("phase-landing");
  });
});
```

- [ ] **Step 6: Run — RED**

```bash
cd src/frontend && pnpm vitest run pages/NewProject.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 7: Implement useCreateProject + NewProject**

Create `src/frontend/hooks/useCreateProject.ts`:

```typescript
import { useMutation } from "@tanstack/react-query"
import { apiClient } from "../api/client"
import type { ProjectListItem } from "../types/project"

export interface CreateProjectInput { title: string; description: string }

export function useCreateProject() {
  return useMutation({
    mutationFn: (input: CreateProjectInput) =>
      apiClient.post<ProjectListItem>("/api/v1/projects", input),
  })
}
```

Create `src/frontend/pages/NewProject.tsx`:

```tsx
import { useNavigate } from "react-router-dom"
import { CreateProjectForm } from "../components/CreateProjectForm"
import { useCreateProject } from "../hooks/useCreateProject"

export function NewProject(): JSX.Element {
  const nav = useNavigate()
  const mutation = useCreateProject()
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">新建项目</h1>
      <CreateProjectForm
        isSubmitting={mutation.isPending}
        onSubmit={(input) =>
          mutation.mutate(input, {
            onSuccess: (data) => nav(`/projects/${data.id}`),
          })
        }
      />
    </div>
  )
}
```

- [ ] **Step 8: Extend MSW handlers + fixture map**

Modify `src/frontend/mocks/handlers.ts` — add POST handler for `/api/v1/projects` returning `create_response.json`. Update `tests/fixtures/api/projects/_index.json` to map it.

- [ ] **Step 9: Wire route**

Modify `src/frontend/pages/AppRouter.tsx`:

```tsx
import { NewProject } from "./NewProject"
// inside <Routes>:
<Route path="/projects/new" element={<NewProject />} />
```

- [ ] **Step 10: Run page test — GREEN**

```bash
cd src/frontend && pnpm vitest run pages/NewProject.test.tsx 2>&1 | tail -5
```
Expected: 1 passed.

- [ ] **Step 11: Rewrite pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_002.py` to shell out to vitest per AC (see Task 1 Step 17 pattern, 5 classes matching AC-1..AC-5).

- [ ] **Step 12: Run pytest**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_002.py -v 2>&1 | tail -10
```
Expected: 5 passed (AC-1..AC-5).

- [ ] **Step 13: Commit**

```bash
git add src/frontend/hooks/useCreateProject.ts src/frontend/components/CreateProjectForm.tsx src/frontend/pages/NewProject.tsx src/frontend/pages/AppRouter.tsx src/frontend/mocks/handlers.ts tests/unit/frontend/components/CreateProjectForm.test.tsx tests/unit/frontend/pages/NewProject.test.tsx tests/unit/frontend/test_spec_e_002.py tests/fixtures/api/projects/create_response.json tests/fixtures/api/projects/_index.json
git commit -m "[SPEC-E-002] NewProject wizard: title + description (>=10 char) + POST + redirect"
```

---

## Task 3: State Recovery (E-003)

**Files:**
- Create: `src/frontend/types/project_state.ts`
- Create: `src/frontend/hooks/useProjectState.ts`
- Create: `src/frontend/components/PhaseNavigation.tsx`
- Create: `src/frontend/components/LoadingState.tsx`
- Create: `src/frontend/components/ErrorState.tsx`
- Create: `src/frontend/pages/WorkflowPage.tsx`
- Create: `tests/unit/frontend/hooks/useProjectState.test.tsx`
- Create: `tests/unit/frontend/pages/WorkflowPage.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_003.py`
- Modify: `src/frontend/pages/AppRouter.tsx`

- [ ] **Step 1: Failing test for useProjectState**

Create `tests/unit/frontend/hooks/useProjectState.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useProjectState } from "@frontend/hooks/useProjectState";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function wrapper() {
  const qc = createQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useProjectState", () => {
  it("AC-1,AC-2 fetches ProjectState with all fields defined", async () => {
    const { result } = renderHook(() => useProjectState("proj_001"), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 10000 });
    const s = result.current.data!;
    expect(s.project).toBeDefined();
    expect(s.phases).toBeDefined();
    expect(s.preferences).toBeDefined();
    expect(s.system_status).toBeDefined();
    expect(Array.isArray(s.phases)).toBe(true);
  });
});
```

- [ ] **Step 2: RED**

```bash
cd src/frontend && pnpm vitest run hooks/useProjectState.test.tsx 2>&1 | tail -10
```
Expected: FAIL.

- [ ] **Step 3: Implement types + hook**

Create `src/frontend/types/project_state.ts`:

```typescript
export type { ProjectState, PhaseState } from "../../shared/types/project_state"
```

Create `src/frontend/hooks/useProjectState.ts`:

```typescript
import { useQuery } from "@tanstack/react-query"
import { apiClient } from "../api/client"
import type { ProjectState } from "../../shared/types/project_state"

export function useProjectState(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.get<ProjectState>(`/api/v1/projects/${projectId}/state`),
    enabled: !!projectId,
  })
}
```

Ensure MSW handler maps `/api/v1/projects/:id/state` to `detail_p3.json`. Verify handler file imports and re-exports the fixture.

- [ ] **Step 4: Run — GREEN**

```bash
cd src/frontend && pnpm vitest run hooks/useProjectState.test.tsx 2>&1 | tail -5
```
Expected: 1 passed.

- [ ] **Step 5: Write failing test for WorkflowPage (AC-3, AC-4, AC-5, AC-6)**

Create `tests/unit/frontend/pages/WorkflowPage.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { WorkflowPage } from "@frontend/pages/WorkflowPage";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderAt(path: string) {
  return render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/projects/:id/phases/:phase" element={<WorkflowPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkflowPage", () => {
  it("AC-3 highlights current_phase in phase navigation", async () => {
    renderAt("/projects/proj_001/phases/3");
    await waitFor(() => expect(screen.getByTestId("phase-nav-3")).toHaveAttribute("data-active", "true"));
  });

  it("AC-4 renders phase-specific preview slot for current_phase", async () => {
    renderAt("/projects/proj_001/phases/3");
    await waitFor(() => expect(screen.getByTestId("preview-slot-p3")).toBeInTheDocument());
  });

  it("AC-5 shows loading state during fetch", async () => {
    server.use(
      http.get("/api/v1/projects/:id/state", async () => {
        await new Promise((r) => setTimeout(r, 200));
        return HttpResponse.json({ project: {}, phases: [], preferences: {}, system_status: {} });
      }),
    );
    renderAt("/projects/proj_001/phases/0");
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
  });

  it("AC-6 shows error state with retry button on API failure", async () => {
    server.use(
      http.get("/api/v1/projects/:id/state", () =>
        HttpResponse.json({ error_code: "EVID_5002", message: "worker down" }, { status: 500 }),
      ),
    );
    renderAt("/projects/proj_001/phases/0");
    await waitFor(() => expect(screen.getByTestId("error-state")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /重试/ })).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: RED**

```bash
cd src/frontend && pnpm vitest run pages/WorkflowPage.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 7: Implement Loading / Error / PhaseNavigation / WorkflowPage**

Create `src/frontend/components/LoadingState.tsx`:
```tsx
export function LoadingState(): JSX.Element {
  return <div data-testid="loading-state" className="p-6">加载中...</div>
}
```

Create `src/frontend/components/ErrorState.tsx`:
```tsx
interface Props { message: string; onRetry: () => void }
export function ErrorState({ message, onRetry }: Props): JSX.Element {
  return (
    <div data-testid="error-state" className="p-6 space-y-2">
      <div className="text-red-600">加载失败: {message}</div>
      <button className="px-3 py-1 border rounded" onClick={onRetry}>重试</button>
    </div>
  )
}
```

Create `src/frontend/components/PhaseNavigation.tsx`:
```tsx
interface Props { currentPhase: number; phases: { phase: number; status?: string }[] }
export function PhaseNavigation({ currentPhase, phases }: Props): JSX.Element {
  return (
    <nav className="flex gap-2 overflow-x-auto">
      {phases.map((p) => (
        <div
          key={p.phase}
          data-testid={`phase-nav-${p.phase}`}
          data-active={p.phase === currentPhase ? "true" : "false"}
          className={p.phase === currentPhase ? "px-3 py-1 bg-blue-600 text-white rounded" : "px-3 py-1 border rounded"}
        >
          P{p.phase}
        </div>
      ))}
    </nav>
  )
}
```

Create `src/frontend/pages/WorkflowPage.tsx`:
```tsx
import { useParams } from "react-router-dom"
import { useProjectState } from "../hooks/useProjectState"
import { PhaseNavigation } from "../components/PhaseNavigation"
import { LoadingState } from "../components/LoadingState"
import { ErrorState } from "../components/ErrorState"

export function WorkflowPage(): JSX.Element {
  const { id = "", phase = "0" } = useParams<{ id: string; phase: string }>()
  const currentPhase = Number(phase)
  const { data, isLoading, isError, error, refetch } = useProjectState(id)

  if (isLoading) return <LoadingState />
  if (isError || !data) {
    const msg = (error as { message?: string } | null)?.message ?? "未知错误"
    return <ErrorState message={msg} onRetry={() => refetch()} />
  }

  const phases = data.phases?.length ? data.phases : Array.from({ length: 12 }, (_, i) => ({ phase: i }))

  return (
    <div className="p-6 space-y-4">
      <PhaseNavigation currentPhase={currentPhase} phases={phases as { phase: number }[]} />
      <div data-testid={`preview-slot-p${currentPhase}`} className="border rounded p-4 min-h-[200px]">
        <div className="text-gray-500">P{currentPhase} 预览 (Wave 3b 填充)</div>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Add redirect route `/projects/:id`**

Modify `src/frontend/pages/AppRouter.tsx` to add:

```tsx
import { WorkflowPage } from "./WorkflowPage"
import { ProjectRedirect } from "./ProjectRedirect"
// ...
<Route path="/projects/:id" element={<ProjectRedirect />} />
<Route path="/projects/:id/phases/:phase" element={<WorkflowPage />} />
```

Create `src/frontend/pages/ProjectRedirect.tsx`:

```tsx
import { Navigate, useParams } from "react-router-dom"
import { useProjectState } from "../hooks/useProjectState"
import { LoadingState } from "../components/LoadingState"
import { ErrorState } from "../components/ErrorState"

export function ProjectRedirect(): JSX.Element {
  const { id = "" } = useParams()
  const { data, isLoading, isError, refetch } = useProjectState(id)
  if (isLoading) return <LoadingState />
  if (isError || !data) return <ErrorState message="无法加载项目" onRetry={() => refetch()} />
  const phase = data.project?.latest_reached_phase ?? data.project?.current_phase ?? 0
  return <Navigate to={`/projects/${id}/phases/${phase}`} replace />
}
```

- [ ] **Step 9: Run WorkflowPage test — GREEN**

```bash
cd src/frontend && pnpm vitest run pages/WorkflowPage.test.tsx 2>&1 | tail -10
```
Expected: 4 passed.

- [ ] **Step 10: Rewrite pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_003.py` with 6 AC classes calling vitest with patterns `AC-1`..`AC-6`. Match the Step 5 test names.

- [ ] **Step 11: Run pytest + full tsc**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_003.py -v 2>&1 | tail -10
cd src/frontend && pnpm tsc 2>&1 | tail -5
```
Expected: 6 passed, tsc 0 errors.

- [ ] **Step 12: Commit**

```bash
git add src/frontend/types/project_state.ts src/frontend/hooks/useProjectState.ts src/frontend/components/LoadingState.tsx src/frontend/components/ErrorState.tsx src/frontend/components/PhaseNavigation.tsx src/frontend/pages/WorkflowPage.tsx src/frontend/pages/ProjectRedirect.tsx src/frontend/pages/AppRouter.tsx tests/unit/frontend/hooks/useProjectState.test.tsx tests/unit/frontend/pages/WorkflowPage.test.tsx tests/unit/frontend/test_spec_e_003.py
git commit -m "[SPEC-E-003] state recovery: useProjectState hook + WorkflowPage + Phase nav + Loading/Error states"
```

---

## Task 4: ArtifactStatusBadge (E-007)

**Files:**
- Create: `src/frontend/components/ArtifactStatusBadge.tsx`
- Create: `src/frontend/hooks/useArtifactStatus.ts`
- Create: `tests/unit/frontend/components/ArtifactStatusBadge.test.tsx`
- Modify: `src/frontend/components/PhaseNavigation.tsx`
- Modify: `tests/unit/frontend/test_spec_e_007.py`

- [ ] **Step 1: Failing badge test**

Create `tests/unit/frontend/components/ArtifactStatusBadge.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ArtifactStatusBadge } from "@frontend/components/ArtifactStatusBadge";

describe("ArtifactStatusBadge", () => {
  it("AC-1 renders nothing for status=ok", () => {
    const { container } = render(<ArtifactStatusBadge status="ok" />);
    expect(container.firstChild).toBeNull();
  });

  it("AC-2 renders red badge with 'damaged' label for status=damaged", () => {
    render(<ArtifactStatusBadge status="damaged" />);
    const el = screen.getByText(/damaged/i);
    expect(el).toBeInTheDocument();
    expect(el.className).toMatch(/red|danger/i);
  });

  it("AC-3 renders red badge with 'missing' label for status=missing", () => {
    render(<ArtifactStatusBadge status="missing" />);
    const el = screen.getByText(/missing/i);
    expect(el).toBeInTheDocument();
    expect(el.className).toMatch(/red|danger/i);
  });
});
```

- [ ] **Step 2: RED**

```bash
cd src/frontend && pnpm vitest run components/ArtifactStatusBadge.test.tsx 2>&1 | tail -5
```
Expected: FAIL module-not-found.

- [ ] **Step 3: Implement badge**

Create `src/frontend/components/ArtifactStatusBadge.tsx`:

```tsx
type Status = "ok" | "damaged" | "missing"
interface Props { status: Status; compact?: boolean }

const LABELS: Record<Status, string> = { ok: "", damaged: "damaged", missing: "missing" }

export function ArtifactStatusBadge({ status, compact = false }: Props): JSX.Element | null {
  if (status === "ok") return null
  return (
    <span
      title={LABELS[status]}
      className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded"
    >
      {compact ? "!" : LABELS[status]}
    </span>
  )
}
```

Create `src/frontend/hooks/useArtifactStatus.ts`:

```typescript
import type { PhaseState } from "../../shared/types/project_state"

export function useArtifactStatus(phases: PhaseState[] | undefined, phase: number): "ok" | "damaged" | "missing" {
  const p = phases?.find((x) => x.phase === phase)
  return (p?.artifact_status as "ok" | "damaged" | "missing") ?? "ok"
}
```

- [ ] **Step 4: GREEN**

```bash
cd src/frontend && pnpm vitest run components/ArtifactStatusBadge.test.tsx 2>&1 | tail -5
```
Expected: 3 passed.

- [ ] **Step 5: Integrate into PhaseNavigation**

Modify `src/frontend/components/PhaseNavigation.tsx` — add badge next to phase label:

```tsx
import { ArtifactStatusBadge } from "./ArtifactStatusBadge"
// ...inside the map:
<div ... >
  P{p.phase}
  <ArtifactStatusBadge status={(p as any).artifact_status ?? "ok"} compact />
</div>
```

- [ ] **Step 6: Add integration test — AC-4, AC-5**

Append to `tests/unit/frontend/components/ArtifactStatusBadge.test.tsx`:

```tsx
import { PhaseNavigation } from "@frontend/components/PhaseNavigation";

describe("Badge integration via PhaseNavigation", () => {
  it("AC-4 badge appears in phase navigation item", () => {
    render(
      <PhaseNavigation
        currentPhase={0}
        phases={[{ phase: 0, artifact_status: "ok" } as any, { phase: 1, artifact_status: "damaged" } as any]}
      />,
    );
    expect(screen.getByText(/damaged/i)).toBeInTheDocument();
  });

  it("AC-5 badge reflects new artifact_status when phases array changes (simulated refresh)", () => {
    const { rerender } = render(
      <PhaseNavigation currentPhase={0} phases={[{ phase: 0, artifact_status: "ok" } as any]} />,
    );
    expect(screen.queryByText(/damaged/i)).toBeNull();
    rerender(<PhaseNavigation currentPhase={0} phases={[{ phase: 0, artifact_status: "damaged" } as any]} />);
    expect(screen.getByText(/damaged/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 7: Run all 5 tests — GREEN**

```bash
cd src/frontend && pnpm vitest run components/ArtifactStatusBadge.test.tsx 2>&1 | tail -10
```
Expected: 5 passed.

- [ ] **Step 8: Rewrite pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_007.py` — 5 classes shelling to vitest.

- [ ] **Step 9: Run pytest**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_007.py -v 2>&1 | tail -10
```
Expected: 5 passed.

- [ ] **Step 10: Commit**

```bash
git add src/frontend/components/ArtifactStatusBadge.tsx src/frontend/hooks/useArtifactStatus.ts src/frontend/components/PhaseNavigation.tsx tests/unit/frontend/components/ArtifactStatusBadge.test.tsx tests/unit/frontend/test_spec_e_007.py
git commit -m "[SPEC-E-007] ArtifactStatusBadge (ok/damaged/missing) + PhaseNavigation integration"
```

---

## Task 5: AgentActivityPanel (E-008)

**Files:**
- Create: `src/frontend/types/events.ts`
- Create: `src/frontend/hooks/useEventStream.ts`
- Create: `src/frontend/components/ActivityEventRow.tsx`
- Create: `src/frontend/components/AgentActivityPanel.tsx`
- Create: `tests/unit/frontend/hooks/useEventStream.test.tsx`
- Create: `tests/unit/frontend/components/AgentActivityPanel.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_008.py`
- Modify: `src/frontend/mocks/handlers.ts`
- Create: `tests/fixtures/api/events/list_response.json`

- [ ] **Step 1: Failing AgentActivityPanel test**

Create fixture `tests/fixtures/api/events/list_response.json`:

```json
[
  {"id": "e1", "type": "phase.advanced", "project_id": "proj_001", "timestamp": "2026-04-17T10:00:00Z", "payload": {"agent_name": "ScriptAgent", "action": "generate", "progress": "100%"}},
  {"id": "e2", "type": "agent.call", "project_id": "proj_001", "timestamp": "2026-04-17T10:05:00Z", "payload": {"agent_name": "TTSAgent", "action": "synthesize", "result": "ok"}},
  {"id": "e3", "type": "gate.failed", "project_id": "proj_001", "timestamp": "2026-04-17T10:07:00Z", "payload": {"agent_name": "GateAgent", "action": "check", "result": "fail"}}
]
```

Add POST-like mapping in `_index.json` (or HTTP-level mapping in handlers).

Create `tests/unit/frontend/components/AgentActivityPanel.test.tsx`:

```tsx
import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Server } from "mock-socket";
import React from "react";
import { server } from "@frontend/mocks/server";
import { createQueryClient } from "@frontend/lib/queryClient";
import { AgentActivityPanel } from "@frontend/components/AgentActivityPanel";

const WS_URL = "ws://localhost:8000/ws/proj_001/events";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function wrap() {
  const qc = createQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("AgentActivityPanel", () => {
  it("AC-1 renders events in [HH:MM:SS] [agent] [action] [result] format", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const rows = screen.getAllByTestId("activity-row");
    expect(rows[0].textContent).toMatch(/\[\d{2}:\d{2}:\d{2}\].*\[.+\].*\[.+\]/);
  });

  it("AC-2 fetches initial history via GET /events?limit=50", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getByText(/ScriptAgent/)).toBeInTheDocument());
  });

  it("AC-3 appends live event from WS", async () => {
    const mockWs = new Server(WS_URL);
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    act(() => {
      mockWs.emit("message", JSON.stringify({
        id: "eLive", type: "agent.call", project_id: "proj_001",
        timestamp: new Date().toISOString(),
        payload: { agent_name: "LiveAgent", action: "now", result: "ok" },
      }));
    });
    await waitFor(() => expect(screen.getByText(/LiveAgent/)).toBeInTheDocument());
    mockWs.stop();
  });

  it("AC-4 DOM update within 200ms of WS message", async () => {
    const mockWs = new Server(WS_URL + "/perf");
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/perf"} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const t0 = performance.now();
    act(() => {
      mockWs.emit("message", JSON.stringify({
        id: "eFast", type: "agent.call", project_id: "proj_001",
        timestamp: new Date().toISOString(),
        payload: { agent_name: "FastAgent", action: "x", result: "ok" },
      }));
    });
    await waitFor(() => expect(screen.getByText(/FastAgent/)).toBeInTheDocument());
    expect(performance.now() - t0).toBeLessThan(200);
    mockWs.stop();
  });

  it("AC-6 dedup: WS re-delivery of same id is not rendered twice", async () => {
    const mockWs = new Server(WS_URL + "/dedup");
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/dedup"} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const payload = JSON.stringify({
      id: "eDup", type: "agent.call", project_id: "proj_001",
      timestamp: new Date().toISOString(),
      payload: { agent_name: "DupAgent", action: "x", result: "ok" },
    });
    act(() => { mockWs.emit("message", payload); mockWs.emit("message", payload); });
    await waitFor(() => expect(screen.getAllByText(/DupAgent/).length).toBe(1));
    mockWs.stop();
  });
});
```

- [ ] **Step 2: RED**

```bash
cd src/frontend && pnpm vitest run components/AgentActivityPanel.test.tsx 2>&1 | tail -10
```
Expected: FAIL.

- [ ] **Step 3: Implement types + hook + component**

Create `src/frontend/types/events.ts`:

```typescript
export interface AgentEvent {
  id: string
  type: string
  project_id: string
  timestamp: string
  payload: { agent_name?: string; action?: string; result?: string; progress?: string; [k: string]: unknown }
}
```

Create `src/frontend/hooks/useEventStream.ts`:

```typescript
import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { apiClient } from "../api/client"
import { useWebSocket } from "./useWebSocket"
import type { AgentEvent } from "../types/events"

const LIMIT = 50

export function useEventStream(projectId: string, wsUrl: string) {
  const history = useQuery({
    queryKey: ["events", projectId],
    queryFn: () => apiClient.get<AgentEvent[]>(`/api/v1/projects/${projectId}/events?limit=${LIMIT}`),
    enabled: !!projectId,
  })
  const [live, setLive] = useState<AgentEvent[]>([])
  useWebSocket(wsUrl, {
    enabled: !!wsUrl,
    onMessage: (data) => {
      const evt = data as AgentEvent
      if (!evt?.id) return
      setLive((prev) => (prev.some((e) => e.id === evt.id) ? prev : [...prev, evt]))
    },
  })
  const merged = useMemo(() => {
    const seen = new Set<string>()
    const all = [...(history.data ?? []), ...live]
    const uniq: AgentEvent[] = []
    for (const e of all) {
      if (seen.has(e.id)) continue
      seen.add(e.id); uniq.push(e)
    }
    return uniq.slice(-LIMIT)
  }, [history.data, live])
  return { events: merged, isLoading: history.isLoading, isError: history.isError }
}
```

Create `src/frontend/components/ActivityEventRow.tsx`:

```tsx
import type { AgentEvent } from "../types/events"

interface Props { event: AgentEvent }

export function ActivityEventRow({ event }: Props): JSX.Element {
  const ts = new Date(event.timestamp)
  const hhmmss = ts.toTimeString().slice(0, 8)
  const agent = event.payload?.agent_name ?? "-"
  const action = event.payload?.action ?? event.type
  const result = event.payload?.result ?? event.payload?.progress ?? ""
  return (
    <div data-testid="activity-row" className="text-xs font-mono py-0.5">
      [{hhmmss}] [{agent}] [{action}] [{result}]
    </div>
  )
}
```

Create `src/frontend/components/AgentActivityPanel.tsx`:

```tsx
import { useEventStream } from "../hooks/useEventStream"
import { ActivityEventRow } from "./ActivityEventRow"

interface Props { projectId: string; wsUrl: string }

export function AgentActivityPanel({ projectId, wsUrl }: Props): JSX.Element {
  const { events, isLoading } = useEventStream(projectId, wsUrl)
  if (isLoading) return <div>加载事件...</div>
  return (
    <div className="border rounded p-3 max-h-[400px] overflow-y-auto">
      <div className="text-sm font-semibold mb-2">Agent 活动</div>
      {events.map((e) => <ActivityEventRow key={e.id} event={e} />)}
    </div>
  )
}
```

- [ ] **Step 4: Add MSW handler for GET events**

Modify `src/frontend/mocks/handlers.ts`:

```typescript
http.get("/api/v1/projects/:id/events", () => HttpResponse.json(eventsListFixture))
```

Add `tests/fixtures/api/events/list_response.json` to index (`tests/fixtures/api/events/_index.json`).

- [ ] **Step 5: GREEN**

```bash
cd src/frontend && pnpm vitest run components/AgentActivityPanel.test.tsx 2>&1 | tail -10
```
Expected: 5 passed.

- [ ] **Step 6: Write AC-5 scroll-to-top test (pagination signal only)**

Append to `AgentActivityPanel.test.tsx`:

```tsx
it("AC-5 scroll-to-top emits onLoadMore signal", async () => {
  const onLoadMore = vi.fn();
  render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/scroll"} onLoadMore={onLoadMore} />, { wrapper: wrap() });
  await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
  const panel = screen.getByTestId("activity-panel-scroll");
  // simulate scroll to top
  act(() => { panel.scrollTop = 0; panel.dispatchEvent(new Event("scroll")); });
  expect(onLoadMore).toHaveBeenCalled();
});
```

Update component: wrap list in `<div data-testid="activity-panel-scroll" onScroll={...}>`; add `onLoadMore?: () => void` prop; invoke when `scrollTop === 0`.

- [ ] **Step 7: GREEN + regression**

```bash
cd src/frontend && pnpm vitest run components/AgentActivityPanel.test.tsx 2>&1 | tail -10
```
Expected: 6 passed.

- [ ] **Step 8: Pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_008.py` — 6 classes shelling to vitest.

- [ ] **Step 9: Run pytest**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_008.py -v 2>&1 | tail -10
```
Expected: 6 passed.

- [ ] **Step 10: Commit**

```bash
git add src/frontend/types/events.ts src/frontend/hooks/useEventStream.ts src/frontend/components/ActivityEventRow.tsx src/frontend/components/AgentActivityPanel.tsx src/frontend/mocks/handlers.ts tests/fixtures/api/events/list_response.json tests/fixtures/api/events/_index.json tests/unit/frontend/components/AgentActivityPanel.test.tsx tests/unit/frontend/test_spec_e_008.py
git commit -m "[SPEC-E-008] AgentActivityPanel: REST history + WS live + dedup + 200ms DOM + scroll-to-top"
```

---

## Task 6: Error UX Map (E-009)

**Files:**
- Create: `src/frontend/types/errors.ts`
- Create: `src/frontend/utils/errorUxMap.ts`
- Create: `src/frontend/hooks/useErrorHandler.ts`
- Create: `src/frontend/components/errors/TechnicalDetails.tsx`
- Create: `src/frontend/components/errors/ErrorToast.tsx`
- Create: `src/frontend/components/errors/ErrorModal.tsx`
- Create: `tests/unit/frontend/utils/errorUxMap.test.ts`
- Create: `tests/unit/frontend/components/errors/ErrorToast.test.tsx`
- Create: `tests/unit/frontend/components/errors/ErrorModal.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_009.py`

- [ ] **Step 1: Failing test for errorUxMap**

Create `tests/unit/frontend/utils/errorUxMap.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { ERROR_UX_MAP, lookupErrorUx } from "@frontend/utils/errorUxMap";

const CODES = ["EVID_3002","EVID_3004","EVID_4001","EVID_4002","EVID_2001","EVID_5001","EVID_5002","EVID_3001"];

describe("ERROR_UX_MAP", () => {
  it("AC-1 maps all 8 error codes", () => {
    for (const c of CODES) expect(ERROR_UX_MAP[c]).toBeDefined();
  });

  it("AC-2 is pure static (no function calls, plain object)", () => {
    for (const c of CODES) {
      const entry = ERROR_UX_MAP[c];
      expect(typeof entry.tier).toBe("string");
      expect(typeof entry.component).toBe("string");
      expect(Array.isArray(entry.actions)).toBe(true);
    }
  });

  it("AC-3 EVID_3002 + EVID_3004 are auto_handling toast", () => {
    expect(ERROR_UX_MAP.EVID_3002.tier).toBe("auto_handling");
    expect(ERROR_UX_MAP.EVID_3002.component).toBe("toast");
    expect(ERROR_UX_MAP.EVID_3004.tier).toBe("auto_handling");
  });

  it("AC-4 user_choice entries each have >= 2 actions", () => {
    for (const c of ["EVID_4001","EVID_4002","EVID_2001"]) {
      expect(ERROR_UX_MAP[c].tier).toBe("user_choice");
      expect(ERROR_UX_MAP[c].component).toBe("modal");
      expect(ERROR_UX_MAP[c].actions.length).toBeGreaterThanOrEqual(2);
    }
  });

  it("AC-5 user_action entries render modal", () => {
    for (const c of ["EVID_5001","EVID_5002","EVID_3001"]) {
      expect(ERROR_UX_MAP[c].tier).toBe("user_action");
      expect(ERROR_UX_MAP[c].component).toBe("modal");
    }
  });

  it("AC-6 every code has >= 1 recovery action", () => {
    for (const c of CODES) expect(ERROR_UX_MAP[c].actions.length).toBeGreaterThanOrEqual(1);
  });

  it("AC-7 unknown code falls back to user_action generic modal", () => {
    const fb = lookupErrorUx("UNKNOWN_9999");
    expect(fb.tier).toBe("user_action");
    expect(fb.component).toBe("modal");
    expect(fb.actions.length).toBeGreaterThanOrEqual(1);
  });
});
```

- [ ] **Step 2: RED**

```bash
cd src/frontend && pnpm vitest run utils/errorUxMap.test.ts 2>&1 | tail -5
```
Expected: FAIL.

- [ ] **Step 3: Implement errorUxMap + types**

Create `src/frontend/types/errors.ts`:

```typescript
export type ErrorTier = "auto_handling" | "user_choice" | "user_action"
export type ErrorComponent = "toast" | "modal"

export interface ErrorUxEntry {
  tier: ErrorTier
  component: ErrorComponent
  actions: string[]
}

export interface NormalizedError {
  error_code: string
  message: string
  status: number
  details?: unknown
}
```

Create `src/frontend/utils/errorUxMap.ts`:

```typescript
import type { ErrorUxEntry } from "../types/errors"

export const ERROR_UX_MAP: Record<string, ErrorUxEntry> = {
  EVID_3002: { tier: "auto_handling", component: "toast", actions: ["retry_auto"] },
  EVID_3004: { tier: "auto_handling", component: "toast", actions: ["retry_auto", "degrade"] },
  EVID_4001: { tier: "user_choice",   component: "modal", actions: ["regenerate", "skip_phase"] },
  EVID_4002: { tier: "user_choice",   component: "modal", actions: ["regenerate", "use_prev_version"] },
  EVID_2001: { tier: "user_choice",   component: "modal", actions: ["fix_items", "force_skip"] },
  EVID_5001: { tier: "user_action",   component: "modal", actions: ["check_config", "contact_admin"] },
  EVID_5002: { tier: "user_action",   component: "modal", actions: ["restart_worker", "check_logs"] },
  EVID_3001: { tier: "user_action",   component: "modal", actions: ["retry_manual", "export_logs"] },
}

const FALLBACK: ErrorUxEntry = {
  tier: "user_action", component: "modal", actions: ["contact_admin"],
}

export function lookupErrorUx(code: string): ErrorUxEntry {
  return ERROR_UX_MAP[code] ?? FALLBACK
}
```

- [ ] **Step 4: GREEN**

```bash
cd src/frontend && pnpm vitest run utils/errorUxMap.test.ts 2>&1 | tail -10
```
Expected: 7 passed.

- [ ] **Step 5: Write failing tests for ErrorToast + ErrorModal**

Create `tests/unit/frontend/components/errors/ErrorToast.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorToast } from "@frontend/components/errors/ErrorToast";

describe("ErrorToast", () => {
  it("renders ETA and non-modal layout", () => {
    render(<ErrorToast code="EVID_3002" message="Agent 超时" etaSec={5} />);
    expect(screen.getByText(/Agent 超时/)).toBeInTheDocument();
    expect(screen.getByText(/5s/)).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
```

Create `tests/unit/frontend/components/errors/ErrorModal.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorModal } from "@frontend/components/errors/ErrorModal";

describe("ErrorModal", () => {
  it("renders >= 2 action buttons for user_choice tier", () => {
    const onAction = vi.fn();
    render(
      <ErrorModal
        code="EVID_4001" message="产物不存在"
        actions={["regenerate", "skip_phase"]} tier="user_choice"
        onAction={onAction} onClose={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("button").length).toBeGreaterThanOrEqual(2);
  });

  it("renders expandable technical details for user_action tier", async () => {
    render(
      <ErrorModal
        code="EVID_3001" message="Agent 崩溃"
        actions={["retry_manual"]} tier="user_action"
        details={{ stack: "traceback…" }}
        onAction={vi.fn()} onClose={vi.fn()}
      />,
    );
    const toggle = screen.getByRole("button", { name: /技术详情/ });
    await userEvent.click(toggle);
    expect(screen.getByText(/traceback/)).toBeInTheDocument();
  });

  it("clicking an action calls onAction with action name", async () => {
    const onAction = vi.fn();
    render(
      <ErrorModal
        code="EVID_4001" message="x" actions={["regenerate"]} tier="user_choice"
        onAction={onAction} onClose={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /regenerate/ }));
    expect(onAction).toHaveBeenCalledWith("regenerate");
  });
});
```

- [ ] **Step 6: RED**

```bash
cd src/frontend && pnpm vitest run components/errors 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 7: Implement components**

Create `src/frontend/components/errors/TechnicalDetails.tsx`:

```tsx
import { useState } from "react"

export function TechnicalDetails({ details }: { details: unknown }): JSX.Element {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button
        type="button" className="text-xs text-blue-600 underline"
        onClick={() => setOpen(!open)}
      >
        {open ? "隐藏" : "查看"} 技术详情
      </button>
      {open && (
        <pre className="mt-2 p-2 bg-gray-100 text-xs overflow-auto max-h-48">
          {JSON.stringify(details, null, 2)}
        </pre>
      )}
    </div>
  )
}
```

Create `src/frontend/components/errors/ErrorToast.tsx`:

```tsx
interface Props { code: string; message: string; etaSec?: number }

export function ErrorToast({ code, message, etaSec }: Props): JSX.Element {
  return (
    <div className="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded shadow">
      <div className="font-mono text-xs">{code}</div>
      <div className="text-sm">{message}</div>
      {etaSec !== undefined && <div className="text-xs opacity-70">自动重试中 (ETA {etaSec}s)</div>}
    </div>
  )
}
```

Create `src/frontend/components/errors/ErrorModal.tsx`:

```tsx
import { TechnicalDetails } from "./TechnicalDetails"
import type { ErrorTier } from "../../types/errors"

interface Props {
  code: string
  message: string
  actions: string[]
  tier: ErrorTier
  details?: unknown
  onAction: (action: string) => void
  onClose: () => void
}

export function ErrorModal({ code, message, actions, tier, details, onAction, onClose }: Props): JSX.Element {
  return (
    <div role="dialog" className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full space-y-4">
        <div>
          <div className="font-mono text-xs text-gray-500">{code}</div>
          <div className="text-lg font-semibold">{message}</div>
        </div>
        {tier === "user_action" && details !== undefined && <TechnicalDetails details={details} />}
        <div className="flex gap-2 justify-end">
          {actions.map((a) => (
            <button
              key={a} className="px-3 py-1 border rounded hover:bg-gray-50"
              onClick={() => onAction(a)}
            >{a}</button>
          ))}
          <button className="px-3 py-1 text-gray-500" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
```

Create `src/frontend/hooks/useErrorHandler.ts`:

```typescript
import { toast } from "sonner"
import { lookupErrorUx } from "../utils/errorUxMap"
import type { NormalizedError } from "../types/errors"

export function useErrorHandler() {
  return {
    handle(err: NormalizedError) {
      const ux = lookupErrorUx(err.error_code)
      if (ux.component === "toast") {
        toast.error(`[${err.error_code}] ${err.message}`, {
          description: ux.actions.includes("retry_auto") ? "自动重试中..." : undefined,
        })
      }
      return ux
    },
  }
}
```

- [ ] **Step 8: GREEN**

```bash
cd src/frontend && pnpm vitest run components/errors 2>&1 | tail -10
```
Expected: 4 passed (1 toast + 3 modal).

- [ ] **Step 9: Pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_009.py` with 7 classes matching AC-1..AC-7.

- [ ] **Step 10: Run pytest**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_009.py -v 2>&1 | tail -10
```
Expected: 7 passed.

- [ ] **Step 11: Commit**

```bash
git add src/frontend/types/errors.ts src/frontend/utils/errorUxMap.ts src/frontend/hooks/useErrorHandler.ts src/frontend/components/errors/ tests/unit/frontend/utils/errorUxMap.test.ts tests/unit/frontend/components/errors/ tests/unit/frontend/test_spec_e_009.py
git commit -m "[SPEC-E-009] ERROR_UX_MAP (8 codes) + ErrorToast/ErrorModal + fallback"
```

---

## Task 7: CandidateSelector (E-010)

**Files:**
- Create: `src/frontend/types/candidates.ts`
- Create: `src/frontend/hooks/useCandidateSelection.ts`
- Create: `src/frontend/components/CandidateCard.tsx`
- Create: `src/frontend/components/CandidateSelector.tsx`
- Create: `tests/unit/frontend/hooks/useCandidateSelection.test.tsx`
- Create: `tests/unit/frontend/components/CandidateSelector.test.tsx`
- Modify: `tests/unit/frontend/test_spec_e_010.py`

- [ ] **Step 1: Failing hook test (state machine + 60s reminder)**

Create `tests/unit/frontend/hooks/useCandidateSelection.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCandidateSelection } from "@frontend/hooks/useCandidateSelection";

const c1 = { id: "c1", is_recommended: true, preview_url: "u1" };
const c2 = { id: "c2", is_recommended: false, preview_url: "u2" };

describe("useCandidateSelection", () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); });

  it("AC-2 state transitions idle -> previewing -> selected -> confirmed", () => {
    const { result } = renderHook(() => useCandidateSelection([c1, c2], vi.fn()));
    expect(result.current.state).toBe("idle");
    act(() => result.current.preview("c1"));
    expect(result.current.state).toBe("previewing");
    act(() => result.current.select("c1"));
    expect(result.current.state).toBe("selected");
    act(() => result.current.confirm());
    expect(result.current.state).toBe("confirmed");
  });

  it("AC-3 two-step confirm: cannot confirm without select", () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useCandidateSelection([c1, c2], onConfirm));
    act(() => result.current.confirm());
    expect(onConfirm).not.toHaveBeenCalled();
    expect(result.current.state).toBe("idle");
  });

  it("AC-4 fires reminder exactly once after 60s idle", () => {
    const onReminder = vi.fn();
    renderHook(() => useCandidateSelection([c1, c2], vi.fn(), { onReminder, reminderMs: 60_000 }));
    act(() => { vi.advanceTimersByTime(59_000); });
    expect(onReminder).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(2_000); });
    expect(onReminder).toHaveBeenCalledOnce();
    act(() => { vi.advanceTimersByTime(60_000); });
    expect(onReminder).toHaveBeenCalledOnce();
  });

  it("AC-5 skipAndAccept confirms is_recommended candidate", () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useCandidateSelection([c1, c2], onConfirm));
    act(() => result.current.skipAndAccept());
    expect(onConfirm).toHaveBeenCalledWith("c1");
    expect(result.current.state).toBe("confirmed");
  });
});
```

- [ ] **Step 2: RED**

```bash
cd src/frontend && pnpm vitest run hooks/useCandidateSelection.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 3: Implement types + hook**

Create `src/frontend/types/candidates.ts`:

```typescript
export interface CandidateLike {
  id: string
  is_recommended: boolean
  preview_url?: string
  [k: string]: unknown
}

export type CandidateState = "idle" | "previewing" | "selected" | "confirmed"
```

Create `src/frontend/hooks/useCandidateSelection.ts`:

```typescript
import { useEffect, useRef, useState } from "react"
import type { CandidateLike, CandidateState } from "../types/candidates"

interface Options {
  onReminder?: () => void
  reminderMs?: number
}

export function useCandidateSelection<T extends CandidateLike>(
  candidates: T[],
  onConfirm: (candidateId: string) => void,
  opts: Options = {},
) {
  const { onReminder, reminderMs = 60_000 } = opts
  const [state, setState] = useState<CandidateState>("idle")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const reminderFired = useRef(false)

  useEffect(() => {
    if (state !== "idle" || reminderFired.current || !onReminder) return
    const t = setTimeout(() => {
      reminderFired.current = true
      onReminder()
    }, reminderMs)
    return () => clearTimeout(t)
  }, [state, onReminder, reminderMs])

  return {
    state,
    selectedId,
    preview(id: string) { setSelectedId(id); setState("previewing") },
    select(id: string) { setSelectedId(id); setState("selected") },
    confirm() {
      if (state !== "selected" || !selectedId) return
      setState("confirmed"); onConfirm(selectedId)
    },
    skipAndAccept() {
      const rec = candidates.find((c) => c.is_recommended) ?? candidates[0]
      if (!rec) return
      setSelectedId(rec.id); setState("confirmed"); onConfirm(rec.id)
    },
  }
}
```

- [ ] **Step 4: GREEN hook**

```bash
cd src/frontend && pnpm vitest run hooks/useCandidateSelection.test.tsx 2>&1 | tail -10
```
Expected: 4 passed.

- [ ] **Step 5: Failing CandidateSelector component test (AC-1, AC-6, AC-7, AC-8)**

Create `tests/unit/frontend/components/CandidateSelector.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "@frontend/mocks/server";
import { CandidateSelector } from "@frontend/components/CandidateSelector";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const candidates = [
  { id: "c1", is_recommended: true, preview_url: "u1" },
  { id: "c2", is_recommended: false, preview_url: "u2" },
];

describe("CandidateSelector", () => {
  it("AC-1 displays up to 3 candidates with preview capability", () => {
    const many = [...candidates, { id: "c3", is_recommended: false, preview_url: "u3" }, { id: "c4", is_recommended: false, preview_url: "u4" }];
    render(<CandidateSelector projectId="p1" phase={5} candidates={many} />);
    expect(screen.getAllByTestId("candidate-card").length).toBeLessThanOrEqual(3);
  });

  it("AC-6 confirm posts to /preferences/confirm with candidate_id", async () => {
    let body: unknown = null;
    server.use(
      http.post("/api/v1/projects/:id/preferences/confirm", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ok: true });
      }),
    );
    render(<CandidateSelector projectId="p1" phase={5} candidates={candidates} />);
    await userEvent.click(screen.getAllByTestId("candidate-card")[1]);                   // preview
    await userEvent.click(screen.getAllByRole("button", { name: /选择/ })[1]);          // select
    await userEvent.click(screen.getByRole("button", { name: /确认/ }));                 // confirm
    await vi.waitFor(() => expect(body).toMatchObject({ decisions: expect.any(Object) }));
    expect(JSON.stringify(body)).toContain("c2");
  });

  it("AC-7 accepts generic Candidate shape (compile-time + runtime smoke)", () => {
    render(
      <CandidateSelector
        projectId="p1" phase={8}
        candidates={[{ id: "x", is_recommended: true, custom_field: 42 } as any]}
      />,
    );
    expect(screen.getByTestId("candidate-card")).toBeInTheDocument();
  });

  it("AC-8 no unlock style_lock button exposed", () => {
    render(<CandidateSelector projectId="p1" phase={5} candidates={candidates} />);
    expect(screen.queryByRole("button", { name: /解锁/ })).toBeNull();
  });
});
```

- [ ] **Step 6: RED**

```bash
cd src/frontend && pnpm vitest run components/CandidateSelector.test.tsx 2>&1 | tail -10
```
Expected: FAIL module-not-found.

- [ ] **Step 7: Implement CandidateCard + CandidateSelector**

Create `src/frontend/components/CandidateCard.tsx`:

```tsx
import type { CandidateLike } from "../types/candidates"

interface Props<T extends CandidateLike> {
  candidate: T
  isActive: boolean
  onPreview: () => void
  onSelect: () => void
}

export function CandidateCard<T extends CandidateLike>({ candidate, isActive, onPreview, onSelect }: Props<T>): JSX.Element {
  return (
    <div
      data-testid="candidate-card"
      className={`border rounded p-3 cursor-pointer ${isActive ? "ring-2 ring-blue-500" : ""}`}
      onClick={onPreview}
    >
      {candidate.preview_url && <div className="h-20 bg-gray-100 mb-2" />}
      <div className="text-sm">
        {candidate.id}
        {candidate.is_recommended && <span className="ml-2 text-xs text-blue-600">推荐</span>}
      </div>
      <button
        className="mt-2 px-2 py-1 text-xs border rounded"
        onClick={(e) => { e.stopPropagation(); onSelect() }}
      >选择</button>
    </div>
  )
}
```

Create `src/frontend/components/CandidateSelector.tsx`:

```tsx
import { useMemo } from "react"
import { toast } from "sonner"
import { apiClient } from "../api/client"
import { CandidateCard } from "./CandidateCard"
import { useCandidateSelection } from "../hooks/useCandidateSelection"
import type { CandidateLike } from "../types/candidates"

interface Props<T extends CandidateLike> {
  projectId: string
  phase: number
  candidates: T[]
}

const REMINDER_MSG = "已等待 60 秒，请选择一个候选方案，或点击「跳过并接受推荐」"

export function CandidateSelector<T extends CandidateLike>({ projectId, phase, candidates }: Props<T>): JSX.Element {
  const visible = useMemo(() => candidates.slice(0, 3), [candidates])
  const sel = useCandidateSelection(
    visible,
    async (candidateId) => {
      await apiClient.post(`/api/v1/projects/${projectId}/preferences/confirm`, {
        phase, decisions: { candidate_id: candidateId, action: candidateId === visible.find(c => c.is_recommended)?.id ? "accept" : "select" },
      })
    },
    { onReminder: () => toast(REMINDER_MSG), reminderMs: 60_000 },
  )

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {visible.map((c) => (
          <CandidateCard
            key={c.id} candidate={c}
            isActive={sel.selectedId === c.id}
            onPreview={() => sel.preview(c.id)}
            onSelect={() => sel.select(c.id)}
          />
        ))}
      </div>
      <div className="flex gap-2">
        <button
          className="px-3 py-1 border rounded" disabled={sel.state !== "selected"}
          onClick={sel.confirm}
        >确认</button>
        <button className="px-3 py-1 border rounded" onClick={sel.skipAndAccept}>
          跳过并接受推荐
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: GREEN**

```bash
cd src/frontend && pnpm vitest run components/CandidateSelector.test.tsx 2>&1 | tail -10
```
Expected: 4 passed.

- [ ] **Step 9: Pytest wrapper**

Modify `tests/unit/frontend/test_spec_e_010.py` — 8 classes matching AC-1..AC-8 (map to vitest patterns as above).

- [ ] **Step 10: Run pytest**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_010.py -v 2>&1 | tail -12
```
Expected: 8 passed.

- [ ] **Step 11: Commit**

```bash
git add src/frontend/types/candidates.ts src/frontend/hooks/useCandidateSelection.ts src/frontend/components/CandidateCard.tsx src/frontend/components/CandidateSelector.tsx tests/unit/frontend/hooks/useCandidateSelection.test.tsx tests/unit/frontend/components/CandidateSelector.test.tsx tests/unit/frontend/test_spec_e_010.py
git commit -m "[SPEC-E-010] CandidateSelector: state machine + 60s reminder + skip-to-recommended"
```

---

## Task 8: Wave 3a Close-out

- [ ] **Step 1: Run full frontend test suite**

```bash
cd src/frontend && pnpm tsc 2>&1 | tail -5
cd src/frontend && pnpm vitest run 2>&1 | tail -20
```
Expected: tsc 0 errors; vitest all passing (approx 40+ tests across 12 files).

- [ ] **Step 2: Run full SPEC-E pytest suite**

```bash
python3 -m pytest tests/unit/frontend/test_spec_e_001.py tests/unit/frontend/test_spec_e_002.py tests/unit/frontend/test_spec_e_003.py tests/unit/frontend/test_spec_e_007.py tests/unit/frontend/test_spec_e_008.py tests/unit/frontend/test_spec_e_009.py tests/unit/frontend/test_spec_e_010.py tests/unit/frontend/test_spec_e_100.py -v 2>&1 | tail -30
```
Expected: all PASS (expected counts per task in earlier steps); total ≈ 40.

- [ ] **Step 3: Contract tests still green**

```bash
python3 -m pytest tests/contract/ -v 2>&1 | tail -10
```
Expected: unchanged from Wave 2 (0 failures).

- [ ] **Step 4: Dev server smoke**

```bash
cd src/frontend && pnpm dev 2>&1 &
sleep 5
curl -s http://localhost:3000/ -o /dev/null -w "%{http_code}"
echo ""
# expected: 200
kill %1 2>/dev/null || true
```
Expected: 200.

- [ ] **Step 5: Append PROGRESS.md entry**

Append to `PROGRESS.md`:

```markdown
## [SPEC-E-WAVE-3A] Frontend Shell V1 (E-001+100 merged, E-002/003/007/008/009/010)
- **Status**: DONE
- **Started**: 2026-04-17
- **Completed**: 2026-04-17
- **Branch**: feat/spec-e-wave-3a
- **Files Changed**: (see 8 task commits for full list)
- **Verification**:
  - `pnpm tsc` → 0 errors
  - `pnpm vitest run` → 40+ tests passing across 12 files
  - `pytest tests/unit/frontend/test_spec_e_{001,002,003,007,008,009,010,100}.py` → all PASS
  - `pytest tests/contract/` → unchanged (Wave 2 contracts still green)
- **Artifacts**:
  - Shell infra: apiClient, queryClient, Zustand store, useWebSocket, App, AppRouter
  - Pages: ProjectList, NewProject, WorkflowPage, ProjectRedirect
  - Components: ProjectCard, CreateProjectForm, PhaseNavigation, LoadingState, ErrorState,
    ArtifactStatusBadge, AgentActivityPanel, ActivityEventRow, CandidateSelector, CandidateCard,
    ErrorToast, ErrorModal, TechnicalDetails
  - Hooks: useProjects, useCreateProject, useProjectState, useArtifactStatus, useEventStream,
    useErrorHandler, useCandidateSelection
  - Utils: errorUxMap (8 codes + fallback)
  - Types: project, project_state, events, errors, candidates
  - Test pattern: pytest subprocess wrapper → vitest real tests
- **Decisions**:
  - Merged E-001 + E-100 into single task — E-100 explicitly extends E-001; building separately would throw away the plain ProjectCard.
  - Test contract: task cards say `pytest tests/unit/frontend/test_spec_e_NNN.py`, so we keep pytest as the AC verification layer and shell out to vitest for real component testing. Honors both contracts.
  - Deferred E-006 → replaced by E-102 ClaimWorkbench in Wave 3b (BDD explicitly supersedes DataVerificationPanel).
  - Deferred Playwright e2e from E-100 → vitest + MemoryRouter gives equivalent coverage; Playwright smoke to be added in Wave 3b once Settings page provides a stable login/nav anchor.
  - React Query + Zustand over Redux: minimal API surface, server-cache-as-primary, Zustand only for WS event buffer (naturally ephemeral).
  - React Router v6 (not v7): v7 renamed several APIs and prototype references assume v6 shape.
- **Notes**:
  - 14 SPEC-E cards remain for Wave 3b (E-004, E-005's 12 previews, E-101, E-102, E-103, E-104, E-105) and Wave 3c (E-011..E-015).
  - prototype/** untouched this wave (read-only; imports still forbidden per HARNESS §1.2).
```

- [ ] **Step 6: Mark task cards DONE**

For each completed card, update the one-liner status in its task card file. Use a single sed or Edit per file.

```bash
for c in E-001 E-002 E-003 E-007 E-008 E-009 E-010 E-100; do
  echo "Updating status for ${c}"
  # Update header/status line if present
done
```

(Manually open each card and add status: DONE under Metadata, or leave as-is if tracking is in PROGRESS.md only — HARNESS §9 says PROGRESS.md is append-only and per-card completion tracked here is acceptable.)

- [ ] **Step 7: Commit close-out**

```bash
git add PROGRESS.md tasks/SPEC-E/
git commit -m "[SPEC-E-WAVE-3A] PROGRESS entry + task card status updates (8 cards DONE)"
```

- [ ] **Step 8: Present finishing options**

After this task, invoke superpowers:finishing-a-development-branch for the 4-option flow (merge/PR/keep/discard).

---

## Self-Review Checklist (performed 2026-04-17)

### Spec coverage
- E-001 (SPEC-2.1): Task 1, all 5 ACs ✓
- E-100 (SPEC-E §E-BDD-1): Task 1 (merged), all 3 ACs ✓
- E-002 (SPEC-2.2): Task 2, all 5 ACs ✓
- E-003 (SPEC-2.3): Task 3, all 6 ACs ✓
- E-007 (SPEC-2.4): Task 4, all 5 ACs ✓
- E-008 (SPEC-11.4): Task 5, all 6 ACs ✓
- E-009 (SPEC-24.1): Task 6, all 7 ACs ✓
- E-010 (SPEC-25.1): Task 7, all 8 ACs ✓
- Shell infra (no card; prerequisite): Task 0 ✓

Explicit deferrals (out of Wave 3a): E-004, E-005 (12 sub-components), E-006 (superseded by E-102), E-011..E-015, E-101..E-105 — listed in spec §2 "Skipped in 3a" and in close-out notes.

### Placeholder scan
- No "TBD", "TODO", "fill in later" in steps.
- Every RED step has complete test code.
- Every GREEN step has complete implementation code or explicit file modification instruction.
- Every run step has exact command and expected output.

### Type consistency
- `ProjectListItem` = `ProjectInfo` (re-export) — used in ProjectCard, useProjects, ProjectList.
- `AgentEvent` defined in Task 0 store AND Task 5 types/events.ts — **consistency gap**. Resolution: Task 5's `types/events.ts` is the authoritative frontend type; Task 0 store imports from it. The store test (Task 0 Step 11) uses an inline-compatible shape that will validate against `AgentEvent` from `types/events.ts` once Task 5 lands. If subagent runs Task 0 first, they should create a minimal placeholder in `store/index.ts` using the inline interface, and Task 5 refactors it to import from `types/events.ts`.
- `CandidateLike` (Task 7) vs shared `Candidate` (src/shared/types/candidate.ts) — different shapes intentional. Shared is strict; frontend CandidateLike is generic over phase-specific candidate types. Selector accepts any.
- `ErrorUxEntry.tier` union: `"auto_handling" | "user_choice" | "user_action"` — used identically in errorUxMap and ErrorModal props.

### Gaps found and fixed inline
1. **Task 0 Step 11 store test imports AgentEvent from @frontend/store**; Task 5 exports from `types/events.ts`. Mitigated by note above: store owns its own minimal shape; Task 5's AgentEvent is the user-facing one. If subagents see a type conflict, they should align by having `store/index.ts` import from `types/events.ts` (circular-safe since types has no runtime).
2. **list_response.json fixture shape**: spec asserts the current fixture may be a single object. Task 1 Step 9 explicitly verifies and fixes to a 3-item array.
3. **Pytest wrapper requires pnpm in subprocess PATH**: CI is assumed to have pnpm; if a subagent runs locally without pnpm, Task 0 Step 2 install will fail first and block subsequent steps.
4. **AppRouter test coverage**: no standalone test; routes are exercised through page-level MemoryRouter tests. Accepted tradeoff — routing is trivial declaration, tested by page tests that rely on correct URL dispatch.
