from __future__ import annotations
import logging
import json
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from typing import Any, Dict
from .base import EnrichmentModule

# Load secrets.env with override so admin dashboard updates work in Docker
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config" / "secrets.env", override=True)

logger = logging.getLogger(__name__)


class AIClassifier(EnrichmentModule):
    name = "ai_classifier"

    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        description = company.get("description")
        company_name = company.get("name", "Unknown")

        print(f"\n[DEBUG] Gemini AI analyzing: {company_name}")
        
        if not description or len(description) < 20:
            print("   -> SKIPPING: No description.")
            return {}

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Act as a Private Equity Analyst. Analyze this company website text:
            "{description[:3500]}"

            Task: Extract structured data points.
            
            1. Legal Name: Look for "Copyright © 2024 [Legal Name]" or "Terms of Service".
            2. Industry Tag: Specific classification (e.g. "Commercial HVAC").
            3. NAICS Code: Determine the most accurate 6-digit NAICS code (2022 standard).
            4. Customer Type: "B2B", "B2C", or "Both".
            5. Revenue Model: "Recurring", "Project", or "Retail".
            6. Family Owned: boolean.
            7. Franchise: boolean.
            8. Owner Name: Look for names near "Founder", "President", "CEO", "Owner".
            9. Tech Stack: List of software found.
            10. Confidence: 0.0 to 1.0.

            Return strictly valid JSON:
            {{
                "legal_name": str or null,
                "industry_tag": str,
                "naics_code": "string (e.g. 238220)",
                "naics_description": "string (e.g. Plumbing, Heating, and AC Contractors)",
                "customer_type": str,
                "revenue_model": str,
                "is_family_owned": bool,
                "is_franchise": bool,
                "owner_name": str or null,
                "website_tech_stack": list[str],
                "confidence": float,
                "evidence": str
            }}
            """

            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            
            # Formatting outputs
            tech_stack = data.get("website_tech_stack")
            tech_stack_json = json.dumps(tech_stack) if isinstance(tech_stack, list) else None

            print(f"   -> SUCCESS: Tagged as '{data.get('industry_tag')}'")
            if data.get("naics_code"):
                print(f"   -> NAICS: {data.get('naics_code')} ({data.get('naics_description')})")

            return {
                "legal_name": data.get("legal_name"),
                "industry_tag": data.get("industry_tag", "Unknown"),
                "naics_code": data.get("naics_code"),
                "naics_description": data.get("naics_description"),
                "customer_type": data.get("customer_type"),
                "revenue_model": data.get("revenue_model"),
                "is_family_owned": data.get("is_family_owned", False),
                "is_franchise": data.get("is_franchise", False),
                "owner_name": data.get("owner_name"),
                "website_tech_stack": tech_stack_json,
                "ai_confidence": data.get("confidence"),
                "ai_evidence": data.get("evidence")
            }

        except Exception as e:
            print(f"   -> ERROR: Gemini API call failed: {e}")
            logger.warning(f"Gemini Enrichment failed: {e}")

        return {}
