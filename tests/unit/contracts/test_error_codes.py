"""Tests for [SPEC-A-011] HTTP Error Code System (SPEC-13A).

Authority: docs/specs/SPEC-A-contracts.md SPEC-13A.

Covers AC-1 .. AC-8 per tasks/SPEC-A/A-011-http-error-codes.md.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest
from pydantic import ValidationError


EXPECTED_ERROR_CODES: dict[str, tuple[int, str]] = {
    # EVID_1xxx -- project operations
    "EVID_1001": (400, "Description too short (min 10 chars)"),
    "EVID_1002": (404, "Project not found"),
    "EVID_1003": (409, "Project is not active"),
    # EVID_2xxx -- workflow / gatekeeper
    "EVID_2001": (422, "Gate check failed"),
    "EVID_2002": (409, "Gate check already in progress"),
    "EVID_2003": (400, "Phase {N} cannot be skipped"),
    "EVID_2004": (400, "Cannot rollback to phase {N}"),
    "EVID_2005": (409, "Active tasks exist, cannot advance"),
    # EVID_3xxx -- agent / task
    "EVID_3001": (500, "Agent {name} failed: {reason}"),
    "EVID_3002": (504, "Agent {name} timed out after {N}s"),
    "EVID_3003": (400, "Task {id} cannot be cancelled (status: {status})"),
    "EVID_3004": (500, "LLM call failed: {provider} {error}"),
    # EVID_4xxx -- artifact / storage
    "EVID_4001": (404, "Artifact not found for phase {N}"),
    "EVID_4002": (409, "Artifact damaged: {path}"),
    # EVID_5xxx -- system / infrastructure
    "EVID_5001": (503, "System not ready: {check_name} failed"),
    "EVID_5002": (503, "Worker unavailable"),
    "EVID_5003": (500, "Database error"),
}


class TestAC1ErrorResponseSchema:
    """AC-1: Error response schema: `{error: {code, message, details?}}`."""

    def test_error_response_schema(self):
        from src.shared.schemas.error_response import ErrorBody, ErrorResponse

        outer_fields = set(ErrorResponse.model_fields.keys())
        assert outer_fields == {"error"}, (
            f"ErrorResponse must wrap a single `error` field, got {outer_fields}"
        )

        inner_fields = set(ErrorBody.model_fields.keys())
        assert inner_fields == {"code", "message", "details"}, (
            f"ErrorBody must have exactly "
            f"{{code, message, details}}, got {inner_fields}"
        )
        assert ErrorBody.model_fields["details"].is_required() is False, (
            "details must be optional"
        )

        resp = ErrorResponse(
            error=ErrorBody(
                code="EVID_1002",
                message="Project not found",
            )
        )
        assert resp.error.code == "EVID_1002"
        assert resp.error.details is None

        resp_with_details = ErrorResponse(
            error=ErrorBody(
                code="EVID_2001",
                message="Gate check failed",
                details={"failed_checks": [], "passed_checks": []},
            )
        )
        assert resp_with_details.error.details == {
            "failed_checks": [],
            "passed_checks": [],
        }


class TestAC2Exactly17ErrorCodes:
    """AC-2: the 17 baseline EVID error codes are defined as constants.

    SPEC-A-018 (v3.17) added render_failed / material_missing /
    material_unverified. This test enforces that the baseline 17 remain
    in the enum; v3.17 additions are covered by tests/unit/contracts/
    test_error_codes_v317.py.
    """

    def test_exactly_17_error_codes(self):
        from src.shared.constants.error_codes import ErrorCode

        values = {e.value for e in ErrorCode}
        baseline = set(EXPECTED_ERROR_CODES.keys())
        missing = baseline - values
        assert not missing, f"Baseline ErrorCode members dropped: {sorted(missing)}"


class TestAC3ErrorCodeHttpStatusMapping:
    """AC-3: Each error code maps to correct HTTP status (400/404/409/422/500/503/504)."""

    def test_error_code_http_status_mapping(self):
        from src.shared.constants.error_codes import (
            ErrorCode,
            HTTP_STATUS_BY_CODE,
        )

        # AC-3 is the baseline-17 invariance check. SPEC-A-018 adds more
        # codes; their HTTP status assertions live in
        # tests/unit/contracts/test_error_codes_v317.py.
        allowed_statuses = {400, 404, 409, 422, 500, 503, 504}
        for code_value, (expected_status, _) in EXPECTED_ERROR_CODES.items():
            code = ErrorCode(code_value)
            actual_status = HTTP_STATUS_BY_CODE[code]
            assert actual_status == expected_status, (
                f"{code.value}: expected HTTP {expected_status}, got {actual_status}"
            )
            assert actual_status in allowed_statuses, (
                f"{code.value}: HTTP {actual_status} not in allowed set {allowed_statuses}"
            )


class TestAC4ErrorCodeDomainPrefixes:
    """AC-4: Domain prefixes 1xxx=project, 2xxx=workflow, 3xxx=agent, 4xxx=artifact, 5xxx=system."""

    def test_error_code_domain_prefixes(self):
        from src.shared.constants.error_codes import (
            ErrorCode,
            ErrorDomain,
            DOMAIN_BY_CODE,
        )

        prefix_to_domain = {
            "1": ErrorDomain.PROJECT,
            "2": ErrorDomain.WORKFLOW,
            "3": ErrorDomain.AGENT,
            "4": ErrorDomain.ARTIFACT,
            "5": ErrorDomain.SYSTEM,
        }
        for code in ErrorCode:
            digits = code.value.removeprefix("EVID_")
            prefix = digits[0]
            assert prefix in prefix_to_domain, (
                f"{code.value}: unrecognised prefix digit {prefix!r}"
            )
            expected_domain = prefix_to_domain[prefix]
            assert DOMAIN_BY_CODE[code] is expected_domain, (
                f"{code.value}: domain should be {expected_domain}, "
                f"got {DOMAIN_BY_CODE[code]}"
            )


class TestAC5Evid1001Message:
    """AC-5: EVID_1001 message is exactly 'Description too short (min 10 chars)'."""

    def test_evid_1001_message(self):
        from src.shared.constants.error_codes import (
            ErrorCode,
            HTTP_STATUS_BY_CODE,
            MESSAGE_BY_CODE,
        )

        assert ErrorCode.EVID_1001.value == "EVID_1001"
        assert MESSAGE_BY_CODE[ErrorCode.EVID_1001] == (
            "Description too short (min 10 chars)"
        )
        assert HTTP_STATUS_BY_CODE[ErrorCode.EVID_1001] == 400


class TestAC6GateFailureDetailsStructure:
    """AC-6: EVID_2001 gate failure details structure includes failed_checks[] and passed_checks[]."""

    def test_gate_failure_details_structure(self):
        from src.shared.schemas.error_response import (
            FailedGateCheck,
            GateFailureDetails,
        )

        fields = set(GateFailureDetails.model_fields.keys())
        assert fields == {"failed_checks", "passed_checks"}, (
            f"GateFailureDetails must have exactly "
            f"{{failed_checks, passed_checks}}, got {fields}"
        )

        details = GateFailureDetails(
            failed_checks=[
                FailedGateCheck(check="review_passed", reason="Review verdict is FAIL"),
                FailedGateCheck(
                    check="no_running_tasks",
                    reason="Task t_000123 is still running",
                ),
            ],
            passed_checks=[
                "artifact_exists",
                "version_match",
                "preferences_confirmed",
                "cost_logged",
            ],
        )
        assert details.failed_checks[0].check == "review_passed"
        assert details.failed_checks[0].reason == "Review verdict is FAIL"
        assert "artifact_exists" in details.passed_checks

        with pytest.raises(ValidationError):
            FailedGateCheck(check="review_passed")  # type: ignore[call-arg]


class TestAC7GateNoShortCircuitDocumented:
    """AC-7: Gate failure does not short-circuit -- all checks reported (documented in code)."""

    def test_gate_no_short_circuit_documented(self):
        from src.shared.schemas import error_response as er

        doc = (er.GateFailureDetails.__doc__ or "") + "\n" + (er.__doc__ or "")
        doc_lower = doc.lower()
        assert "short-circuit" in doc_lower or "short circuit" in doc_lower, (
            "GateFailureDetails docstring must document no-short-circuit behavior"
        )
        assert "all" in doc_lower and "check" in doc_lower, (
            "Docstring must state that all checks are reported"
        )


class TestAliasRegistry:
    """Friendly alias names resolve to canonical EVID codes.

    The BDD @error_ux feature authors scenarios against human-readable names
    (e.g. ``tts_api_timeout``). SPEC-A-011 owns the contract boundary that
    maps those names into the 17 canonical EVID codes so downstream UX
    components (SPEC-E-009) can render consistent treatments.
    """

    def test_alias_registry_resolves_known_names(self):
        from src.shared.constants.error_codes import (
            ERROR_CODE_ALIASES,
            ErrorCode,
            resolve_error_code,
        )

        # The three aliases the @error_ux BDD suite names explicitly.
        assert resolve_error_code("tts_api_timeout") is ErrorCode.EVID_3002
        assert resolve_error_code("financial_data_unavailable") is ErrorCode.EVID_4001
        assert resolve_error_code("worker_crash_max_retries") is ErrorCode.EVID_5002

        # Dict form exposes the same mapping.
        assert ERROR_CODE_ALIASES["tts_api_timeout"] is ErrorCode.EVID_3002
        assert ERROR_CODE_ALIASES["financial_data_unavailable"] is ErrorCode.EVID_4001
        assert ERROR_CODE_ALIASES["worker_crash_max_retries"] is ErrorCode.EVID_5002

    def test_alias_registry_passes_through_canonical_codes(self):
        from src.shared.constants.error_codes import ErrorCode, resolve_error_code

        # Canonical EVID codes resolve to themselves (idempotent lookup).
        assert resolve_error_code("EVID_3002") is ErrorCode.EVID_3002
        assert resolve_error_code("EVID_1001") is ErrorCode.EVID_1001

    def test_alias_registry_rejects_unknown(self):
        from src.shared.constants.error_codes import resolve_error_code

        with pytest.raises(KeyError):
            resolve_error_code("__not_a_known_alias__")

    def test_alias_registry_values_are_enum_members(self):
        from src.shared.constants.error_codes import ERROR_CODE_ALIASES, ErrorCode

        for alias, code in ERROR_CODE_ALIASES.items():
            assert isinstance(code, ErrorCode), (
                f"alias {alias!r} maps to {code!r}, expected ErrorCode member"
            )


class TestAC8NoMagicErrorStrings:
    """AC-8: No `EVID_\\d{4}` literals outside the constants module.

    Scope: backend + shared layers (the contract boundary that this SPEC owns).
    Frontend consumers (e.g. `src/frontend/utils/errorUxMap.ts`) are outside
    this task card's `allowed_files` and will be migrated to typed imports
    in a downstream SPEC-E task -- not enforced here to avoid coupling
    this contract test to work that is explicitly forbidden for this card.
    """

    def test_no_magic_error_strings(self):
        repo_root = Path(__file__).resolve().parents[3]
        src_root = repo_root / "src"
        assert src_root.is_dir(), f"src/ not found at {src_root}"

        # Modules that ARE allowed to declare the literals.
        allowed = {
            src_root / "shared" / "constants" / "error_codes.py",
            src_root / "shared" / "constants" / "error_codes.ts",
            src_root / "shared" / "contracts" / "error_codes.py",
            src_root / "shared" / "contracts" / "error_codes.ts",
        }
        # Layers enforced by this test -- contract + backend consumers.
        enforced_roots = (src_root / "backend", src_root / "shared")

        evid_re = re.compile(r"EVID_\d{4}")
        offenders: list[tuple[Path, int, str]] = []
        for root in enforced_roots:
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix not in {".py", ".ts", ".tsx"}:
                    continue
                if path in allowed:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if path.suffix == ".py":
                    offenders.extend(
                        _find_evid_in_python_code(path, text, evid_re, repo_root)
                    )
                else:
                    offenders.extend(
                        _find_evid_in_ts_code(path, text, evid_re, repo_root)
                    )

        assert not offenders, (
            "Magic EVID_* literals found outside "
            "src/shared/constants/error_codes.{py,ts}:\n"
            + "\n".join(f"  {p}:{n}: {s}" for p, n, s in offenders)
        )


def _find_evid_in_python_code(
    path: Path, text: str, evid_re: re.Pattern[str], repo_root: Path
) -> list[tuple[Path, int, str]]:
    """Grep Python source for EVID_* *excluding* comments and docstrings.

    Uses ``tokenize`` to skip COMMENT tokens, and ``ast`` to collect the
    line ranges of module/class/function docstrings (AST-level ``Expr`` +
    ``Constant[str]`` at the head of a body).
    """
    docstring_lines: set[int] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        docstring_owners = (
            ast.Module,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        )
        for node in ast.walk(tree):
            if not isinstance(node, docstring_owners):
                continue
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                start = first.lineno
                end = first.end_lineno or start
                docstring_lines.update(range(start, end + 1))

    hits: list[tuple[Path, int, str]] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except tokenize.TokenizeError:
        tokens = []
    comment_lines: set[int] = {
        tok.start[0] for tok in tokens if tok.type == tokenize.COMMENT
    }
    lines = text.splitlines()
    for tok in tokens:
        # Only flag EVID_* inside STRING literal tokens -- enum attribute
        # references like ``ErrorCode.EVID_2001`` are NAME tokens and are
        # the correct way to reference error codes outside the constants
        # module.
        if tok.type != tokenize.STRING:
            continue
        if not evid_re.search(tok.string):
            continue
        lineno = tok.start[0]
        if lineno in docstring_lines or lineno in comment_lines:
            continue
        hits.append((path.relative_to(repo_root), lineno, lines[lineno - 1].strip()))
    return hits


def _find_evid_in_ts_code(
    path: Path, text: str, evid_re: re.Pattern[str], repo_root: Path
) -> list[tuple[Path, int, str]]:
    """Grep TypeScript source for EVID_* *excluding* // and /* */ comments."""

    # Strip /* ... */ block comments first (replace with spaces to preserve
    # line numbers).
    def _strip_block(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    stripped = re.sub(r"/\*.*?\*/", _strip_block, text, flags=re.DOTALL)

    hits: list[tuple[Path, int, str]] = []
    for lineno, line in enumerate(stripped.splitlines(), start=1):
        # Remove // line comment tail.
        idx = line.find("//")
        code_part = line if idx < 0 else line[:idx]
        if evid_re.search(code_part):
            hits.append((path.relative_to(repo_root), lineno, line.strip()))
    return hits
