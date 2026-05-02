// [SPEC-A-012] LogLine wire-format mirror (SPEC-13B).
//
// TS mirror of src/shared/logging/log_schema.py. Frontend log-aggregator
// callers and operator dashboards consume this contract; the Python
// module is the cross-language authority.

export type Service = "api" | "worker";

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

export interface LogLine {
  // Required (SPEC-13B AC-1)
  ts: string;            // ISO-8601 / RFC3339 UTC
  level: LogLevel;
  service: Service;
  event: string;

  // Optional (SPEC-13B AC-2)
  project_id?: string;
  phase?: number;
  agent?: string;
  duration_ms?: number;
  error_code?: string | null;
  extra?: Record<string, unknown>;
}

// SPEC-13B AC-6 -- per-level usage rules (matches LOG_LEVEL_USAGE in Python).
export const LOG_LEVEL_USAGE: Readonly<Record<LogLevel, string>> = {
  DEBUG: "Dev-only diagnostics (suppressed in production by default).",
  INFO: "Normal business events: task start/finish, phase advance, downgrade switch.",
  WARN: "Non-fatal anomalies: degradation events (capability_gap / source_fallback), cost warnings, retries.",
  ERROR: "Fatal exceptions: agent crash, DB error, uncaught exception.",
};
