"""Tests for [SPEC-A-008] Table Read/Write Ownership Registry."""

import pytest

from src.shared.contracts.table_ownership import TABLE_OWNERSHIP, TableOwnership


class TestAC1All10TablesCovered:
    """AC-1: Registry covers all 10 tables with writer, write_trigger, and reader fields"""

    def test_all_10_tables_covered(self):
        assert len(TABLE_OWNERSHIP) == 10
        required_tables = {
            "projects",
            "phases",
            "task_ledger",
            "async_tasks",
            "events",
            "preferences",
            "agent_call_log",
            "system_status",
            "financial_data_cache",
            "preference_snapshots",
        }
        registered = {e.table_name for e in TABLE_OWNERSHIP}
        assert registered == required_tables
        for entry in TABLE_OWNERSHIP:
            assert entry.writer
            assert entry.write_trigger
            assert entry.readers


class TestAC2ProjectsOwnership:
    """AC-2: projects table: writer=API, readers=[frontend, WorkflowEngine]"""

    def test_projects_ownership(self):
        e = _find("projects")
        assert e.writer == "API"
        assert "frontend" in e.readers
        assert "WorkflowEngine" in e.readers


class TestAC3PhasesOwnership:
    """AC-3: phases table: writer=WorkflowEngine, readers=[frontend, GateKeeper]"""

    def test_phases_ownership(self):
        e = _find("phases")
        assert e.writer == "WorkflowEngine"
        assert "frontend" in e.readers
        assert "GateKeeper" in e.readers


class TestAC4TaskLedgerOwnership:
    """AC-4: task_ledger table: writer=WorkflowEngine, readers=[Dispatcher, frontend, GateKeeper]"""

    def test_task_ledger_ownership(self):
        e = _find("task_ledger")
        assert e.writer == "WorkflowEngine"
        assert "Dispatcher" in e.readers
        assert "frontend" in e.readers
        assert "GateKeeper" in e.readers


class TestAC5EventsOwnership:
    """AC-5: events table: writer=[API, WorkflowEngine], readers=[frontend, WS broadcast]"""

    def test_events_ownership(self):
        e = _find("events")
        assert "API" in e.writer
        assert "WorkflowEngine" in e.writer
        assert "frontend" in e.readers
        assert "WS" in e.readers


class TestAC6PreferencesOwnership:
    """AC-6: preferences table: writer=API, readers=[frontend, ProducerAgent, PreferenceExtractor]"""

    def test_preferences_ownership(self):
        e = _find("preferences")
        assert e.writer == "API"
        assert "frontend" in e.readers
        assert "ProducerAgent" in e.readers
        assert "PreferenceExtractor" in e.readers


class TestAC7RegistryImmutable:
    """AC-7: Registry exported as frozen/immutable data structure"""

    def test_registry_immutable(self):
        assert isinstance(TABLE_OWNERSHIP, tuple)
        with pytest.raises(TypeError):
            TABLE_OWNERSHIP[0] = "mutated"


def _find(name: str) -> TableOwnership:
    for e in TABLE_OWNERSHIP:
        if e.table_name == name:
            return e
    raise KeyError(name)
