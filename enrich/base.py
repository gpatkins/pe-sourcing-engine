from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class EnrichmentModule(ABC):
    """
    Base class for all enrichment modules.

    Each module receives a company dict and returns a dict of updates:
        {"column_name": new_value, ...}
    """

    name: str = "base"

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
