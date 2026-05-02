// [SPEC-A-011] EVID_* error code registry (SPEC-13A).
// Authority: docs/specs/SPEC-A-contracts.md SPEC-13A.
//
// Keep in lockstep with src/shared/constants/error_codes.py.
// No `EVID_xxxx` string literals may appear outside this module
// (enforced by tests/unit/contracts/test_error_codes.py::TestAC8).

export const ERROR_CODES = [
  // EVID_1xxx -- project operations
  "EVID_1001",
  "EVID_1002",
  "EVID_1003",
  // EVID_2xxx -- workflow / gatekeeper
  "EVID_2001",
  "EVID_2002",
  "EVID_2003",
  "EVID_2004",
  "EVID_2005",
  // EVID_3xxx -- agent / task
  "EVID_3001",
  "EVID_3002",
  "EVID_3003",
  "EVID_3004",
  // EVID_4xxx -- artifact / storage
  "EVID_4001",
  "EVID_4002",
  // EVID_5xxx -- system / infrastructure
  "EVID_5001",
  "EVID_5002",
  "EVID_5003",
] as const;

export type ErrorCode = (typeof ERROR_CODES)[number];

export type ErrorDomain =
  | "project"
  | "workflow"
  | "agent"
  | "artifact"
  | "system";

export const HTTP_STATUS_BY_CODE: Readonly<Record<ErrorCode, number>> = {
  EVID_1001: 400,
  EVID_1002: 404,
  EVID_1003: 409,
  EVID_2001: 422,
  EVID_2002: 409,
  EVID_2003: 400,
  EVID_2004: 400,
  EVID_2005: 409,
  EVID_3001: 500,
  EVID_3002: 504,
  EVID_3003: 400,
  EVID_3004: 500,
  EVID_4001: 404,
  EVID_4002: 409,
  EVID_5001: 503,
  EVID_5002: 503,
  EVID_5003: 500,
};

export const MESSAGE_BY_CODE: Readonly<Record<ErrorCode, string>> = {
  EVID_1001: "Description too short (min 10 chars)",
  EVID_1002: "Project not found",
  EVID_1003: "Project is not active",
  EVID_2001: "Gate check failed",
  EVID_2002: "Gate check already in progress",
  EVID_2003: "Phase {N} cannot be skipped",
  EVID_2004: "Cannot rollback to phase {N}",
  EVID_2005: "Active tasks exist, cannot advance",
  EVID_3001: "Agent {name} failed: {reason}",
  EVID_3002: "Agent {name} timed out after {N}s",
  EVID_3003: "Task {id} cannot be cancelled (status: {status})",
  EVID_3004: "LLM call failed: {provider} {error}",
  EVID_4001: "Artifact not found for phase {N}",
  EVID_4002: "Artifact damaged: {path}",
  EVID_5001: "System not ready: {check_name} failed",
  EVID_5002: "Worker unavailable",
  EVID_5003: "Database error",
};

export const DOMAIN_BY_CODE: Readonly<Record<ErrorCode, ErrorDomain>> = {
  EVID_1001: "project",
  EVID_1002: "project",
  EVID_1003: "project",
  EVID_2001: "workflow",
  EVID_2002: "workflow",
  EVID_2003: "workflow",
  EVID_2004: "workflow",
  EVID_2005: "workflow",
  EVID_3001: "agent",
  EVID_3002: "agent",
  EVID_3003: "agent",
  EVID_3004: "agent",
  EVID_4001: "artifact",
  EVID_4002: "artifact",
  EVID_5001: "system",
  EVID_5002: "system",
  EVID_5003: "system",
};

// Maps human-readable BDD/UX scenario names onto the 17 canonical EVID codes.
// Keep in lockstep with src/shared/constants/error_codes.py.
export const ERROR_CODE_ALIASES: Readonly<Record<string, ErrorCode>> = {
  tts_api_timeout: "EVID_3002",
  financial_data_unavailable: "EVID_4001",
  worker_crash_max_retries: "EVID_5002",
};

export function resolveErrorCode(name: string): ErrorCode {
  for (const code of ERROR_CODES) {
    if (code === name) return code;
  }
  const resolved = ERROR_CODE_ALIASES[name];
  if (resolved === undefined) {
    throw new Error(
      "Unknown error code or alias: " +
        JSON.stringify(name) +
        ". Expected an ErrorCode value or one of " +
        JSON.stringify(Object.keys(ERROR_CODE_ALIASES).sort()),
    );
  }
  return resolved;
}
