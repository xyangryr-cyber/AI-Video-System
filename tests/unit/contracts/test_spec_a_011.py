"""Tests for [SPEC-A-011] HTTP Error Code System (SPEC-13A)."""

from __future__ import annotations

from tests.unit.contracts.test_error_codes import (
    EXPECTED_ERROR_CODES,
    TestAC1ErrorResponseSchema as _TestAC1ErrorResponseSchema,
    TestAC2Exactly17ErrorCodes as _TestAC2Exactly17ErrorCodes,
    TestAC3ErrorCodeHttpStatusMapping as _TestAC3ErrorCodeHttpStatusMapping,
    TestAC4ErrorCodeDomainPrefixes as _TestAC4ErrorCodeDomainPrefixes,
    TestAC5Evid1001Message as _TestAC5Evid1001Message,
    TestAC6GateFailureDetailsStructure as _TestAC6GateFailureDetailsStructure,
    TestAC7GateNoShortCircuitDocumented as _TestAC7GateNoShortCircuitDocumented,
    TestAC8NoMagicErrorStrings as _TestAC8NoMagicErrorStrings,
)


class TestAC1ErrorResponseSchema(_TestAC1ErrorResponseSchema):
    pass


class TestAC2Exactly17ErrorCodes(_TestAC2Exactly17ErrorCodes):
    def test_exactly_17_error_codes(self):
        from src.shared.constants.error_codes import ErrorCode

        actual = {e.value for e in ErrorCode}
        expected = set(EXPECTED_ERROR_CODES)
        missing = expected - actual
        assert not missing, f"Missing baseline SPEC-13A codes: {sorted(missing)}"
        assert len(expected) == 17, (
            f"Baseline snapshot drifted: expected 17, got {len(expected)}"
        )


class TestAC3ErrorCodeHttpStatusMapping(_TestAC3ErrorCodeHttpStatusMapping):
    def test_error_code_http_status_mapping(self):
        from src.shared.constants.error_codes import ErrorCode, HTTP_STATUS_BY_CODE

        allowed_statuses = {400, 404, 409, 422, 500, 503, 504}
        for code_value, (expected_status, _) in EXPECTED_ERROR_CODES.items():
            code = ErrorCode(code_value)
            actual_status = HTTP_STATUS_BY_CODE[code]
            assert actual_status == expected_status, (
                f"HTTP status mismatch for {code_value}: expected {expected_status}, got {actual_status}"
            )
            assert actual_status in allowed_statuses


class TestAC4ErrorCodeDomainPrefixes(_TestAC4ErrorCodeDomainPrefixes):
    pass


class TestAC5Evid1001Message(_TestAC5Evid1001Message):
    pass


class TestAC6GateFailureDetailsStructure(_TestAC6GateFailureDetailsStructure):
    pass


class TestAC7GateNoShortCircuitDocumented(_TestAC7GateNoShortCircuitDocumented):
    pass


class TestAC8NoMagicErrorStrings(_TestAC8NoMagicErrorStrings):
    pass
