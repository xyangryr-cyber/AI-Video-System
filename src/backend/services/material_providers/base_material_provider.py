"""[SPEC-D-014] BaseMaterialProvider -- abstract material provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMaterialProvider(ABC):
    @abstractmethod
    def fetch(self, **kwargs: Any) -> dict[str, Any]: ...
