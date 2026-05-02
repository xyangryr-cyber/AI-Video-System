# Wave 3a Frontend Shell — Design Spec

**Date**: 2026-04-17
**Branch**: `feat/spec-e-wave-3a`
**Worktree**: `/Users/xyangryr/Desktop/硅基员工/AI-Video-System.wt-wave3a`

---

## 1. Goal

Build the Frontend V1 shell: list / create / recover / error / event / candidate flows — the minimum UI surface that lets a user see projects, create one, open it, and observe system activity. 12 phase-preview bodies, Settings page, Claim workbench, and audio master UI are **out of scope** (→ Wave 3b / 3c).

## 2. Scope — 8 Tasks

Of the 21 SPEC-E cards, Wave 3a covers **8 cards** (7 feature + 1 foundation). Remaining 14 → Wave 3b/3c.

| Wave 3a Task | Source Card(s) | Produces |
|---|---|---|
| **Task 0 — Shell Foundation** | (no card; pre-req) | Router, QueryClient, Zustand store, useWebSocket, apiClient, test wrapper pattern |
| **Task 1 — E-015 types** | — *(deferred; E-015 is audio-only, belongs to 3c)* | — |
| **Task 1 — ProjectList + ProjectCard** | E-001 + E-100 *(merged)* | `pages/ProjectList.tsx`, `components/ProjectCard.tsx`, `hooks/useProjects.ts`, rollback badge, auto-redirect to `latest_reached_phase` |
| **Task 2 — NewProject Wizard** | E-002 | `pages/NewProject.tsx`, `components/CreateProjectForm.tsx`, `hooks/useCreateProject.ts` |
| **Task 3 — State Recovery** | E-003 | `pages/WorkflowPage.tsx`, `hooks/useProjectState.ts`, `components/PhaseNavigation.tsx`, `components/LoadingState.tsx`, `components/ErrorState.tsx` |
| **Task 4 — ArtifactStatusBadge** | E-007 | `components/ArtifactStatusBadge.tsx`, `hooks/useArtifactStatus.ts` |
| **Task 5 — AgentActivityPanel** | E-008 | `components/AgentActivityPanel.tsx`, `components/ActivityEventRow.tsx`, `hooks/useEventStream.ts`, `types/events.ts` |
| **Task 6 — Error UX Map** | E-009 | `components/errors/ErrorToast.tsx`, `components/errors/ErrorModal.tsx`, `components/errors/TechnicalDetails.tsx`, `utils/errorUxMap.ts`, `hooks/useErrorHandler.ts`, `types/errors.ts` |
| **Task 7 — CandidateSelector** | E-010 | `components/CandidateSelector.tsx`, `components/CandidateCard.tsx`, `hooks/useCandidateSelection.ts`, `types/candidates.ts` |

**Merged rationale — E-001 + E-100**: E-100 explicitly "扩展 SPEC-2.1" of E-001 with `latest_reached_phase` badge + auto-redirect. Building E-001 first and then ripping it apart for E-100 = wasted work. Instead, implement ProjectCard with the final v3.16-BDD props shape from Task 1.

**Skipped in 3a**:
- E-004 Settings (4 tabs, large) → 3b
- E-005 Phase previews (12 components P0–P11) → 3b (one sub-task per phase)
- E-006 DataVerificationPanel → superseded by E-102 ClaimWorkbench (3b)
- E-011..E-015 Audio master + types → 3c
- E-101..E-105 BDD upgrades (except E-100 which is folded into Task 1) → 3b

## 3. Architecture

### 3.1 Stack (already aligned from Wave 0/1)

- **React 19** + **TypeScript 5.8** (strict)
- **Tailwind 4** (via `@tailwindcss/vite`)
- **Vite 6** (dev/build)
- **Vitest 2** + `@testing-library/react` 16 + `jsdom` (unit/integration tests)
- **MSW 2.6.6** (mock server, reuses Wave 0/1 setup)
- **lucide-react**, **motion** (existing)

