export interface CandidateLike {
  id: string
  is_recommended: boolean
  preview_url?: string
  [k: string]: unknown
}

export type CandidateState = "idle" | "previewing" | "selected" | "confirmed"
