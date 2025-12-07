import random
from etl.utils.db import fetch_all_dict, execute

def enrich_companies():
    rows = fetch_all_dict("""
        SELECT id, name
        FROM companies
        WHERE revenue_estimate IS NULL
        LIMIT 100;
    """)

    for row in rows:
        revenue = random.randint(1_000_000, 20_000_000)
        employees = random.randint(10, 200)

        execute(
            """
            UPDATE companies
            SET revenue_estimate = %s,
                employee_count = %s,
                is_ecommerce = FALSE,
                industry_tag = 'Unknown',
                updated_at = now()
            WHERE id = %s
            """,
            (revenue, employees, row["id"])
        )

def main():
    enrich_companies()

if __name__ == "__main__":
    main()
