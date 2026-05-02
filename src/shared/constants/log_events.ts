// [SPEC-A-012] Special log event names (SPEC-13B).
//
// TS mirror of src/shared/constants/log_events.py. Keep field-by-field
// parity -- the Python module is the cross-language authority.

export const ROUTER_FALLBACK = "router_fallback" as const;
export const CAPABILITY_GAP = "capability_gap" as const;
export const SOURCE_FALLBACK = "source_fallback" as const;
export const COST_WARNING = "cost_warning" as const;
export const LEAK_SCAN_HIT = "leak_scan_hit" as const;

export const SPECIAL_EVENT_NAMES: ReadonlySet<string> = new Set([
  ROUTER_FALLBACK,
  CAPABILITY_GAP,
  SOURCE_FALLBACK,
  COST_WARNING,
  LEAK_SCAN_HIT,
]);

export const SOURCE_FALLBACK_REQUIRED_EXTRAS: ReadonlySet<string> = new Set([
  "source_attempted",
  "reason_failed",
  "source_used",
]);

export type SpecialEventName =
  | typeof ROUTER_FALLBACK
  | typeof CAPABILITY_GAP
  | typeof SOURCE_FALLBACK
  | typeof COST_WARNING
  | typeof LEAK_SCAN_HIT;
