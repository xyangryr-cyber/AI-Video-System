"""[SPEC-D-012] GateRegistry -- look up gate by phase number.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Gate Registry"
"""

from __future__ import annotations

from typing import Dict, Type

from src.backend.gates.base_gate import BaseGate

_registry: Dict[int, Type[BaseGate]] = {}


def register_gate(phase: int, gate_cls: Type[BaseGate]) -> None:
    _registry[phase] = gate_cls


def get_gate(phase: int) -> Type[BaseGate]:
    return _registry.get(phase, BaseGate)