### 3.2 New dependencies (Task 0)

| Package | Version | Purpose |
|---|---|---|
| `@tanstack/react-query` | `^5.x` | Server state / cache |
| `zustand` | `^5.x` | Client state (WS event buffer, UI state) |
| `react-router-dom` | `^6.x` | Routing (v7 breaks prototype patterns) |
| `dayjs` | `^1.11.x` | Relative time ("3 分钟前") |
| `sonner` | `^1.x` | Toast UI (error + 60s reminder) |
| `mock-socket` | `^9.x` | WebSocket mock for vitest |

### 3.3 Layer placement (HARNESS §2)

All new files follow the allowed pattern:

```
src/frontend/
├── pages/         Layer 7 — imports from Layer 0..6
├── components/    Layer 6
├── hooks/         Layer 6
├── types/         Layer 5
├── utils/         Layer 5
├── store/         Layer 5 — new; Zustand slices
├── api/           Layer 5 — new; apiClient + endpoints
├── lib/           Layer 5 — new; queryClient instance
└── mocks/         Layer 5 — existing MSW handlers
```

Cross-layer imports **from `src/shared/types/`** are allowed (Layer 5 ← Layer 0). Wave 3a imports the Pydantic-mirror TS types from Wave 2 directly — no re-declaration.

### 3.4 State architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Component (pages/components)                                │
│   useQuery(['projects'])           useProjects.ts           │
│   useQuery(['project', id])        useProjectState.ts       │
│   useMutation(createProject)       useCreateProject.ts      │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
       React Query cache             Zustand store
       (server state)                (WS buffer, UI state)
                  │                           ▲
                  │                           │ ws.onmessage → push event
                  ▼                           │
             apiClient ──► fetch ──► MSW ──► fixtures
                                              ▲
                                     useWebSocket.ts
                                     (mock-socket in test)
```

**Cache invalidation**: WS events update the Zustand event buffer AND call `queryClient.invalidateQueries` on affected keys. AC-5 of E-001 (6s refresh) is satisfied by this pattern.

### 3.5 Routing

```
/                                    → redirect to /projects
/projects                            → ProjectList
/projects/new                        → NewProject
/projects/:id                        → redirect to /projects/:id/phases/{latest_reached_phase}
/projects/:id/phases/:phase          → WorkflowPage (phase-scoped)
```

The `/projects/:id` → latest-phase redirect satisfies E-100 AC-2 via a `<Navigate>` element that reads `latest_reached_phase` from cached project state.

### 3.6 Test strategy

**Task cards mandate pytest for frontend verification**. We satisfy the contract via **pytest-wrapping-vitest**:

```python
# tests/unit/frontend/test_spec_e_001.py
import subprocess, pytest
FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"

def _vitest(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=verbose", "-t", pattern],
        cwd=FRONTEND_ROOT, capture_output=True, text=True, timeout=120
    )

class TestAC1RendersAllProjectFields:
    def test_renders_all_project_fields(self):
        r = _vitest("AC-1 renders all project fields")
        assert r.returncode == 0, r.stdout + r.stderr
