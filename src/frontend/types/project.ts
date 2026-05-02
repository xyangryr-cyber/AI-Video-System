// View model for project list items returned by GET /api/projects.
// Contains the fields needed for display, independent of the shared ProjectInfo contract.

export interface ProjectListItem {
  id: string
  project_id: string
  title: string
  category: string
  current_phase: number
  latest_reached_phase: number
  progress: number
  status: string
  updated_at: string
}

export function rollbackDelta(p: ProjectListItem): number {
  return p.latest_reached_phase - p.current_phase
}
