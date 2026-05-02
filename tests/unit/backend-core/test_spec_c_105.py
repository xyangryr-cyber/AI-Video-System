"""Tests for [SPEC-C-105] ChartIntentEngine 8 state machine.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-6 (SPEC-6.V).

Test matrix (AC mapping from task card):
  AC-1  Property-based: the engine accepts the 10 legal (from, to) edges
        and rejects every other pair in {CHART_STATES} x {CHART_STATES}
        with ``IllegalChartStateTransition``. Exhaustive 8x8 = 64 pairs
        plus a seeded random walk of 4000 draws validates sequences.
  AC-2  Clarification field priority:
        time_range > granularity > entity > unit > comparison_targets,
        at most 2 fields returned per ``next_clarification_fields`` call.
  AC-3  awaiting_verification: engine stays until every chart-bound
        claim is ``verified``; any ``rejected`` forces ``failed``;
        pending / missing claim set blocks advance.
  AC-4  Data source unavailable: ``handle_fetch_result`` transitions to
        ``failed`` directly -- never ``awaiting_verification`` or
        ``rendering``. The legal-edge matrix also excludes
        ``(fetching, rendering)``.
"""

from __future__ import annotations

import random

import pytest

from src.backend.agents.chart_intent_engine import (
    CHART_STATES,
    CLARIFICATION_PRIORITY,
    LEGAL_EDGES,
    MAX_CLARIFICATIONS_PER_ROUND,
    TERMINAL_STATES,
    ChartIntentEngine,
    IllegalChartStateTransition,
)


_EXPECTED_LEGAL_EDGES = frozenset(
    {
        ("awaiting_clarification", "fetching"),
        ("awaiting_clarification", "cancelled"),
        ("fetching", "awaiting_verification"),
        ("fetching", "failed"),
        ("awaiting_verification", "awaiting_confirmation"),
        ("awaiting_verification", "failed"),
        ("awaiting_confirmation", "rendering"),
        ("awaiting_confirmation", "cancelled"),
        ("rendering", "completed"),
        ("rendering", "failed"),
    }
)


class TestAC1:
    """AC-1: property-based -- any random transition respects legal edges."""

    def test_property_based_transitions_respect_legal_edges(self):
        # Matrix sanity: 8 states, 10 legal edges, 3 terminals.
        assert set(CHART_STATES) == {
            "awaiting_clarification",
            "fetching",
            "awaiting_verification",
            "awaiting_confirmation",
            "rendering",
            "completed",
            "failed",
            "cancelled",
        }
        assert len(CHART_STATES) == 8
        assert LEGAL_EDGES == _EXPECTED_LEGAL_EDGES
        assert len(LEGAL_EDGES) == 10
        assert TERMINAL_STATES == frozenset({"completed", "failed", "cancelled"})

        engine = ChartIntentEngine()

        # Exhaustive 8x8 = 64 pairs: legal succeeds, illegal raises.
        for from_state in CHART_STATES:
            for to_state in CHART_STATES:
                pair = (from_state, to_state)
                if pair in _EXPECTED_LEGAL_EDGES:
                    engine.assert_legal_transition(from_state, to_state)
                else:
                    with pytest.raises(IllegalChartStateTransition) as exc:
                        engine.assert_legal_transition(from_state, to_state)
                    assert exc.value.from_state == from_state
                    assert exc.value.to_state == to_state

        # Terminal states have no outgoing edges.
        for terminal in TERMINAL_STATES:
            for to_state in CHART_STATES:
                with pytest.raises(IllegalChartStateTransition):
                    engine.assert_legal_transition(terminal, to_state)

        # Seeded random walk -- 4000 draws, arbitrary sequences of
        # (from, to) pairs; never violates the matrix.
        rng = random.Random(0xC105)
        current = "awaiting_clarification"
        for _ in range(4000):
            candidate = rng.choice(CHART_STATES)
            pair = (current, candidate)
            if pair in _EXPECTED_LEGAL_EDGES:
                engine.assert_legal_transition(current, candidate)
                current = candidate
                if current in TERMINAL_STATES:
                    # Restart walk from the entry state.
                    current = "awaiting_clarification"
            else:
                with pytest.raises(IllegalChartStateTransition):
                    engine.assert_legal_transition(current, candidate)


