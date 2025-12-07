# PE Sourcing Engine - Documentation

## Overview
This is an automated deal sourcing platform designed for Private Equity. It scrapes Google Maps for companies, enriches them with AI analysis, finds owner contact info, and scores them based on "Buyability."

## System Architecture
* **Discovery:** Google Places API (Finds targets).
* **Enrichment:** Custom scrapers + Gemini AI (Analyzes websites).
* **Risk:** Serper Google News API (Checks for lawsuits/bankruptcy).
* **Database:** PostgreSQL (Stores all data).
* **UI:** FastAPI Dashboard (Port 8000) & Metabase (Port 3000).

## Scripts & Modules
* `etl/discover/google_places.py`: The search engine. Deduplicates by domain.
* `enrich_companies.py`: The main orchestrator. Runs all enrichment modules.
* `etl/score/calculate_scores.py`: Applies the 0-100 Buyability Score.
* `api/main.py`: The backend for the Web Dashboard.

## Troubleshooting
* **Logs:** Select Option 2 in the CLI Menu to see live logs.
* **Restarts:** If the dashboard freezes, use Option 3 to restart containers.
* **Config:** Use Option 10 to edit API keys (Google, Gemini, Serper).

## Developer
Developed by Gabriel Atkinson.
