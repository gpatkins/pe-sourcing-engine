from __future__ import annotations
import logging
import time
import random
from typing import Any, Dict
from duckduckgo_search import DDGS
from .base import EnrichmentModule

logger = logging.getLogger(__name__)

class LinkedInFinder(EnrichmentModule):
    name = "linkedin_finder"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Skip if we already have the LinkedIn URL
        if company.get("linkedin_company_url"):
            return {}
            
        company_name = company.get("name")
        if not company_name:
            return {}

        # 2. Construct Query
        # We search specifically for the company name on LinkedIn
        location = f"{company.get('city') or ''} {company.get('state') or ''}".strip()
        query = f'site:linkedin.com "{company_name}" {location}'

        logger.info(f"Searching LinkedIn for: {company_name}")
        
        try:
            # 3. Search DuckDuckGo (Max 3 results)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            # 4. Parse Results
            updates = {}
            for r in results:
                link = r.get("href", "")
                
                # DEBUG: Print what we found so we know if it's working
                print(f"   -> RAW RESULT: {link}")

                # Check for Company Page
                if "linkedin.com/company/" in link:
                    print(f"   -> FOUND LINKEDIN COMPANY: {link}")
                    updates["linkedin_company_url"] = link
                    # If we found the company page, we are happy. Stop looking.
                    break 
                
                # Check for Owner/Person Page
                elif "linkedin.com/in/" in link and not updates.get("owner_linkedin_url"):
                    print(f"   -> FOUND POTENTIAL OWNER: {link}")
                    updates["owner_linkedin_url"] = link
            
            if updates:
                # Sleep randomly to be nice to the search engine
                time.sleep(random.uniform(1, 2))
                return updates

        except Exception as e:
            logger.warning(f"LinkedIn search failed for {company_name}: {e}")
            
        return {}
