// [SPEC-A-018] SPEC-13A v3.17 error code additions (TypeScript).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6.
//
// The 17 v3.15/v3.16 canonical EVID codes live in
// src/shared/constants/error_codes.ts (frozen). This file only declares the
// v3.17 friendly alias surface (render_failed / material_missing /
// material_unverified) + their HTTP-status mapping, mirrored from
// src/shared/constants/error_codes.py. We intentionally do NOT re-declare
// EVID_* string literals here: that would require widening
// tests/unit/contracts/test_error_codes.py::TestAC8NoMagicErrorStrings's
// whitelist, which is outside this task card's allowed_files.

// The 3 friendly alias names introduced by SPEC-13A v3.17. Each maps (via
// error_codes.py::ERROR_CODE_ALIASES) to a canonical EVID_* member of the
// Python ErrorCode enum; TS-side consumers use the alias string directly
// when emitting SPEC-13B log rows (see log_event_codes below).
export const ERROR_CODE_ALIASES_V317 = [
  "render_failed",
  "material_missing",
  "material_unverified",
] as const;

export type ErrorCodeAliasV317 = (typeof ERROR_CODE_ALIASES_V317)[number];

// HTTP status mapping for the 3 v3.17 aliases. Kept in lockstep with
// src/shared/constants/error_codes.py::HTTP_STATUS_BY_CODE entries for
// EVID_3005 / EVID_4003 / EVID_4004.
export const V317_ALIAS_HTTP_STATUS: Readonly<
  Record<ErrorCodeAliasV317, number>
> = {
  render_failed: 500, // EVID_3005 (agent domain)
  material_missing: 422, // EVID_4003 (artifact domain)
  material_unverified: 422, // EVID_4004 (artifact domain)
};

// Log-event constraint (SPEC-13B v3.17): the `event` field of P8
// render-fail / shot-block log rows MUST be one of these 3 aliases.
// Python counterpart: src/shared/constants/log_event_codes.py.
export const ALLOWED_LOG_EVENT_CODES: readonly ErrorCodeAliasV317[] =
  ERROR_CODE_ALIASES_V317;

export class InvalidLogEventError extends Error {
  constructor(name: string) {
    super(
      `Log event ${JSON.stringify(name)} is not in ALLOWED_LOG_EVENT_CODES. ` +
        `Expected one of ${JSON.stringify([...ALLOWED_LOG_EVENT_CODES].sort())} ` +
        `(SPEC-13B v3.17 / SPEC-A-018).`,
    );
    this.name = "InvalidLogEventError";
  }
}

export function validateLogEventCode(name: string): ErrorCodeAliasV317 {
  for (const code of ALLOWED_LOG_EVENT_CODES) {
    if (code === name) return code;
  }
  throw new InvalidLogEventError(name);
}
