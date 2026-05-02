// [SPEC-A-011] Unified API error response types (SPEC-13A).
// Authority: docs/specs/SPEC-A-contracts.md SPEC-13A.
//
// Keep in lockstep with src/shared/schemas/error_response.py.

import type { ErrorCode } from "../constants/error_codes";

// Inner body of the unified error response envelope.
//   - code: an `EVID_xxxx` identifier from ERROR_CODES.
//   - message: human-readable description (template placeholders may be
//     substituted with concrete values before send).
//   - details: optional machine-readable context; for EVID_2001 this MUST
//     be a `GateFailureDetails`-shaped object.
export interface ErrorBody<D = Record<string, unknown>> {
  code: ErrorCode;
  message: string;
  details?: D;
}

// Top-level error envelope: `{error: {code, message, details?}}`.
export interface ErrorResponse<D = Record<string, unknown>> {
  error: ErrorBody<D>;
}

// A single failed gatekeeper check with a human-readable reason.
export interface FailedGateCheck {
  check: string;
  reason: string;
}

// `details` payload attached to EVID_2001 (Gate check failed).
//
// Gate evaluation does NOT short-circuit on the first failure: all declared
// checks are evaluated and every outcome is recorded here. `failed_checks`
// lists every check that did not pass (with its reason), and `passed_checks`
// lists every check that did pass. Together they expose the full gate
// evaluation so the frontend can render a complete fix list to the user
// without another round-trip.
export interface GateFailureDetails {
  failed_checks: FailedGateCheck[];
  passed_checks: string[];
}

// Convenience alias for a gate-failure response.
export type GateFailureResponse = ErrorResponse<GateFailureDetails>;