class TestAC2:
    """AC-2: clarification priority time_range/granularity > entity > unit/comparison."""

    def test_clarification_field_priority_order(self):
        # SPEC order is fixed; the engine exposes the tuple verbatim.
        assert CLARIFICATION_PRIORITY == (
            "time_range",
            "granularity",
            "entity",
            "unit",
            "comparison_targets",
        )
        assert MAX_CLARIFICATIONS_PER_ROUND == 2

        engine = ChartIntentEngine()

        # All five missing -> returns the FIRST two (time_range, granularity).
        all_missing = {
            "time_range": None,
            "granularity": None,
            "entity": None,
            "unit": None,
            "comparison_targets": None,
        }
        assert engine.next_clarification_fields(all_missing) == [
            "time_range",
            "granularity",
        ]

        # time_range provided -> (granularity, entity).
        tr_ok = dict(all_missing, time_range="2024-01-01..2024-06-30")
        assert engine.next_clarification_fields(tr_ok) == ["granularity", "entity"]

        # time_range + granularity provided -> (entity, unit).
        tg_ok = dict(tr_ok, granularity="month")
        assert engine.next_clarification_fields(tg_ok) == ["entity", "unit"]

        # time_range + granularity + entity provided -> (unit, comparison_targets).
        tge_ok = dict(tg_ok, entity="GOLD")
        assert engine.next_clarification_fields(tge_ok) == [
            "unit",
            "comparison_targets",
        ]

        # Entity missing but lower-priority filled -> still surfaces entity.
        entity_only = {
            "time_range": "2024-01-01..2024-06-30",
            "granularity": "month",
            "entity": None,
            "unit": "USD/oz",
            "comparison_targets": ["SILVER"],
        }
        assert engine.next_clarification_fields(entity_only) == ["entity"]

        # Empty string / empty list treated as missing.
        blanks = {
            "time_range": "",
            "granularity": "month",
            "entity": "",
            "unit": "USD",
            "comparison_targets": [],
        }
        assert engine.next_clarification_fields(blanks) == [
            "time_range",
            "entity",
        ]

        # Fully populated -> no clarifications needed.
        populated = {
            "time_range": "2024-01-01..2024-06-30",
            "granularity": "month",
            "entity": "GOLD",
            "unit": "USD/oz",
            "comparison_targets": ["SILVER"],
        }
        assert engine.next_clarification_fields(populated) == []


class TestAC3:
    """AC-3: awaiting_verification holds until every chart-bound claim verified."""

    def test_awaiting_verification_waits_all_chart_bound_claims(self):
        engine = ChartIntentEngine()

        # Empty claim set: engine refuses to advance (no evidence yet).
        assert engine.advance_after_verification([]) == "awaiting_verification"

        # Any single pending claim -> still awaiting_verification.
        pending = [
            {"claim_id": "c_001", "status": "verified"},
            {"claim_id": "c_002", "status": "pending"},
            {"claim_id": "c_003", "status": "verified"},
        ]
        assert engine.advance_after_verification(pending) == "awaiting_verification"

        # User-disputed is also non-terminal -- hold.
        disputed = [
            {"claim_id": "c_001", "status": "verified"},
            {"claim_id": "c_002", "status": "user_disputed"},
        ]
        assert engine.advance_after_verification(disputed) == "awaiting_verification"

        # Any rejected claim -> verifier FAIL branch -> failed.
        rejected = [
            {"claim_id": "c_001", "status": "verified"},
            {"claim_id": "c_002", "status": "rejected"},
            {"claim_id": "c_003", "status": "pending"},
        ]
        assert engine.advance_after_verification(rejected) == "failed"

        # All verified -> PASS branch -> awaiting_confirmation.
        all_verified = [
            {"claim_id": "c_001", "status": "verified"},
            {"claim_id": "c_002", "status": "verified"},
            {"claim_id": "c_003", "status": "verified"},
        ]
        assert (
            engine.advance_after_verification(all_verified) == "awaiting_confirmation"
        )

        # Destinations from both branches must be legal matrix edges.
        assert ("awaiting_verification", "awaiting_confirmation") in LEGAL_EDGES
        assert ("awaiting_verification", "failed") in LEGAL_EDGES
        # Skipping verification straight to rendering is NEVER legal.
        assert ("awaiting_verification", "rendering") not in LEGAL_EDGES


class TestAC4:
    """AC-4: unavailable data source goes straight to failed (not rendering)."""

    def test_unavailable_data_source_transitions_to_failed(self):
        engine = ChartIntentEngine()

        # Data source available -> awaiting_verification.
        assert (
            engine.handle_fetch_result(data_source_available=True)
            == "awaiting_verification"
        )

        # Data source unavailable -> failed (skip verification + rendering).
        assert engine.handle_fetch_result(data_source_available=False) == "failed"

        # Matrix sanity: the ONLY two legal successors of `fetching` are
        # awaiting_verification and failed. `rendering` must NOT be legal.
        assert ("fetching", "awaiting_verification") in LEGAL_EDGES
        assert ("fetching", "failed") in LEGAL_EDGES
        assert ("fetching", "rendering") not in LEGAL_EDGES
        assert ("fetching", "awaiting_confirmation") not in LEGAL_EDGES
        assert ("fetching", "completed") not in LEGAL_EDGES

        # The engine also refuses a fetching -> rendering assertion.
        with pytest.raises(IllegalChartStateTransition):
            engine.assert_legal_transition("fetching", "rendering")
