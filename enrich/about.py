from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base import EnrichmentModule

logger = logging.getLogger(__name__)

class AboutEnricher(EnrichmentModule):
    name = "about"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        url = company.get("url")
        if not url:
            return {}

        timeout = int(self.config.get("http_timeout_seconds", 15))
        ua = self.config.get("user_agent", "PE-Sourcing-Bot/1.0")

        # Candidates to check for text
        candidates: List[str] = [
            url,
            f"{url.rstrip('/')}/about",
            f"{url.rstrip('/')}/about-us",
            f"{url.rstrip('/')}/our-story",
            f"{url.rstrip('/')}/contact",
        ]

        best_text = ""
        socials = {}

        for candidate in candidates:
            try:
                resp = requests.get(
                    candidate,
                    timeout=timeout,
                    headers={"User-Agent": ua},
                    allow_redirects=True,
                )
                if resp.status_code >= 400:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 1. Extract Social Links (New Feature)
                # We do this on every page we visit to maximize chances
                page_socials = self._extract_social_links(soup, url)
                socials.update(page_socials) # Merge found links

                # 2. Extract Text for AI
                text = self._extract_full_text(soup)
                if len(text) > len(best_text):
                    best_text = text
                
                if len(best_text) > 500 and len(socials) > 1:
                    break
                    
            except Exception as exc:
                logger.debug("Error fetching %s: %s", candidate, exc)

        updates = {}
        
        # Only update description if we found something substantial
        if best_text:
            updates["description"] = best_text[:5000]
            
        # Add found social links to the updates
        updates.update(socials)

        return updates

    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Scans all <a> tags for known social media patterns."""
        links = {}
        
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            
            # Resolve relative URLs just in case
            full_url = urljoin(base_url, a["href"])

            if "linkedin.com/company" in href:
                links["linkedin_company_url"] = full_url
            elif "linkedin.com/in/" in href:
                links["owner_linkedin_url"] = full_url
            elif "facebook.com" in href and "sharer" not in href:
                links["facebook_url"] = full_url
            elif "instagram.com" in href:
                links["instagram_url"] = full_url
            elif "twitter.com" in href or "x.com" in href:
                links["twitter_url"] = full_url
            elif "youtube.com" in href or "youtu.be" in href:
                links["youtube_url"] = full_url
                
        return links

    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style", "nav", "noscript"]):
            script.extract()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)
