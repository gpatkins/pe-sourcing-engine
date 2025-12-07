from __future__ import annotations
import logging
import json
import os
import requests
from typing import Any, Dict
from .base import EnrichmentModule

logger = logging.getLogger(__name__)

class NewsFinder(EnrichmentModule):
    name = "news_finder"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return {}

        company_name = company.get("name")
        if not company_name:
            return {}

        # Get location to anchor the search (Critical for reducing noise)
        city = company.get("city") or ""
        state = company.get("state") or ""
        
        logger.info(f"Checking news for: {company_name} ({city}, {state})")

        try:
            # 1. STRICTER QUERY
            # We force the City or State to be present in the results to avoid national noise
            # Query: "Company Name" "City" (lawsuit OR bankruptcy...)
            query = f'"{company_name}" "{city}" lawsuit OR bankruptcy OR fraud OR scandal OR "court case" OR complaint'
            
            payload = json.dumps({
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": 5,
                "tbs": "qdr:y5" # Last 5 years
            })
            
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post("https://google.serper.dev/news", headers=headers, data=payload)
            if response.status_code != 200:
                return {}

            results = response.json().get("news", [])
            
            if not results:
                return {"risk_flags": "Clean (No local negative news)"}

            risk_summary = []
            cleaned_news = []
            
            # 2. STRICTER FILTERING (Python Side)
            # Define risk keywords
            keywords = ["lawsuit", "sue", "bankrupt", "fraud", "scandal", "court", "guilty", "fine", "violation", "investigation"]
            
            # Create a "Simple Name" for matching (e.g., "Quality HVAC Inc" -> "Quality HVAC")
            simple_name = company_name.lower().replace("inc", "").replace("llc", "").replace("corp", "").strip()

            for item in results:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                
                text_blob = (title + " " + snippet).lower()
                
                # CHECK 1: Risk Keyword must exist
                has_risk = any(k in text_blob for k in keywords)
                
                # CHECK 2: Company Name (or City) must be explicit in the snippet
                # This prevents "HVAC industry lawsuit" articles from flagging a specific company
                is_relevant = (simple_name in text_blob) or (city.lower() in text_blob)
                
                if has_risk and is_relevant:
                    risk_summary.append(f"ALERT: {title}")
                
                cleaned_news.append({
                    "title": title,
                    "date": item.get("date"),
                    "source": item.get("source"),
                    "link": link
                })

            updates = {
                "recent_news": json.dumps(cleaned_news)
            }
            
            if risk_summary:
                updates["risk_flags"] = " | ".join(risk_summary[:2])
            else:
                updates["risk_flags"] = "Clean (News found but validated as irrelevant/safe)"
                
            print(f"   -> NEWS CHECK: Processed {len(results)} articles. Risks Flagged: {len(risk_summary)}")
            return updates

        except Exception as e:
            logger.warning(f"News search failed for {company_name}: {e}")
            
        return {}
