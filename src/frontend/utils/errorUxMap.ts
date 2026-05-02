import type { ErrorUxEntry } from "../types/errors"

export const ERROR_UX_MAP: Record<string, ErrorUxEntry> = {
  EVID_3002: { tier: "auto_handling", component: "toast", actions: ["retry_auto"] },
  EVID_3004: { tier: "auto_handling", component: "toast", actions: ["retry_auto", "degrade"] },
  EVID_4001: { tier: "user_choice",   component: "modal", actions: ["regenerate", "manual_input", "skip"] },
  EVID_4002: { tier: "user_choice",   component: "modal", actions: ["regenerate", "use_prev_version"] },
  EVID_2001: { tier: "user_choice",   component: "modal", actions: ["fix_items", "force_skip"] },
  EVID_5001: { tier: "user_action",   component: "modal", actions: ["check_config", "contact_admin", "retry"] },
  EVID_5002: { tier: "user_action",   component: "modal", actions: ["restart_worker", "check_logs", "retry"] },
  EVID_3001: { tier: "user_action",   component: "modal", actions: ["export_logs", "retry", "go_back"] },
}

const FALLBACK: ErrorUxEntry = {
  tier: "user_action", component: "modal", actions: ["contact_admin"],
}

export function lookupErrorUx(code: string): ErrorUxEntry {
  return ERROR_UX_MAP[code] ?? FALLBACK
}
