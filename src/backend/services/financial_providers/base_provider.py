"""[SPEC-D-013] BaseProvider -- abstract financial data provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProvider(ABC):
    @abstractmethod
    def fetch(self, *, symbol: str, start: str, end: str) -> Dict[str, Any]: ...
