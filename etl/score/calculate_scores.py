import os
import yaml
import logging
from etl.utils.db import get_connection, fetch_all_dict

logger = logging.getLogger("scoring")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "config", "settings.yaml")

def load_config():
    with open(SETTINGS_PATH, "r") as f:
        return yaml.safe_load(f)

def calculate_score(company):
    score = 0
    breakdown = []

    # --- 1. FINANCIAL SIZE (Max 30) ---
    rev = company.get("revenue_estimate") or 0
    if rev > 1_000_000:
        if rev < 5_000_000:
            score += 10
            breakdown.append("size_small")
        elif rev < 15_000_000:
            score += 20
            breakdown.append("size_medium")
        else:
            score += 30
            breakdown.append("size_large")
    else:
        # Too small or unknown
        score += 0

    # --- 2. QUALITY (Max 40) ---
    # Family Owned is the holy grail
    if company.get("is_family_owned"):
        score += 20
        breakdown.append("family_owned")

    # Franchises are usually bad targets for platform plays
    if company.get("is_franchise"):
        score -= 50
        breakdown.append("franchise_penalty")

    # B2B / Commercial is preferred over pure residential
    ind_tag = (company.get("industry_tag") or "").lower()
    cust_type = (company.get("customer_type") or "").lower()
    if "commercial" in ind_tag or "industrial" in ind_tag or "b2b" in cust_type:
        score += 20
        breakdown.append("commercial_focus")
    elif "residential" in ind_tag:
        score += 5
        breakdown.append("residential_focus")

    # --- 3. ACTIONABILITY (Max 30) ---
    # Can we actually contact the owner?
    if company.get("owner_name"):
        score += 15
        breakdown.append("owner_known")

    if company.get("linkedin_company_url") or company.get("owner_linkedin_url"):
        score += 15
        breakdown.append("linkedin_found")

    # --- 4. RISK (Penalty) ---
    # Lawsuits, Bankruptcy, Fraud = Deal Killer
    risk = company.get("risk_flags")
    if risk and "ALERT" in risk:
        score -= 50
        breakdown.append("risk_alert")

    # Clamp score 0-100
    return max(0, min(100, score))

def main():
    cfg = load_config()

    # Fetch all data needed for scoring
    sql = """
        SELECT
            id, name, revenue_estimate,
            industry_tag, customer_type,
            is_family_owned, is_franchise,
            owner_name, linkedin_company_url, owner_linkedin_url,
            risk_flags
        FROM companies
    """
    logger.info("Fetching companies to score...")
    companies = fetch_all_dict(sql)
    logger.info(f"Found {len(companies)} companies.")

    updates = []
    # Calculate in Memory
    for c in companies:
        total = calculate_score(c)
        updates.append((total, c["id"]))

    if not updates:
        return

    # Batch Update using psycopg3
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # psycopg3 way: use executemany instead of execute_batch
                cur.executemany(
                    "UPDATE companies SET buyability_score = %s, updated_at = now() WHERE id = %s",
                    updates
                )
            conn.commit()
        logger.info(f"Updated scores for {len(updates)} companies.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
