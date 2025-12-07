from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from etl.utils.state_manager import get_current_state, request_stop
from etl.utils.db import get_connection

# Pipeline Imports
try:
    from run_pipeline import run_discover, run_enrich, run_score
except ImportError:
    def run_discover(): pass
    def run_enrich(): pass
    def run_score(): pass

# --- CONFIG & CITIES ---
US_CITIES = [
    ("Birmingham", "AL"), ("Anchorage", "AK"), ("Phoenix", "AZ"), ("Little Rock", "AR"),
    ("Los Angeles", "CA"), ("Denver", "CO"), ("Bridgeport", "CT"), ("Wilmington", "DE"),
    ("Jacksonville", "FL"), ("Atlanta", "GA"), ("Honolulu", "HI"), ("Boise", "ID"),
    ("Chicago", "IL"), ("Indianapolis", "IN"), ("Des Moines", "IA"), ("Wichita", "KS"),
    ("Louisville", "KY"), ("New Orleans", "LA"), ("Portland", "ME"), ("Baltimore", "MD"),
    ("Boston", "MA"), ("Detroit", "MI"), ("Minneapolis", "MN"), ("Jackson", "MS"),
    ("Kansas City", "MO"), ("Billings", "MT"), ("Omaha", "NE"), ("Las Vegas", "NV"),
    ("Manchester", "NH"), ("Newark", "NJ"), ("Albuquerque", "NM"), ("New York", "NY"),
    ("Charlotte", "NC"), ("Fargo", "ND"), ("Columbus", "OH"), ("Oklahoma City", "OK"),
    ("Portland", "OR"), ("Philadelphia", "PA"), ("Providence", "RI"), ("Charleston", "SC"),
    ("Sioux Falls", "SD"), ("Nashville", "TN"), ("Houston", "TX"), ("Salt Lake City", "UT"),
    ("Burlington", "VT"), ("Virginia Beach", "VA"), ("Seattle", "WA"), ("Charleston", "WV"),
    ("Milwaukee", "WI"), ("Cheyenne", "WY")
]

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
ENV_PATH = BASE_DIR / "config" / "secrets.env"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"

load_dotenv(ENV_PATH)

def get_admin_creds() -> tuple[str, str]:
    user = os.getenv("ADMIN_USER", "admin")
    password = os.getenv("ADMIN_PASS", "changeme123")
    return user, password

app = FastAPI(title="PE Sourcing Engine Control Panel")
templates = Jinja2Templates(directory="api/templates")
security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    expected_user, expected_pass = get_admin_creds()
    username_correct = hmac.compare_digest(credentials.username, expected_user)
    password_correct = hmac.compare_digest(credentials.password, expected_pass)
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- SETTINGS HELPERS ---
def load_settings() -> Dict[str, Any]:
    if not CONFIG_PATH.exists(): return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_settings(settings: Dict[str, Any]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False)

def get_discovery_queries() -> List[Dict[str, Any]]:
    settings = load_settings()
    discovery = settings.get("discovery", {})
    queries = discovery.get("queries", [])
    return queries

def update_discovery_queries(queries: List[Dict[str, Any]]) -> None:
    settings = load_settings()
    if "discovery" not in settings: settings["discovery"] = {}
    settings["discovery"]["queries"] = queries
    save_settings(settings)

# --- STATUS & STATS ---
def get_dashboard_stats() -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Total Discovered (All companies)
        cur.execute("SELECT COUNT(*) FROM companies;")
        total = cur.fetchone()[0]
        
        # 2. Fully Enriched (Completed)
        cur.execute("SELECT COUNT(*) FROM companies WHERE enrichment_status = 'complete';")
        enriched = cur.fetchone()[0]
        
        # 3. Pending Enrichment (Queue)
        cur.execute("SELECT COUNT(*) FROM companies WHERE enrichment_status IN ('pending', 'partial');")
        pending = cur.fetchone()[0]
        
        # 4. Scored Companies
        cur.execute("SELECT COUNT(*) FROM companies WHERE buyability_score IS NOT NULL;")
        scored = cur.fetchone()[0]

        # 5. Risk Alerts
        # Assuming we check risk_flags column if it exists, otherwise 0
        try:
            cur.execute("SELECT COUNT(*) FROM companies WHERE risk_flags LIKE 'ALERT%';")
            risks = cur.fetchone()[0]
        except:
            risks = 0
        
        return {
            "discovered_count": total,
            "enriched_count": enriched,
            "pending_count": pending,
            "scored_count": scored,
            "risk_count": risks
        }
    except:
        return {"discovered_count": 0, "enriched_count": 0, "pending_count": 0, "scored_count": 0, "risk_count": 0}
    finally:
        conn.close()

