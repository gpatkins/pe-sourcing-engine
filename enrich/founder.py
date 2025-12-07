from __future__ import annotations

from typing import Any, Dict

from .base import EnrichmentModule


class FounderEnricher(EnrichmentModule):
    name = "founder"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for future integration with a people/company data API.
        return {}
