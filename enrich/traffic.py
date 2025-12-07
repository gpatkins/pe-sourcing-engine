from __future__ import annotations

from typing import Any, Dict
import logging

import requests

from .base import EnrichmentModule

logger = logging.getLogger(__name__)


class TrafficEnricher(EnrichmentModule):
    name = "traffic"

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

            size = len(resp.content)

            if size < 50_000:
                score = 10
            elif size < 200_000:
                score = 30
            elif size < 1_000_000:
                score = 60
            else:
                score = 80

            return {"web_traffic_estimate": score}

        except Exception as exc:  # noqa: BLE001
            logger.debug("Traffic enrichment failed for %s: %s", url, exc)
            return {}
