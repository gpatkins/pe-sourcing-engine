# PE Sourcing Engine - Documentation

## Overview
DealGenome is an automated deal sourcing platform designed for Private Equity. It discovers companies via Google Maps, enriches them with AI analysis, finds owner contact information, and scores them based on acquisition suitability ("Buyability Score").

## Version
**Current Version:** 5.8

## System Architecture
* **Discovery:** Google Places API (Finds target companies)
* **Enrichment:** Custom scrapers + Gemini AI (Analyzes websites and extracts data)
* **Risk Intelligence:** Serper Google News API (Checks for lawsuits/bankruptcy)
* **Database:** PostgreSQL (Stores all enriched data)
* **UI:** FastAPI Dashboard (Port 8000) & Metabase Analytics (Port 3000)

## Key Features
* **AI-Powered Classification:** Industry tags, NAICS codes, revenue models
* **Owner Discovery:** "Ghost hunting" to find owner names and contact info
* **Risk Scanning:** Automated news monitoring for red flags
* **Multi-User System:** JWT authentication with role-based access control
* **Scale Generator:** Batch query generation across 80+ US cities
* **Buyability Scoring:** 0-100 score based on financial size, ownership structure, and actionability

## Core Scripts & Modules
* `etl/discover/google_places.py` - Discovery engine (Google Maps search with deduplication)
* `enrich_companies.py` - Enrichment orchestrator (runs all enrichment modules)
* `etl/score/calculate_scores.py` - Scoring algorithm (0-100 buyability score)
* `api/main.py` - FastAPI backend (dashboard and API endpoints)

## Two Deployment Modes

### Source / Development Server (dg)
- **Location:** `/opt/pe-sourcing-engine/`
- **OS:** Fedora
- **Runtime:** systemd service (`pe-sourcing-gui.service`)
- **Database:** PostgreSQL on 10.55.55.55
- **Docker:** ❌ Not used
- **Purpose:** Primary development and testing environment

### Production Deployment (docker-dg)
- **Runtime:** Docker Compose
- **Docker:** ✅ Required
- **Purpose:** Easy deployment on new machines
- **Documentation:** See `docker-README.md`

## Docker Deployment Files

**For docker-dg deployments only** (NOT used on source server):

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Container orchestration |
| `Dockerfile` | Application image definition |
| `Caddyfile` | HTTPS reverse proxy configuration |
| `.dockerignore` | Docker build exclusions |
| `docker-install.py` | Interactive deployment installer |
| `docker-manage.py` | Container management CLI |
| `docker-README.md` | Complete Docker documentation |

**Quick Docker Commands:**
```bash
# Deploy with installer
python3 docker-install.py

# Manual deployment
docker compose up -d

# View logs
docker compose logs -f app

# Stop services
docker compose down
```

See `docker-README.md` for complete Docker deployment guide.

## Database Schema
Authoritative schema documentation: `schema/README.md`

**Core Tables:**
* `companies` - Primary company data (50+ fields)
* `users` - Authentication and user management
* `user_activity` - Audit log
* `scale_generator_config` - City/state configuration for discovery
* `signals_job_postings` - Job posting tracking (future use)
* `signals_revenue_history` - Revenue tracking (future use)

## Development Workflow

### Service Management (Source Server)
```bash
# Restart service
sudo systemctl restart pe-sourcing-gui.service

# View status
sudo systemctl status pe-sourcing-gui.service

# View logs
sudo journalctl -u pe-sourcing-gui.service -f
```

### Git Workflow
```bash
cd /opt/pe-sourcing-engine

# Check status
git status

# Stage changes
git add <files>

# Commit
git commit -m "descriptive message"

# Push
git push origin main
```

## API Keys Required

Configuration file: `config/secrets.env`

**Required APIs:**
* `GOOGLE_PLACES_API_KEY` - Company discovery
* `GEMINI_API_KEY` - AI classification and analysis
* `SERPER_API_KEY` - News and risk intelligence

