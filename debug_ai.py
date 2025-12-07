import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Load Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "config/secrets.env"))

# DB Connection
def get_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def debug_one_company():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Grab a company that has a description but missing AI data
    print("Fetching a test company...")
    cur.execute("""
        SELECT name, description 
        FROM companies 
        WHERE description IS NOT NULL 
        LIMIT 1
    """)
    company = cur.fetchone()
    conn.close()

    if not company:
        print("Error: No companies with descriptions found.")
        return

    print(f"\n--- TESTING: {company['name']} ---")
    
    prompt = f"""
    Act as a Private Equity Analyst. Analyze this text:
    "{company['description'][:3000]}"

    Task: Extract structured data.
    1. Industry Tag: Specific classification.
    2. Customer Type: "B2B", "B2C", or "Both".
    3. Revenue Model: "Recurring", "Project", or "Retail".
    4. Family Owned: boolean.
    5. Franchise: boolean.
    6. Owner Name: Name of founder/owner/CEO.
    7. Tech Stack: List of software.
    8. Confidence: 0.0 to 1.0.
    9. Evidence: Quote supporting the findings.

    Return strictly valid JSON with these EXACT keys:
    {{
        "industry_tag": str,
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

    print("\nSending to Gemini...")
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        print("\n--- RAW JSON RESPONSE FROM GEMINI ---")
        print(response.text)
        print("-------------------------------------\n")
        
        data = json.loads(response.text)
        print(f"Parsed 'is_family_owned': {data.get('is_family_owned')}")
        print(f"Parsed 'owner_name': {data.get('owner_name')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_one_company()
