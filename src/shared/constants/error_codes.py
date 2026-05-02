"""[SPEC-A-011 + SPEC-A-018] EVID_* error code registry (SPEC-13A).

Authority:
  - docs/specs/SPEC-A-contracts.md SPEC-13A (the 17 v3.15/v3.16 codes).
  - docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6
    (the 3 v3.17 additions: EVID_3005 render_failed / EVID_4003
    material_missing / EVID_4004 material_unverified).

Single source of truth for the 20 HTTP error codes used by the API layer.
Every backend error response MUST reference one of these codes -- no magic
string literals of the form ``EVID_xxxx`` may appear outside this module
(enforced by tests/unit/contracts/test_error_codes.py::TestAC8).

Domain prefixes (SPEC-13A):
  - EVID_1xxx: project operations
  - EVID_2xxx: workflow / gatekeeper
  - EVID_3xxx: agent / task
  - EVID_4xxx: artifact / storage
  - EVID_5xxx: system / infrastructure

Allowed HTTP statuses: 400, 404, 409, 422, 500, 503, 504.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


class ErrorCode(str, Enum):
    """The 17 canonical HTTP error codes (order = SPEC-13A table)."""

    # EVID_1xxx -- project operations
    EVID_1001 = "EVID_1001"
    EVID_1002 = "EVID_1002"
    EVID_1003 = "EVID_1003"
    # EVID_2xxx -- workflow / gatekeeper
    EVID_2001 = "EVID_2001"
    EVID_2002 = "EVID_2002"
    EVID_2003 = "EVID_2003"
    EVID_2004 = "EVID_2004"
    EVID_2005 = "EVID_2005"
    # EVID_3xxx -- agent / task
    EVID_3001 = "EVID_3001"
    EVID_3002 = "EVID_3002"
    EVID_3003 = "EVID_3003"
    EVID_3004 = "EVID_3004"
    # EVID_4xxx -- artifact / storage
    EVID_4001 = "EVID_4001"
    EVID_4002 = "EVID_4002"
    # EVID_5xxx -- system / infrastructure
    EVID_5001 = "EVID_5001"
    EVID_5002 = "EVID_5002"
    EVID_5003 = "EVID_5003"
    # -- v3.17 additions (SPEC-A-018, PRD-DELTA-08 / TECH-DELTA-07) --
    EVID_3005 = "EVID_3005"  # render_failed     (HTTP 500, agent domain)
    EVID_4003 = "EVID_4003"  # material_missing  (HTTP 422, artifact domain)
    EVID_4004 = "EVID_4004"  # material_unverified (HTTP 422, artifact domain)


class ErrorDomain(str, Enum):
    """Semantic domain groupings used by SPEC-13A."""

    PROJECT = "project"
    WORKFLOW = "workflow"
    AGENT = "agent"
    ARTIFACT = "artifact"
    SYSTEM = "system"


HTTP_STATUS_BY_CODE: Final[dict[ErrorCode, int]] = {
    ErrorCode.EVID_1001: 400,
    ErrorCode.EVID_1002: 404,
    ErrorCode.EVID_1003: 409,
    ErrorCode.EVID_2001: 422,
    ErrorCode.EVID_2002: 409,
    ErrorCode.EVID_2003: 400,
    ErrorCode.EVID_2004: 400,
    ErrorCode.EVID_2005: 409,
    ErrorCode.EVID_3001: 500,
    ErrorCode.EVID_3002: 504,
    ErrorCode.EVID_3003: 400,
    ErrorCode.EVID_3004: 500,
    ErrorCode.EVID_4001: 404,
    ErrorCode.EVID_4002: 409,
    ErrorCode.EVID_5001: 503,
    ErrorCode.EVID_5002: 503,
    ErrorCode.EVID_5003: 500,
    # v3.17 additions (SPEC-A-018)
    ErrorCode.EVID_3005: 500,
    ErrorCode.EVID_4003: 422,
    ErrorCode.EVID_4004: 422,
}


MESSAGE_BY_CODE: Final[dict[ErrorCode, str]] = {
    ErrorCode.EVID_1001: "Description too short (min 10 chars)",
    ErrorCode.EVID_1002: "Project not found",
    ErrorCode.EVID_1003: "Project is not active",
    ErrorCode.EVID_2001: "Gate check failed",
    ErrorCode.EVID_2002: "Gate check already in progress",
    ErrorCode.EVID_2003: "Phase {N} cannot be skipped",
    ErrorCode.EVID_2004: "Cannot rollback to phase {N}",
    ErrorCode.EVID_2005: "Active tasks exist, cannot advance",
    ErrorCode.EVID_3001: "Agent {name} failed: {reason}",
    ErrorCode.EVID_3002: "Agent {name} timed out after {N}s",
    ErrorCode.EVID_3003: "Task {id} cannot be cancelled (status: {status})",
    ErrorCode.EVID_3004: "LLM call failed: {provider} {error}",
    ErrorCode.EVID_4001: "Artifact not found for phase {N}",
    ErrorCode.EVID_4002: "Artifact damaged: {path}",
    ErrorCode.EVID_5001: "System not ready: {check_name} failed",
    ErrorCode.EVID_5002: "Worker unavailable",
    ErrorCode.EVID_5003: "Database error",
    # v3.17 additions (SPEC-A-018)
    ErrorCode.EVID_3005: "Render failed: {reason}",
    ErrorCode.EVID_4003: "Required material {material_id} is missing",
    ErrorCode.EVID_4004: "Material {material_id} is not yet verified",
}


DOMAIN_BY_CODE: Final[dict[ErrorCode, ErrorDomain]] = {
    ErrorCode.EVID_1001: ErrorDomain.PROJECT,
    ErrorCode.EVID_1002: ErrorDomain.PROJECT,
    ErrorCode.EVID_1003: ErrorDomain.PROJECT,
    ErrorCode.EVID_2001: ErrorDomain.WORKFLOW,
    ErrorCode.EVID_2002: ErrorDomain.WORKFLOW,
    ErrorCode.EVID_2003: ErrorDomain.WORKFLOW,
    ErrorCode.EVID_2004: ErrorDomain.WORKFLOW,
    ErrorCode.EVID_2005: ErrorDomain.WORKFLOW,
    ErrorCode.EVID_3001: ErrorDomain.AGENT,
    ErrorCode.EVID_3002: ErrorDomain.AGENT,
    ErrorCode.EVID_3003: ErrorDomain.AGENT,
    ErrorCode.EVID_3004: ErrorDomain.AGENT,
    ErrorCode.EVID_4001: ErrorDomain.ARTIFACT,
    ErrorCode.EVID_4002: ErrorDomain.ARTIFACT,
    ErrorCode.EVID_5001: ErrorDomain.SYSTEM,
    ErrorCode.EVID_5002: ErrorDomain.SYSTEM,
    ErrorCode.EVID_5003: ErrorDomain.SYSTEM,
    # v3.17 additions (SPEC-A-018). Render failure is categorised under AGENT
    # because the render pipeline is an agent worker (RemotionRenderAgent);
    # material_{missing,unverified} land in ARTIFACT since they describe
    # missing/untrusted upstream artifact references (MaterialManifest).
    ErrorCode.EVID_3005: ErrorDomain.AGENT,
    ErrorCode.EVID_4003: ErrorDomain.ARTIFACT,
    ErrorCode.EVID_4004: ErrorDomain.ARTIFACT,
}


ERROR_CODE_ALIASES: Final[dict[str, ErrorCode]] = {
    # Maps human-readable BDD/UX scenario names onto the 17 canonical EVID
    # codes. Keep in lockstep with src/shared/constants/error_codes.ts.
    # Rationale: BDD @error_ux scenarios reference friendly names so the
    # feature files stay readable for PMs; the contract boundary owns the
    # mapping so no magic strings leak into backend/frontend code.
    "tts_api_timeout": ErrorCode.EVID_3002,
    "financial_data_unavailable": ErrorCode.EVID_4001,
    "worker_crash_max_retries": ErrorCode.EVID_5002,
    # v3.17 additions (SPEC-A-018 / PRD-DELTA-08). These three aliases are
    # also exported via src/shared/constants/log_event_codes.py as the
    # constrained `event` field for P8 render-fail / shot-block log rows.
    "render_failed": ErrorCode.EVID_3005,
    "material_missing": ErrorCode.EVID_4003,
    "material_unverified": ErrorCode.EVID_4004,
}


def resolve_error_code(name: str) -> ErrorCode:
    """Resolve a friendly alias or canonical EVID string to an ``ErrorCode``.

    Canonical codes (``EVID_3002``) pass through as themselves; known aliases
    (``tts_api_timeout``) resolve via ``ERROR_CODE_ALIASES``. Unknown names
    raise ``KeyError`` so callers must handle explicitly -- no silent fallbacks.
    """
    try:
        return ErrorCode(name)
    except ValueError:
        pass
    try:
        return ERROR_CODE_ALIASES[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown error code or alias: {name!r}. "
            f"Expected an ErrorCode value or one of {sorted(ERROR_CODE_ALIASES)}"
        ) from exc


__all__ = [
    "DOMAIN_BY_CODE",
    "ERROR_CODE_ALIASES",
    "ErrorCode",
    "ErrorDomain",
    "HTTP_STATUS_BY_CODE",
    "MESSAGE_BY_CODE",
    "resolve_error_code",
]
