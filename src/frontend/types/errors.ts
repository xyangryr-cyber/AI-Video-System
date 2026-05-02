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
