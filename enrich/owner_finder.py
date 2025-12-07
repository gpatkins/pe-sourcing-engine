from __future__ import annotations
import logging
import json
import os
import requests
import google.generativeai as genai
from typing import Any, Dict
from .base import EnrichmentModule

logger = logging.getLogger(__name__)

class OwnerFinder(EnrichmentModule):
    name = "owner_finder"

    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)
        # Setup Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Skip if we already know the owner
        if company.get("owner_name"):
            return {}

        serper_key = os.getenv("SERPER_API_KEY")
        if not serper_key:
            return {}

        company_name = company.get("name")
        city = company.get("city") or ""
        state = company.get("state") or ""
        
        # Skip if we don't have a name
        if not company_name: 
            return {}

        logger.info(f"Ghost hunting for owner of: {company_name}")

        try:
            # 2. Targeted "Dorking" Query
            # We look for CEO, Owner, President specifically in their city
            query = f'site:linkedin.com OR site:zoominfo.com OR site:buzzfile.com "{company_name}" {city} {state} (Owner OR CEO OR President OR Principal)'
            
            payload = json.dumps({
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": 5 # Top 5 results are usually enough
            })
            
            headers = {
                'X-API-KEY': serper_key,
                'Content-Type': 'application/json'
            }

            # 3. Call Serper
            response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
            if response.status_code != 200:
                return {}

            results = response.json().get("organic", [])
            if not results:
                return {}

            # 4. Compile the Evidence
            # We mash the snippets together into one block of text for the AI
            evidence_text = ""
            for item in results:
                evidence_text += f"SOURCE: {item.get('title')}\nTEXT: {item.get('snippet')}\n\n"

            # 5. Ask Gemini to play Detective
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Task: Identify the name of the Owner, CEO, or President of "{company_name}" based ONLY on these search snippets.
            
            Search Results:
            {evidence_text[:3000]}
            
            Instructions:
            - Look for names associated with titles like Owner, CEO, President, Founder, Principal.
            - If multiple names appear, prefer the Owner.
            - If NO name is clearly identified, return null.
            - Return strictly valid JSON.

            JSON Schema:
            {{
                "owner_name": str or null,
                "title": str or null,
                "confidence": float (0.0 to 1.0)
            }}
            """

            ai_resp = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(ai_resp.text)
            
            # 6. Return Data if confident
            if data.get("owner_name") and data.get("confidence", 0) > 0.6:
                print(f"   -> GHOST FOUND: {data.get('owner_name')} ({data.get('title')})")
                return {
                    "owner_name": data.get("owner_name"),
                    "owner_source": "Serper Ghost Search"
                }

        except Exception as e:
            logger.warning(f"Owner finding failed for {company_name}: {e}")
            
        return {}
