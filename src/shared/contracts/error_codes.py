"""[SPEC-13A] Business error codes and HTTP/message mappings.

Authority: docs/specs/SPEC-A-contracts.md SPEC-13A "Business Error Codes".

Defines 17 EVID_ error codes grouped by domain:
  EVID_1xxx — Input / project validation
  EVID_2xxx — Gate / workflow
  EVID_3xxx — Agent / LLM
  EVID_4xxx — Artifact
  EVID_5xxx — System

Exports:
  ErrorCode            — Enum of all 17 error codes (values are the string ident).
  ERROR_CODE_HTTP_MAP  — Mapping from code string -> HTTP status (int).
  ERROR_CODE_MESSAGE_MAP — Mapping from code string -> default user message (str).
  lookup_evid(code)    — Return {"code":..., "http_status":..., "message":...}
                         for a given code string, or raise KeyError.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


class ErrorCode(str, Enum):
    """Business error codes per SPEC-13A."""

    EVID_1001 = "EVID_1001"
    EVID_1002 = "EVID_1002"
    EVID_1003 = "EVID_1003"
    EVID_2001 = "EVID_2001"
    EVID_2002 = "EVID_2002"
    EVID_2003 = "EVID_2003"
    EVID_2004 = "EVID_2004"
    EVID_2005 = "EVID_2005"
    EVID_3001 = "EVID_3001"
    EVID_3002 = "EVID_3002"
    EVID_3003 = "EVID_3003"
    EVID_3004 = "EVID_3004"
    EVID_4001 = "EVID_4001"
    EVID_4002 = "EVID_4002"
    EVID_5001 = "EVID_5001"
    EVID_5002 = "EVID_5002"
    EVID_5003 = "EVID_5003"


ERROR_CODE_HTTP_MAP: Dict[str, int] = {
    ErrorCode.EVID_1001.value: 400,
    ErrorCode.EVID_1002.value: 404,
    ErrorCode.EVID_1003.value: 409,
    ErrorCode.EVID_2001.value: 422,
    ErrorCode.EVID_2002.value: 409,
    ErrorCode.EVID_2003.value: 400,
    ErrorCode.EVID_2004.value: 400,
    ErrorCode.EVID_2005.value: 409,
    ErrorCode.EVID_3001.value: 500,
    ErrorCode.EVID_3002.value: 504,
    ErrorCode.EVID_3003.value: 400,
    ErrorCode.EVID_3004.value: 500,
    ErrorCode.EVID_4001.value: 404,
    ErrorCode.EVID_4002.value: 409,
    ErrorCode.EVID_5001.value: 503,
    ErrorCode.EVID_5002.value: 503,
    ErrorCode.EVID_5003.value: 500,
}


ERROR_CODE_MESSAGE_MAP: Dict[str, str] = {
    ErrorCode.EVID_1001.value: "Description too short (min 10 chars)",
    ErrorCode.EVID_1002.value: "Project not found",
    ErrorCode.EVID_1003.value: "Project is not active",
    ErrorCode.EVID_2001.value: "Gate check failed",
    ErrorCode.EVID_2002.value: "Gate check already in progress",
    ErrorCode.EVID_2003.value: "Phase {N} cannot be skipped",
    ErrorCode.EVID_2004.value: "Cannot rollback to phase {N}",
    ErrorCode.EVID_2005.value: "Active tasks exist, cannot advance",
    ErrorCode.EVID_3001.value: "Agent {name} failed: {reason}",
    ErrorCode.EVID_3002.value: "Agent {name} timed out after {N}s",
    ErrorCode.EVID_3003.value: "Task {id} cannot be cancelled (status: {status})",
    ErrorCode.EVID_3004.value: "LLM call failed: {provider} {error}",
    ErrorCode.EVID_4001.value: "Artifact not found for phase {N}",
    ErrorCode.EVID_4002.value: "Artifact damaged: {path}",
    ErrorCode.EVID_5001.value: "System not ready: {check_name} failed",
    ErrorCode.EVID_5002.value: "Worker unavailable",
    ErrorCode.EVID_5003.value: "Database error",
}


def lookup_evid(code: str) -> dict:
    """Look up error code metadata.

    Args:
        code: Error code string, e.g. "EVID_1001".

    Returns:
        dict with keys "code", "http_status", "message".

    Raises:
        KeyError: If the code is not known.
    """
    if code not in ERROR_CODE_HTTP_MAP:
        raise KeyError(f"Unknown error code: {code}")
    return {
        "code": code,
        "http_status": ERROR_CODE_HTTP_MAP[code],
        "message": ERROR_CODE_MESSAGE_MAP[code],
    }


__all__ = [
    "ErrorCode",
    "ERROR_CODE_HTTP_MAP",
    "ERROR_CODE_MESSAGE_MAP",
    "lookup_evid",
]
