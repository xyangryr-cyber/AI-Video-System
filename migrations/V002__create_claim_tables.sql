-- [SPEC-A-100] V002: Claim / VerificationRecord tables.
-- Authority: docs/specs/SPEC-A-contracts.md §A-BDD-1 (SPEC-0A.8).
--
-- Creates two new first-class tables (orthogonal to V001's 10-table core)
-- so facts/data/events/citations can carry verification lifecycle state
-- across P2/P7/P8/P9 (v3.16 BDD).
--
-- Legacy compatibility:
--   claims.claim_id accepts the v3.15 `dp_*` form in addition to the
--   canonical `claim_{phase}_{seq}` form, so P2 output can lift
--   existing key_data_point.data_point_id values without rewriting IDs.

CREATE TABLE claims (
    claim_id        TEXT PRIMARY KEY,
    claim_type      TEXT NOT NULL
        CHECK(claim_type IN ('fact','data','event','citation','image_backed')),
    text            TEXT NOT NULL,
    value           TEXT,                       -- JSON-encoded scalar (number or string)
    unit            TEXT,
    entity          TEXT,
    time_range_start TEXT,                      -- ISO8601
    time_range_end   TEXT,                      -- ISO8601
    source_phase    TEXT NOT NULL
        CHECK(source_phase IN ('P2','P7','P8','P9','user_input')),
    source_artifact TEXT NOT NULL,
    source_span_start_char  INTEGER,
    source_span_end_char    INTEGER,
    source_span_segment_id  TEXT,
    blocking_level  TEXT NOT NULL DEFAULT 'none'
        CHECK(blocking_level IN ('hard','soft','none')),
    verification_status TEXT NOT NULL DEFAULT 'pending'
        CHECK(verification_status IN (
            'pending','verifying','verified','failed',
            'stale','superseded','user_disputed'
        )),
    created_at      TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_claims_source_phase_status
    ON claims(source_phase, verification_status);

CREATE TABLE verification_records (
    verification_id TEXT PRIMARY KEY,
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id),
    verifier_type   TEXT NOT NULL
        CHECK(verifier_type IN (
            'fact_check_agent','financial_data_service',
            'web_search','user_override'
        )),
    evidence_refs   TEXT NOT NULL DEFAULT '[]',  -- JSON array of {url?,doc_path?,snippet?}
    checked_at      TEXT NOT NULL,
    expires_at      TEXT,
    verdict         TEXT NOT NULL
        CHECK(verdict IN ('verified','failed','inconclusive')),
    reason          TEXT,
    confidence      REAL
        CHECK(confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_verification_records_claim_id
    ON verification_records(claim_id);
