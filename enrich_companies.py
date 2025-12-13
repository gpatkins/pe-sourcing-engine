from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, List

import yaml
from psycopg.rows import dict_row

from etl.utils.db import get_connection
from etl.utils.logger import setup_logger
from etl.utils.state_manager import should_stop, set_running, clear_running

# --- MODULES ---
from enrich.domain import DomainEnricher
from enrich.about import AboutEnricher
from enrich.ecommerce import EcommerceEnricher
# from enrich.traffic import TrafficEnricher
from enrich.industry import IndustryEnricher
from enrich.founder import FounderEnricher
from enrich.revenue import RevenueEnricher
from enrich.ai_classifier import AIClassifier
from enrich.linkedin_finder import LinkedInFinder
from enrich.news_finder import NewsFinder
from enrich.owner_finder import OwnerFinder
from enrich.email_finder import EmailFinder

logger = setup_logger("enrichment")

def load_settings() -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parent
    cfg_path = base_dir / "config" / "settings.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_modules(config: Dict[str, Any]):
    enrichment_cfg = config.get("enrichment", {})
    modules_cfg = enrichment_cfg.get("modules", {})

    common_cfg = {
        "http_timeout_seconds": enrichment_cfg.get("http_timeout_seconds", 15),
        "user_agent": enrichment_cfg.get("user_agent", "PE-Sourcing-Engine/1.0"),
        "revenue_estimator": enrichment_cfg.get("revenue_estimator", {}),
    }

    modules = []

    modules.append(DomainEnricher(common_cfg))
    modules.append(AboutEnricher(common_cfg))
    modules.append(LinkedInFinder(common_cfg))

    modules.append(EcommerceEnricher(common_cfg))
    modules.append(IndustryEnricher(common_cfg))
    modules.append(FounderEnricher(common_cfg))

    modules.append(NewsFinder(common_cfg))
    modules.append(AIClassifier(common_cfg))
    modules.append(OwnerFinder(common_cfg))

    modules.append(EmailFinder(common_cfg))

    if modules_cfg.get("revenue", True):
        modules.append(RevenueEnricher(common_cfg))

    logger.info("Loaded modules: %s", ", ".join([m.name for m in modules]))
    return modules

def fetch_companies_to_enrich(conn, batch_size: int) -> List[Dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
            FROM companies
            WHERE enrichment_status IS NULL
               OR enrichment_status IN ('pending', 'partial')
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (batch_size,),
        )
        return cur.fetchall()

def apply_modules(company: Dict[str, Any], modules) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}
    current_state = company.copy()

    for module in modules:
        if should_stop():
            break

        try:
            delta = module.enrich(current_state)
            if delta:
                updates.update(delta)
                current_state.update(delta)
        except Exception as exc:
            logger.warning(f"Module {module.name} failed for {company.get('id')}: {exc}")

    return updates

def update_company(conn, company_id, updates: Dict[str, Any]):
    if not updates: return
    set_clauses = []
    values = []
    for col, val in updates.items():
        set_clauses.append(f"{col} = %s")
        values.append(val)
    values.append(company_id)
    sql = f"UPDATE companies SET {', '.join(set_clauses)} WHERE id = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, values)

def mark_complete(conn, company_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE companies SET enrichment_status = 'complete', last_enriched_at = %s WHERE id = %s;", (dt.datetime.now(dt.timezone.utc), company_id))

def mark_partial(conn, company_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE companies SET enrichment_status = 'partial' WHERE id = %s;", (company_id,))

def main():
    try:
        set_running("Enrichment")

        settings = load_settings()
        batch_size = int(settings.get("enrichment", {}).get("batch_size", 50))
        conn = get_connection()
        conn.autocommit = False

        try:
            modules = build_modules(settings)

            while True:
                if should_stop():
                    logger.info("STOP SIGNAL RECEIVED. Halting.")
                    break

                companies = fetch_companies_to_enrich(conn, batch_size)
                if not companies:
                    logger.info("No more companies to enrich.")
                    break

                logger.info(f"Fetched {len(companies)} companies to enrich")

                for company in companies:
                    if should_stop():
                        break

                    logger.info(f"Enriching company id={company['id']} name={company.get('name')}")
                    updates = apply_modules(company, modules)

                    if updates:
                        updates["last_enriched_at"] = dt.datetime.now(dt.timezone.utc)
                        update_company(conn, company["id"], updates)
                        mark_complete(conn, company["id"])
                        conn.commit()
                    else:
                        mark_partial(conn, company["id"])
                        conn.commit()

        finally:
            if 'conn' in locals():
                conn.close()

    finally:
        clear_running()

if __name__ == "__main__":
    main()
