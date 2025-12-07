from __future__ import annotations
from typing import Any, Dict
from .base import EnrichmentModule

class RevenueEnricher(EnrichmentModule):
    name = "revenue"

    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Trust Manual Data: If you manually entered revenue, don't overwrite it.
        if company.get("revenue_estimate") and company.get("source") == "manual":
            return {}

        # 2. Gather Signals
        # We use the new AI columns to make a better guess
        employees = company.get("employee_count") or 0
        industry = (company.get("industry_tag") or "").lower()
        customer = (company.get("customer_type") or "").lower()
        is_franchise = company.get("is_franchise") or False
        is_commercial = "commercial" in industry or "industrial" in industry
        
        estimate = 0

        # 3. METHOD A: Employee-Based (Most Accurate)
        # Service businesses typically generate $150k - $300k per employee.
        if employees > 0:
            rpe = 200000 # Default Baseline ($200k/head)
            
            if is_commercial:
                rpe = 350000 # Higher ticket size for commercial work
            elif "cleaning" in industry or "janitorial" in industry:
                rpe = 90000 # Lower ticket size, lower margin
            
            estimate = employees * rpe

        # 4. METHOD B: Sector Baseline (Fallback)
        # If we have NO employee count, we use a conservative floor based on the business type.
        else:
            # Baseline for a "Mom & Pop" local business
            estimate = 1_200_000 
            
            # Adjusters based on AI Findings
            if is_commercial:
                estimate += 1_500_000  # Commercial shops are generally larger
            if "industrial" in industry:
                estimate += 3_000_000  # Industrial is capital intensive -> higher rev
            if customer == "b2b":
                estimate *= 1.25       # B2B contracts > B2C transactions
            
            # Penalties
            if is_franchise:
                estimate = 1_500_000   # Cap franchises (single units usually ~$1-2M)
            if "residential" in industry and "cleaning" in industry:
                estimate = 750_000     # Maid services are often smaller

        return {"revenue_estimate": int(estimate)}
