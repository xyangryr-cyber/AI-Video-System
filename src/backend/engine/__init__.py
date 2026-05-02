"""[SPEC-C-001 / SPEC-C-015] Backend engine package.

Public surface: ``WorkflowEngine`` (state/event owner),
``EventBus`` (stateless publish helper), and ``GateKeeper`` (SPEC-8
phase gate).
"""

from src.backend.engine import gatekeeper
from src.backend.engine.event_bus import EventBus
from src.backend.engine.workflow_engine import WorkflowEngine

__all__ = ["EventBus", "WorkflowEngine", "gatekeeper"]
