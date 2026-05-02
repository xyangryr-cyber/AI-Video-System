"""[SPEC-D-012] Gate registry binding -- imports and registers all 12 phase gates.

All gate classes are imported here and registered with the gate_registry
so that ``get_gate(phase)`` returns the correct gate class at runtime.
"""

from __future__ import annotations

from src.backend.gates.gate_7a import Gate7A
from src.backend.gates.gate_p0 import GateP0
from src.backend.gates.gate_p1 import GateP1
from src.backend.gates.gate_p2 import GateP2
from src.backend.gates.gate_p3 import GateP3
from src.backend.gates.gate_p4 import GateP4Checker
from src.backend.gates.gate_p5 import GateP5
from src.backend.gates.gate_p6 import GateP6
from src.backend.gates.gate_p7 import GateP7
from src.backend.gates.gate_p8 import GateP8
from src.backend.gates.gate_p9 import GateP9
from src.backend.gates.gate_p10 import GateP10
from src.backend.gates.gate_p11 import GateP11
from src.backend.gates.gate_registry import register_gate

register_gate(0, GateP0)
register_gate(1, GateP1)
register_gate(2, GateP2)
register_gate(3, GateP3)
register_gate(4, GateP4Checker)
register_gate(5, GateP5)
register_gate(6, GateP6)
register_gate(7, GateP7)
register_gate(7, Gate7A)  # Additional sub-phase gate at phase 7
register_gate(8, GateP8)
register_gate(9, GateP9)
register_gate(10, GateP10)
register_gate(11, GateP11)
