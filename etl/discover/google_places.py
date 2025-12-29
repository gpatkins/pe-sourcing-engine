from __future__ import annotations
import os
import time
import uuid
import requests
import yaml
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from etl.utils.db import execute, fetch_one_dict
from etl.utils.state_manager import should_stop, set_running, clear_running
from etl.utils.logger import setup_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "config", "settings.yaml")
ENV_PATH = os.path.join(BASE_DIR, "config", "secrets.env")

# Use override=True so secrets.env takes precedence over Docker env vars
# This allows admin dashboard updates to work in Docker
load_dotenv(ENV_PATH, override=True)
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

logger = setup_logger("discovery")


def search_places_new(text_query: str, page_token: Optional[str] = None, region_code: Optional[str] = None) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.primaryType,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber"
    }
    
    body = {"textQuery": text_query}
    if region_code: 
        body["regionCode"] = region_code
    if page_token: 
        body["pageToken"] = page_token
    
    resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()


def generate_deterministic_id(website: str | None, name: str, address: str | None) -> str:
    if website:
        try:
            parsed = urlparse(website)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if domain:
                return str(uuid.uuid5(uuid.NAMESPACE_URL, domain))
        except:
            pass
    unique_str = f"{(name or '').lower()}|{(address or '').lower()}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))


def get_admin_user_id() -> int:
    """Get the admin user ID (or first user if no admin exists)."""
    result = fetch_one_dict("SELECT id FROM users WHERE role = 'admin' ORDER BY created_at LIMIT 1")
    if result:
        return result['id']
    # Fallback to first user if no admin
    result = fetch_one_dict("SELECT id FROM users ORDER BY created_at LIMIT 1")
    if result:
        return result['id']
    raise RuntimeError("No users found in database")


def upsert_company(place: Dict[str, Any], user_id: int) -> None:
    name = (place.get("displayName") or {}).get("text")
    address = place.get("formattedAddress")
    website = place.get("websiteUri")
    phone = place.get("nationalPhoneNumber")
    rating = place.get("rating")
    reviews = place.get("userRatingCount")
    industry_tag = place.get("primaryType")

    city = state = zip_code = country = None
    if address and "," in address:
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 3:
            city = parts[-3] if len(parts) > 3 else parts[-2]
            state_zip_part = parts[-1]
            tokens = state_zip_part.split()
            if len(tokens) >= 1: state = tokens[0]
            if len(tokens) >= 2: zip_code = tokens[1]
            country = "USA"

    cid = generate_deterministic_id(website, name, address)
    
    sql = """
        INSERT INTO companies (
            id, name, url, phone, address, city, state, zip, country,
            industry_tag, google_rating, google_reviews,
            date_added, created_at, updated_at, enrichment_status, user_id
        )
        VALUES (
            %(id)s, %(name)s, %(url)s, %(phone)s, %(address)s,
            %(city)s, %(state)s, %(zip)s, %(country)s,
            %(industry_tag)s, %(rating)s, %(reviews)s,
            CURRENT_DATE, NOW(), NOW(), 'pending', %(user_id)s
        )
        ON CONFLICT (id) DO UPDATE SET
            updated_at = NOW(),
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            zip = EXCLUDED.zip,
            industry_tag = COALESCE(EXCLUDED.industry_tag, companies.industry_tag),
            google_rating = COALESCE(EXCLUDED.google_rating, companies.google_rating),
            google_reviews = COALESCE(EXCLUDED.google_reviews, companies.google_reviews);
    """
    
    params = {
        "id": cid,
        "name": name or "Unknown",
        "url": website,
        "phone": phone,
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
        "industry_tag": industry_tag,
        "rating": rating,
        "reviews": reviews,
        "user_id": user_id
    }
    
    execute(sql, params)


def run_discovery(user_id: Optional[int] = None):
    try:
        set_running("Discovery")
        if user_id is None:
            user_id = get_admin_user_id()
            logger.info(f"No user_id provided, using admin: {user_id}")
        else:
            logger.info(f"Discoveries will be assigned to user_id: {user_id}")
            
        if not os.path.exists(SETTINGS_PATH): 
            logger.info("No settings.yaml found - skipping discovery")
            return
            
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            queries = yaml.safe_load(f).get("discovery", {}).get("queries", [])
            
        logger.info(f"Loaded {len(queries)} queries")
        
        for q in queries:
            if should_stop():
                logger.info("STOP REQUESTED. Halting.")
                break
                
            text_query = q.get("text_query")
            limit = int(q.get("limit", 20))
            if not text_query: 
                continue
                
            logger.info(f"Searching: {text_query} (Max: {limit})")
            page_token = None
            count = 0
            
            while True:
                if should_stop(): 
                    break
                if count >= limit: 
                    break
                    
                try:
                    data = search_places_new(text_query, page_token=page_token, region_code=q.get("region_code", "US"))
                    places = data.get("places", [])
                    if not places: 
                        break
                        
                    remaining = limit - count
                    batch_to_process = places[:remaining]
                    
                    for place in batch_to_process:
                        upsert_company(place, user_id)
                        
                    added = len(batch_to_process)
                    count += added
                    logger.info(f"Added {added} places (Total: {count}/{limit})")
                    
                    if count >= limit: 
                        break
                        
                    page_token = data.get("nextPageToken")
                    if not page_token: 
                        break
                        
                    time.sleep(2)  # Rate limit respect
                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    if hasattr(e, 'response'):
                        logger.error(f"Response text: {e.response.text}")
                    break
    finally:
        clear_running()


main = run_discovery

if __name__ == "__main__":
    main()
