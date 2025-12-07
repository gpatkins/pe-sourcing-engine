from __future__ import annotations

from typing import Any, Dict
import logging

import requests
from bs4 import BeautifulSoup

from .base import EnrichmentModule

logger = logging.getLogger(__name__)

SIGNATURES = [
    "cdn.shopify.com",
    "woocommerce",
    "wp-e-commerce",
    "add to cart",
    "checkout",
]


class EcommerceEnricher(EnrichmentModule):
    name = "ecommerce"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        url = company.get("url")
        if not url:
            return {}

        timeout = int(self.config.get("http_timeout_seconds", 10))
        ua = self.config.get("user_agent", "PE-Sourcing-Engine/0.1")

        try:
            resp = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": ua},
                allow_redirects=True,
            )
            if resp.status_code >= 400:
                return {}

            text = resp.text.lower()
            if any(sig in text for sig in SIGNATURES):
                return {"is_ecommerce": True}

            soup = BeautifulSoup(resp.text, "html.parser")
            body_text = soup.get_text(" ", strip=True).lower()
            if "add to cart" in body_text:
                return {"is_ecommerce": True}

        except Exception as exc:  # noqa: BLE001
            logger.debug("Ecommerce enrichment failed for %s: %s", url, exc)

        return {}
