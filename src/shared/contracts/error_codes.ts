// [SPEC-13A] Business error codes — TypeScript mirror of
// src/shared/contracts/error_codes.py.
// Authority: docs/specs/SPEC-A-contracts.md SPEC-13A "Business Error Codes".
// 17 EVID_ error codes with HTTP status and default message mappings.

export const ERROR_CODES = {
  EVID_1001: "EVID_1001",
  EVID_1002: "EVID_1002",
  EVID_1003: "EVID_1003",
  EVID_2001: "EVID_2001",
  EVID_2002: "EVID_2002",
  EVID_2003: "EVID_2003",
  EVID_2004: "EVID_2004",
  EVID_2005: "EVID_2005",
  EVID_3001: "EVID_3001",
  EVID_3002: "EVID_3002",
  EVID_3003: "EVID_3003",
  EVID_3004: "EVID_3004",
  EVID_4001: "EVID_4001",
  EVID_4002: "EVID_4002",
  EVID_5001: "EVID_5001",
  EVID_5002: "EVID_5002",
  EVID_5003: "EVID_5003",
} as const;

export type ErrorCodeType = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

/** HTTP status code for each EVID error code. */
export const ERROR_CODE_HTTP_MAP: Record<ErrorCodeType, number> = {
  [ERROR_CODES.EVID_1001]: 400,
  [ERROR_CODES.EVID_1002]: 404,
  [ERROR_CODES.EVID_1003]: 409,
  [ERROR_CODES.EVID_2001]: 422,
  [ERROR_CODES.EVID_2002]: 409,
  [ERROR_CODES.EVID_2003]: 400,
  [ERROR_CODES.EVID_2004]: 400,
  [ERROR_CODES.EVID_2005]: 409,
  [ERROR_CODES.EVID_3001]: 500,
  [ERROR_CODES.EVID_3002]: 504,
  [ERROR_CODES.EVID_3003]: 400,
  [ERROR_CODES.EVID_3004]: 500,
  [ERROR_CODES.EVID_4001]: 404,
  [ERROR_CODES.EVID_4002]: 409,
  [ERROR_CODES.EVID_5001]: 503,
  [ERROR_CODES.EVID_5002]: 503,
  [ERROR_CODES.EVID_5003]: 500,
};

/** Default user-facing message for each EVID error code. */
export const ERROR_CODE_MESSAGE_MAP: Record<ErrorCodeType, string> = {
  [ERROR_CODES.EVID_1001]: "Description too short (min 10 chars)",
  [ERROR_CODES.EVID_1002]: "Project not found",
  [ERROR_CODES.EVID_1003]: "Project is not active",
  [ERROR_CODES.EVID_2001]: "Gate check failed",
  [ERROR_CODES.EVID_2002]: "Gate check already in progress",
  [ERROR_CODES.EVID_2003]: "Phase {N} cannot be skipped",
  [ERROR_CODES.EVID_2004]: "Cannot rollback to phase {N}",
  [ERROR_CODES.EVID_2005]: "Active tasks exist, cannot advance",
  [ERROR_CODES.EVID_3001]: "Agent {name} failed: {reason}",
  [ERROR_CODES.EVID_3002]: "Agent {name} timed out after {N}s",
  [ERROR_CODES.EVID_3003]: "Task {id} cannot be cancelled (status: {status})",
  [ERROR_CODES.EVID_3004]: "LLM call failed: {provider} {error}",
  [ERROR_CODES.EVID_4001]: "Artifact not found for phase {N}",
  [ERROR_CODES.EVID_4002]: "Artifact damaged: {path}",
  [ERROR_CODES.EVID_5001]: "System not ready: {check_name} failed",
  [ERROR_CODES.EVID_5002]: "Worker unavailable",
  [ERROR_CODES.EVID_5003]: "Database error",
};

export interface ErrorCodeInfo {
  code: ErrorCodeType;
  http_status: number;
  message: string;
}

/**
 * Look up error code metadata.
 * Throws if the code string is not a known EVID code.
 */
export function lookupEvid(code: string): ErrorCodeInfo {
  const httpStatus = ERROR_CODE_HTTP_MAP[code as ErrorCodeType];
  const message = ERROR_CODE_MESSAGE_MAP[code as ErrorCodeType];
  if (httpStatus === undefined || message === undefined) {
    throw new Error(`Unknown error code: ${code}`);
  }
  return { code: code as ErrorCodeType, http_status: httpStatus, message };
}