**Database:**
* `DB_USER`, `DB_PASS`, `DB_NAME` - PostgreSQL credentials

**Authentication:**
* `JWT_SECRET_KEY` - JWT token signing
* `CSRF_SECRET` - CSRF protection

## Troubleshooting

### View Pipeline Logs
```bash
# Real-time
tail -f /opt/pe-sourcing-engine/logs/pipeline.log

# Via dashboard
# Navigate to: http://10.55.55.55:8000/logs
```

### Restart Application
```bash
# Development server (dg)
sudo systemctl restart pe-sourcing-gui.service

# Docker deployment
docker compose restart app
```

### Database Access
```bash
# Connect to database
psql -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db

# Useful queries
SELECT COUNT(*) FROM companies;
SELECT enrichment_status, COUNT(*) FROM companies GROUP BY enrichment_status;
```

### Common Issues

**Dashboard not loading:**
```bash
# Check service status
sudo systemctl status pe-sourcing-gui.service

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000
```

**Pipeline not discovering companies:**
- Verify `GOOGLE_PLACES_API_KEY` in `config/secrets.env`
- Check discovery queries in dashboard
- Review logs for API errors

**Enrichment failures:**
- Check `GEMINI_API_KEY` and `SERPER_API_KEY`
- Verify network connectivity
- Check API rate limits

## Project Structure
```
/opt/pe-sourcing-engine/
├── api/                    # FastAPI application
├── etl/                    # ETL pipeline modules
│   ├── discover/          # Discovery scripts
│   ├── score/             # Scoring algorithms
│   └── utils/             # Shared utilities
├── enrich/                # Enrichment modules
├── schema/                # Database schema
│   ├── current.sql        # Authoritative schema
│   └── README.md          # Schema documentation
├── config/                # Configuration files
│   ├── settings.yaml      # Application settings
│   └── secrets.env        # API keys (gitignored)
├── logs/                  # Application logs
├── docker-compose.yml     # Docker orchestration
├── Dockerfile             # Docker image
├── docker-install.py      # Docker installer
├── docker-manage.py       # Docker management CLI
├── docker-README.md       # Docker documentation
└── requirements.txt       # Python dependencies
```

## Technology Stack

**Backend:**
- Python 3.13
- FastAPI (API framework)
- PostgreSQL (Database)
- JWT Authentication
- Jinja2 Templates

**AI & APIs:**
- Google Gemini 2.5 Flash (AI analysis)
- Google Places API (Company discovery)
- Serper.dev (News/risk analysis)
- DuckDuckGo Search (LinkedIn discovery)

**Infrastructure:**
- systemd (Development server)
- Docker Compose (Production deployment)
- Caddy (HTTPS reverse proxy)
- Metabase (Analytics)

## Contributing

This is a private repository. All development happens on the source server (dg) and is deployed to docker-dg after validation.

**Development Workflow:**
1. Make changes on dg server
2. Test thoroughly
3. Commit and push to GitHub
4. Deploy to docker-dg when ready

## Security Notes

- Default admin credentials: `admin@dealgenome.local` / `admin123`
- ⚠️ **Change admin password immediately after deployment**
- API keys stored in `config/secrets.env` (gitignored)
- JWT tokens expire after 24 hours
- Passwords hashed with bcrypt

## Quick Install

For fresh Fedora servers, use the installer scripts:
```bash
# Clone the repository
git clone https://github.com/gpatkins/pe-sourcing-engine.git
cd pe-sourcing-engine

# Run the main installer
./installer/install-dealgenome.sh

# (Optional) Install Metabase analytics
./installer/install-metabase.sh
```

The installer will:
- Install PostgreSQL locally and prompt for database password
- Set up Python 3.13 virtual environment
- Configure systemd service (auto-starts on boot)
- Optionally set up Caddy for HTTPS

See `installer/` directory for details.

## Support & Contact

**Developer:** Gabriel Atkinson  
**Repository:** https://github.com/gpatkins/pe-sourcing-engine (private)  
**Version:** 5.5  
**Last Updated:** December 2025