# --- API ROUTES ---
@app.get("/api/status")
def get_pipeline_status(user: str = Depends(require_auth)):
    current_job = get_current_state() # idle, Discovery, Enrichment
    stats = get_dashboard_stats()
    
    return JSONResponse({
        "status": current_job, 
        "stats": stats
    })

@app.post("/api/stop")
def stop_pipeline(user: str = Depends(require_auth)):
    request_stop()
    return JSONResponse({"status": "stopping"})

@app.get("/api/logs/stream")
def get_logs_stream(user: str = Depends(require_auth)):
    if not LOG_FILE.exists():
        return JSONResponse({"lines": ["Waiting for logs..."]})
    with LOG_FILE.open("r", encoding="utf-8") as f:
        # Read all lines
        lines = f.readlines()
        # Return last 50
        last_lines = [line.rstrip() for line in lines[-50:]]
    return JSONResponse({"lines": last_lines})

# --- UI ROUTES ---
@app.get("/")
def dashboard(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": get_dashboard_stats()})

@app.get("/logs")
def view_logs(request: Request, user: str = Depends(require_auth)):
    lines = []
    if LOG_FILE.exists():
        with LOG_FILE.open("r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()[-200:]]
    return templates.TemplateResponse("logs.html", {"request": request, "lines": lines})

@app.get("/discovery-queries")
def discovery_queries_page(request: Request, user: str = Depends(require_auth)):
    queries = get_discovery_queries()
    return templates.TemplateResponse("discovery_queries.html", {"request": request, "queries": list(enumerate(queries))})

@app.post("/discovery-queries/add")
def add_discovery_query(
    label: str = Form(...),
    text_query: str = Form(...),
    region_code: str = Form("US"),
    limit: int = Form(20),
    user: str = Depends(require_auth),
):
    queries = get_discovery_queries()
    queries.append({
        "label": label.strip() or text_query[:40],
        "text_query": text_query.strip(),
        "region_code": region_code.strip() or "US",
        "limit": limit
    })
    update_discovery_queries(queries)
    return RedirectResponse(url="/discovery-queries", status_code=303)

@app.post("/discovery-queries/delete/{index}")
def delete_discovery_query(index: int, user: str = Depends(require_auth)):
    queries = get_discovery_queries()
    if 0 <= index < len(queries):
        queries.pop(index)
        update_discovery_queries(queries)
    return RedirectResponse(url="/discovery-queries", status_code=303)

@app.post("/discovery-queries/generate")
def generate_queries(
    base_query: str = Form(...),
    limit: int = Form(20),
    user: str = Depends(require_auth),
):
    queries = get_discovery_queries()
    base = base_query.strip()
    for city, state in US_CITIES:
        new_text = f"{base} in {city}, {state}"
        label = f"gen_{state}_{city}"
        queries.append({
            "label": label,
            "text_query": new_text,
            "region_code": "US",
            "limit": limit
        })
    update_discovery_queries(queries)
    return RedirectResponse(url="/discovery-queries", status_code=303)

@app.post("/discovery-queries/delete-all")
def delete_all_queries(user: str = Depends(require_auth)):
    update_discovery_queries([])
    return RedirectResponse(url="/discovery-queries", status_code=303)

def _run_step(step: str):
    if step == "discover": run_discover()
    elif step == "enrich": run_enrich()
    elif step == "score": run_score()
    elif step == "full":
        run_discover()
        run_enrich()
        run_score()

@app.post("/run/{step}")
def run_step(step: str, background_tasks: BackgroundTasks, user: str = Depends(require_auth)):
    if step in {"discover", "enrich", "score", "full"}:
        background_tasks.add_task(_run_step, step)
    return RedirectResponse(url="/", status_code=303)
