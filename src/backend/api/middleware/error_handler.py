"""[SPEC-13A] Global exception handler — maps exceptions to EVID_ error codes.

All EVID_ identifiers and messages are imported from the shared authority module
``src.shared.contracts.error_codes``.  No EVID_ string literal is defined here.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.shared.contracts.error_codes import (
    ERROR_CODE_HTTP_MAP,
    ERROR_CODE_MESSAGE_MAP,
    ErrorCode,
)

# ---------------------------------------------------------------------------
# Reverse lookup: HTTP status -> most-generic EVID_ code string
# ---------------------------------------------------------------------------
_HTTP_TO_CODE: dict[int, str] = {}

# Populate from the shared ERROR_CODE_HTTP_MAP (EVID_ -> HTTP).
# When multiple codes share the same HTTP status the *last* wins;
# we then hard-pin the ones we want to be the "canonical" generic.
for _code_str, _http_status in ERROR_CODE_HTTP_MAP.items():
    _HTTP_TO_CODE[_http_status] = _code_str

# Pin the canonical generic code for each HTTP status we handle explicitly.
_HTTP_TO_CODE[400] = ErrorCode.EVID_1001.value
_HTTP_TO_CODE[404] = ErrorCode.EVID_1002.value
_HTTP_TO_CODE[409] = ErrorCode.EVID_1003.value
_HTTP_TO_CODE[422] = ErrorCode.EVID_2001.value
_HTTP_TO_CODE[500] = ErrorCode.EVID_5003.value
_HTTP_TO_CODE[503] = ErrorCode.EVID_5001.value


def _make_error_body(status_code: int, detail: str = "") -> dict:
    """Build the ``{"error": {...}}`` envelope per SPEC-13A."""
    code = _HTTP_TO_CODE.get(status_code, ErrorCode.EVID_5003.value)
    message = detail or ERROR_CODE_MESSAGE_MAP.get(code, "Internal error")
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    """Register global HTTP-exception and catch-all handlers on *app*."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        body = _make_error_body(exc.status_code, exc.detail)
        body["error"]["details"] = {"path": str(request.url.path)}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Let HTTPException passthrough to its dedicated handler above.
        if isinstance(exc, HTTPException):
            raise exc
        body = _make_error_body(500)
        body["error"]["details"] = {
            "path": str(request.url.path),
            "exception": type(exc).__name__,
        }
        return JSONResponse(status_code=500, content=body)
