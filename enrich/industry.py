from __future__ import annotations

from typing import Any, Dict
import re

from .base import EnrichmentModule

KEYWORD_MAP = [
    ("industrial cleaning", "Industrial Cleaning"),
    ("pressure wash", "Industrial Cleaning"),
    ("janitorial", "Janitorial Services"),
    ("floor coating", "Flooring"),
    ("pest control", "Pest Control"),
    ("landscap", "Landscaping"),
    ("concrete", "Concrete Services"),
    ("excavation", "Excavation"),
]


class IndustryEnricher(EnrichmentModule):
    name = "industry"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        if company.get("industry_tag"):
            return {}

        text = (
            (company.get("description") or "") + " " +
            (company.get("name") or "")
        ).lower()
        text = re.sub(r"\s+", " ", text)

        for keyword, label in KEYWORD_MAP:
            if keyword in text:
                return {"industry_tag": label}

        return {}
