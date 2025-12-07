from __future__ import annotations
import logging
import re
import requests
from typing import Any, Dict
from .base import EnrichmentModule

logger = logging.getLogger(__name__)

class EmailFinder(EnrichmentModule):
    name = "email_finder"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # Skip if we already have an email (unless you want to overwrite)
        if company.get("founder_email"):
            return {}

        url = company.get("url")
        if not url: return {}

        logger.info(f"Scanning for emails: {url}")
        
        # We check Homepage + Contact Page
        candidates = [url, f"{url.rstrip('/')}/contact", f"{url.rstrip('/')}/about"]
        found_emails = set()

        # Regex for email (simple but effective)
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
        # Junk filter (ignore these common false positives)
        ignore_list = {'sentry.io', 'wix.com', 'squarespace.com', 'wordpress.com', 'example.com', 'domain.com', '.png', '.jpg', '.jpeg'}

        ua = self.config.get("user_agent", "PE-Sourcing-Bot/1.0")

        for page in candidates:
            try:
                resp = requests.get(page, headers={"User-Agent": ua}, timeout=10)
                if resp.status_code >= 400: continue
                
                # Scan raw text
                matches = email_pattern.findall(resp.text)
                
                for email in matches:
                    email = email.lower()
                    if any(bad in email for bad in ignore_list):
                        continue
                    found_emails.add(email)
                    
            except Exception:
                continue

        if not found_emails:
            return {}

        # Logic to pick the "Best" email
        best_email = None
        owner_name = (company.get("owner_name") or "").lower()
        
        # 1. Look for founder match (e.g. 'john@' if owner is 'John Smith')
        if owner_name:
            parts = owner_name.split()
            first_name = parts[0] if parts else ""
            if first_name:
                for e in found_emails:
                    if first_name in e:
                        best_email = e
                        break
        
        # 2. If no founder match, pick the first non-generic one
        if not best_email:
            generic_prefixes = {'info', 'contact', 'sales', 'support', 'admin', 'office', 'hello'}
            for e in found_emails:
                prefix = e.split('@')[0]
                if prefix not in generic_prefixes:
                    best_email = e
                    break
        
        # 3. Fallback to generic
        if not best_email:
            best_email = list(found_emails)[0]

        print(f"   -> FOUND EMAIL: {best_email}")
        return {"founder_email": best_email}