```

- Real tests live in `tests/unit/frontend/*.test.tsx` (vitest).
- pytest placeholders in `tests/unit/frontend/test_spec_e_NNN.py` become **wrappers** that shell out to vitest with `-t "<test name pattern>"` and assert returncode 0.
- This keeps the task-card contract (pytest is the verification command) while doing the real work in the right runner.
- `subprocess` imports fail ≤ 2s → RED precondition. Missing `pnpm` raises; CI already has pnpm.

**Per-task test layout** (every TSX + hook gets both):

```
tests/unit/frontend/
├── pages/ProjectList.test.tsx             # vitest — real
├── components/ProjectCard.test.tsx        # vitest — real
├── hooks/useProjects.test.ts              # vitest — real
├── test_spec_e_001.py                     # pytest — wrapper (already exists as stub)
└── test_spec_e_100.py                     # pytest — wrapper (already exists as stub)
```

## 4. Data Flow — Key AC Examples

### 4.1 E-001 AC-5: updated_at refreshes within 6s of status change via WS

```
1. User opens /projects
2. useProjects() → useQuery(['projects']) → GET /api/v1/projects
   → MSW returns list_response.json → cache populated → ProjectList renders
3. WS connects via useWebSocket('/ws') → subscribes to project.* event types
4. Backend emits phase.advanced event (simulated in test by mock-socket send)
5. ws.onmessage → useEventStream buffers event in Zustand store
6. Effect in useProjects detects event type ∈ {phase.advanced, status.changed}
   → queryClient.invalidateQueries(['projects'])
7. React Query refetches → MSW returns updated list → UI re-renders
8. Test asserts: time between ws.send() and DOM update < 6000ms
```

### 4.2 E-100 AC-2: click card routes to latest_reached_phase

```
1. ProjectCard receives project prop with latest_reached_phase=5
2. onClick → navigate(`/projects/${id}`)
3. Route /projects/:id component:
   const state = useProjectState(id).data  // prefetched via React Query
   if (!state) return <LoadingState />
   return <Navigate to={`/projects/${id}/phases/${state.latest_reached_phase}`} />
4. URL becomes /projects/proj_001/phases/5 within one render
```

### 4.3 E-008 AC-4: 200ms DOM update from WS message

```
useEventStream.ts:
  ws.onmessage = (evt) => {
    performance.mark('ws:received')
    const event = JSON.parse(evt.data)
    store.getState().pushEvent(event)  // Zustand setState triggers React re-render
  }

AgentActivityPanel.tsx:
  useEffect(() => { performance.mark('dom:painted') }, [events.length])

Test measures window.performance.getEntriesByName delta < 200ms.
```

## 5. Component Contracts

### 5.1 ProjectCard (E-001 + E-100 merged)

```typescript
interface ProjectCardProps {
  project: {
    id: string
    title: string
    category: string
    current_phase: number          // P0..P11
    latest_reached_phase: number   // P0..P11
    progress: number               // 0..100
    status: string
    updated_at: string             // ISO 8601
  }
  onClick: (id: string) => void
}
```

- Progress bar: `progress / 100` width
- Relative time: `dayjs(updated_at).fromNow()` with zh-cn locale
- Rollback badge: `current_phase !== latest_reached_phase` → orange chip `回退 ${latest_reached_phase - current_phase} 阶段`
- Click: navigate(`/projects/${id}`) → router handles redirect

### 5.2 CandidateSelector (E-010)

```typescript
interface CandidateSelectorProps<T extends Candidate> {
  projectId: string
  phase: number                    // P4/P5/P6/P8/P9
  candidates: T[]                  // <= 3
  onConfirm: (candidateId: string) => void
  onSkip?: () => void
}

type CandidateState = 'idle' | 'previewing' | 'selected' | 'confirmed'
```

State machine:

```
idle ──(hover/click preview)──► previewing ──(click select)──► selected
  ▲                                 │                             │
  │                                 └──(click elsewhere)──────────┤
  │                                                               │
  └──(60s no interaction, fire once)                              │
                                                                  │
selected ──(click confirm)──► confirmed ──► POST /preferences/confirm
        ──(click "skip and accept")──► confirmed with is_recommended=true
```

### 5.3 ERROR_UX_MAP (E-009)

```typescript
// src/frontend/utils/errorUxMap.ts
export const ERROR_UX_MAP: Record<string, ErrorUxEntry> = {
  EVID_3002: { tier: 'auto_handling', component: 'toast',  actions: ['retry_auto'] },
  EVID_3004: { tier: 'auto_handling', component: 'toast',  actions: ['retry_auto', 'degrade'] },
  EVID_4001: { tier: 'user_choice',   component: 'modal',  actions: ['regenerate', 'skip_phase'] },
  EVID_4002: { tier: 'user_choice',   component: 'modal',  actions: ['regenerate', 'use_prev_version'] },
  EVID_2001: { tier: 'user_choice',   component: 'modal',  actions: ['fix_items', 'force_skip'] },
  EVID_5001: { tier: 'user_action',   component: 'modal',  actions: ['check_config', 'contact_admin'] },
  EVID_5002: { tier: 'user_action',   component: 'modal',  actions: ['restart_worker', 'check_logs'] },
  EVID_3001: { tier: 'user_action',   component: 'modal',  actions: ['retry_manual', 'export_logs'] },
}
// Unknown codes → { tier: 'user_action', component: 'modal', actions: ['contact_admin'] }
```

Zero LLM calls (AC-2) — pure object lookup.

## 6. File Budget (HARNESS §6)

All TSX ≤ 300 lines; all TS hooks ≤ 200 lines. If a component exceeds budget, split (e.g., ProjectList-page + ProjectList-grid).

Estimated line counts:
- `ProjectList.tsx` ~120
- `ProjectCard.tsx` ~90
- `NewProject.tsx` ~70, `CreateProjectForm.tsx` ~120
- `WorkflowPage.tsx` ~150, `useProjectState.ts` ~120
- `AgentActivityPanel.tsx` ~180, `useEventStream.ts` ~160
- `CandidateSelector.tsx` ~250, `useCandidateSelection.ts` ~150
- `ErrorModal.tsx` ~130, `ErrorToast.tsx` ~90, `errorUxMap.ts` ~80

## 7. Definition of Done

- All 7 feature tasks: vitest tests PASS + pytest wrappers PASS
- `pnpm tsc` (in src/frontend) → 0 errors
- `pnpm build` (in src/frontend) → clean
- `pnpm dev` smoke: list page shows 3 fixture projects; click one → workflow page loads at latest_reached_phase; rollback badge visible when applicable
- `pytest tests/unit/frontend/ -v` → 0 failures, 0 skips for Wave 3a cards (E-001/002/003/007/008/009/010 + E-100)
- `pytest tests/contract/test_frontend_types_match_schemas.py` → still PASS (unchanged from Wave 2)
- PROGRESS.md Wave 3a entry with decisions + commit list
- All 14 task cards remaining map to Wave 3b/3c plans (explicit)

## 8. Non-Goals

- Wave 3a does **not** hit a real backend. All data via MSW + fixtures.
- No Playwright e2e (`E-100 AC-2` card requests Playwright; we satisfy via vitest + React Router test harness and document the deferral — Playwright wired in Wave 3b after Settings page exists to provide authenticated smoke target).
- No production CSS purging strategy — Tailwind v4 JIT is sufficient for dev.
- No accessibility audit beyond what's in component ACs (E-BDD-6 has explicit a11y and is in Wave 3b).

## 9. Risks

1. **React Router v6 vs v7** — v7 is stable but renames APIs. Pin `react-router-dom@^6.28` to stay on documented v6.
2. **mock-socket + MSW coexistence** — MSW handles HTTP, mock-socket handles WS. No conflict, both documented in vitest setup.
3. **Test flakiness on timers (60s CandidateSelector reminder, 200ms AgentActivityPanel)** — use `vi.useFakeTimers()` for the 60s test; use `Performance.now()` with fake clock for the 200ms.
4. **pnpm lockfile bloat** — 5 new deps; lockfile should grow predictably. Commit lockfile.

## 10. Post-Wave-3a Handoffs

- **Wave 3b plan**: E-004, E-005 (one sub-task per phase), E-101, E-102 (replaces E-006), E-103, E-104, E-105 — estimated 18–22 tasks.
- **Wave 3c plan**: E-011, E-012, E-013, E-014, E-015 — estimated 6–8 tasks.
- **Follow-on Playwright**: add `tests/e2e/project_list_autoopen.spec.ts` in Wave 3b once more pages exist to anchor the smoke.
