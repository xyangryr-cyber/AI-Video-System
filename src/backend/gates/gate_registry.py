"""[SPEC-D-012] GateRegistry -- look up gate by phase number.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Gate Registry"
"""

from __future__ import annotations

from src.backend.gates.base_gate import BaseGate
from src.backend.gates.gate_p0 import GateP0

_registry: dict[int, type[BaseGate]] = {}


def register_gate(phase: int, gate_cls: type[BaseGate]) -> None:
    _registry[phase] = gate_cls


def get_gate(phase: int) -> type[BaseGate]:
    return _registry.get(phase, BaseGate)


register_gate(0, GateP0)
