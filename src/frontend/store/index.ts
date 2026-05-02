import { create } from "zustand"
import type { AgentEvent } from "../types/events"

export type { AgentEvent }

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
