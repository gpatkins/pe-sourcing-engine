from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urlparse

from .base import EnrichmentModule


class DomainEnricher(EnrichmentModule):
    name = "domain"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        url = company.get("url")
        if not url:
            return {}

        cleaned = self._normalize_url(url)
        if cleaned and cleaned != url:
            return {"url": cleaned}
        return {}

    def _normalize_url(self, url: str) -> str:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if netloc.startswith("www."):
            netloc = netloc[4:]

        return f"https://{netloc}".rstrip("/")
