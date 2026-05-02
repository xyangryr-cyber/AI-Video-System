export { EVENT_TYPES, type EventType } from "@shared/contracts/event_types";

export interface AgentEvent {
  id: string
  type: string
  project_id: string
  timestamp: string
  payload: { agent_name?: string; action?: string; result?: string; progress?: string; [k: string]: unknown }
}
