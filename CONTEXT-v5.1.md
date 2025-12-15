# PE Sourcing Engine v5.1 - Project Context File
**Date:** December 15, 2025  
**Current Version:** 5.1  
**Status:** Production Ready  
**Repository:** https://github.com/gpatkins/pe-sourcing-engine (Private)

---

## 🎯 Project Overview

**PE Sourcing Engine** is an automated Private Equity deal sourcing platform that discovers, enriches, and scores potential acquisition targets. Version 5.1 represents a major upgrade from a single-user tool to a multi-user SaaS platform.

**Primary Use Case:** Private equity firms use this to automatically discover family-owned businesses in specific industries/locations, enrich them with detailed data (revenue, ownership, contacts), and score them for buyability (0-100).

---

## 🏗️ System Architecture

### Tech Stack
- **Backend:** Python 3.14, FastAPI
- **Database:** PostgreSQL 15
- **Authentication:** JWT tokens (HTTP-only cookies)
- **Frontend:** Jinja2 templates, Tailwind CSS, Alpine.js
- **Deployment:** Docker Compose (multi-container)
- **Analytics:** Metabase
- **Reverse Proxy:** Caddy (automatic HTTPS)

### Key Components
1. **Discovery Module** (`etl/discover/`) - Google Places API to find companies
2. **Enrichment Module** (`enrich/`) - 11+ enrichers (domain, LinkedIn, owner, revenue, etc.)
3. **Scoring Module** (`etl/score/`) - Calculates buyability score (0-100)
4. **API/Dashboard** (`api/`) - FastAPI web interface
5. **Database** - PostgreSQL with companies, users, activity logs

---

## 📦 Current Deployment

### Development Environment (dg)
- **Server:** Fedora (10.55.55.55)
- **Location:** `/opt/pe-sourcing-engine/`
- **Service:** `pe-sourcing-gui.service` (systemd)
- **Python:** 3.14 in venv
- **Database:** PostgreSQL on host (not containerized)
- **Port:** 8000

### Docker Deployment (docker-dg)
- **Configuration:** `docker-compose.yml`
- **Services:** app, db, metabase, caddy (optional)
- **Installation:** Interactive `install.py` script
- **Status:** Tested, documented, ready for production

---

## 🔐 Version 5.1 Changes (Major Upgrade)

### Authentication System
**Files Created:**
- `api/auth.py` - JWT token management, password hashing, validation
- `api/dependencies.py` - FastAPI auth dependencies, role checks
- `api/models.py` - SQLAlchemy ORM models (User, ApiCredential, UserActivity)

**Database Schema:**
- `schema_v5.1.sql` - Migration script (adds users, api_credentials, user_activity tables)
- `schema.sql` - Base schema (companies table and core structure)
- **Run order:** schema.sql → schema_v5.1.sql

**Key Tables:**
- `users` - email, hashed_password, role (admin/user), is_active
- `api_credentials` - centralized API key storage (admin-managed)
- `user_activity` - audit log (logins, exports, user changes)
- `companies` - added `user_id` column for data isolation

### UI Templates (Tailwind CSS)
**New Pages:**
- `base.html` - Master template with navigation, user dropdown
- `login.html` - Login page
- `register.html` - User creation (admin-only)
- `profile.html` - User profile with password change
- `admin_users.html` - User management dashboard
- `admin_api_keys.html` - API key management
- `companies.html` - Export page (CSV/Excel)

**Updated Pages:**
- `dashboard.html` - Redesigned with modern Tailwind cards
- `discovery_queries.html` - Redesigned query manager

### Main Application Updates
**File:** `api/main.py` (completely rewritten)

**Authentication Routes:**
- `GET/POST /login` - Login with JWT cookie
- `GET /logout` - Clear auth cookie
- `GET/POST /register` - User creation (admin-only)
- `GET /profile` - User profile
- `POST /profile/update-name` - Update full name
- `POST /profile/change-password` - Change password

**Admin Routes:**
- `GET /admin/users` - User management page
- `POST /admin/users/toggle-status/{id}` - Activate/deactivate
- `POST /admin/users/reset-password/{id}` - Generate temp password
- `POST /admin/users/delete/{id}` - Delete user
- `GET /admin/api-keys` - API key management
- `POST /admin/api-keys/update/{id}` - Update API key
- `POST /admin/api-keys/toggle/{id}` - Enable/disable key

**Export Routes:**
- `GET /companies` - Export page with stats
- `POST /companies/export/csv` - CSV export (with filters)
- `POST /companies/export/excel` - Excel export (with filters)

**Filters:** all, top_scored (≥60), family_owned

### Database Compatibility (psycopg3)
**Updated Files:**
- `etl/utils/db.py` - psycopg2 → psycopg3 migration
- `enrich_companies.py` - cursor_factory → row_factory
- `etl/score/calculate_scores.py` - execute_batch → executemany

**Key Changes:**
- `import psycopg` (not psycopg2)
- `row_factory=dict_row` (not cursor_factory=RealDictCursor)
- Explicit `conn.commit()` calls added

### Dependencies Updated
**File:** `requirements.txt`

**New Dependencies:**
- `python-jose[cryptography]==3.3.0` - JWT tokens
- `passlib[bcrypt]==1.7.4` - Password hashing
- `bcrypt<5.0` - bcrypt backend (Python 3.14 compatible)
- `email-validator==2.1.0` - Email validation
- `itsdangerous==2.1.2` - CSRF tokens
- `psycopg[binary]==3.3.2` - PostgreSQL driver (psycopg3)
- `sqlalchemy==2.0.35` - ORM (upgraded for Python 3.14)
- `openpyxl==3.1.5` - Excel export
- `lxml==5.3.0` - XML parsing (Python 3.14 compatible)

---

## 🐳 Docker Configuration

### Files
- `Dockerfile` - Python 3.14-slim, installs dependencies, exposes 8000
- `docker-compose.yml` - Multi-service setup (db, app, metabase, caddy)
- `.dockerignore` - Excludes venv, logs, .git from build
- `.env.example` - Environment variable template
- `Caddyfile` - Reverse proxy config with auto-HTTPS
- `README-DOCKER.md` - Complete deployment guide
- `install.py` - Interactive installer with GitHub clone support

### Services
1. **db** (postgres:15-alpine) - Port 5432 (internal)
2. **app** (custom build) - Port 8000
3. **metabase** (metabase/metabase) - Port 3000
4. **caddy** (caddy:2-alpine) - Ports 80/443 (optional, profile: with-caddy)

### Volumes
- `postgres_data` - Database files (persistent)
- `metabase_data` - Metabase config (persistent)
- `app_data` - Application data (persistent)
- `caddy_data` - TLS certificates (persistent)
- `./config` - Application config (mounted)
- `./logs` - Application logs (mounted)

### Environment Variables
**Required:**
- `DB_USER`, `DB_PASS`, `DB_NAME` - PostgreSQL credentials
- `JWT_SECRET_KEY` - JWT signing secret (64-char hex)
- `CSRF_SECRET` - CSRF token secret (64-char hex)
- `GOOGLE_PLACES_API_KEY` - Google Places API
- `GOOGLE_GEMINI_API_KEY` - Google Gemini API
- `SERPER_API_KEY` - Serper.dev API

**Optional:**
- `AI_SERVER_URL` - External AI service
- `DOMAIN` - Domain for Caddy HTTPS

---

## 🔑 Default Credentials

**Admin Account:**
- Email: `admin@dealgenome.local`
- Password: `admin123`
- **⚠️ MUST BE CHANGED after first login!**

**Database (Development):**
- Host: `10.55.55.55`
- Port: `5432`
- Database: `pe_sourcing_db`
- User: `pe_sourcer`
- Password: (stored in `/opt/pe-sourcing-engine/config/secrets.env`)

---

## 📁 File Structure
```
/opt/pe-sourcing-engine/
├── api/
│   ├── __init__.py
│   ├── main.py                 # Main FastAPI app (v5.1 rewrite)
│   ├── auth.py                 # Auth utilities (NEW v5.1)
│   ├── dependencies.py         # Auth dependencies (NEW v5.1)
│   ├── models.py               # SQLAlchemy models (NEW v5.1)
│   └── templates/
│       ├── base.html           # Master template (NEW v5.1)
│       ├── login.html          # Login page (NEW v5.1)
│       ├── register.html       # Registration (NEW v5.1)
│       ├── profile.html        # User profile (NEW v5.1)
│       ├── admin_users.html    # User management (NEW v5.1)
│       ├── admin_api_keys.html # API key management (NEW v5.1)
│       ├── companies.html      # Export page (NEW v5.1)
│       ├── dashboard.html      # Dashboard (UPDATED v5.1)
│       └── discovery_queries.html # Discovery manager (UPDATED v5.1)
├── config/
│   ├── settings.yaml           # Pipeline configuration
│   └── secrets.env             # Environment secrets
├── enrich/                     # Enrichment modules
│   ├── domain.py
│   ├── about.py
│   ├── linkedin_finder.py
│   ├── owner_finder.py
│   ├── ai_classifier.py
│   ├── revenue.py
│   └── ... (11 total enrichers)
├── etl/
│   ├── discover/               # Google Places discovery
│   ├── score/                  # Scoring algorithm
│   └── utils/
│       ├── db.py               # Database utilities (UPDATED v5.1)
│       ├── logger.py
│       └── state_manager.py
├── logs/
│   └── pipeline.log
├── venv/                       # Python 3.14 virtual environment
├── schema.sql                  # Base database schema
├── schema_v5.1.sql            # v5.1 migration (users, auth)
├── requirements.txt            # Python dependencies (UPDATED v5.1)
├── run_pipeline.py             # Pipeline orchestrator
├── enrich_companies.py         # Enrichment script (UPDATED v5.1)
├── Dockerfile                  # Docker image (NEW)
├── docker-compose.yml          # Multi-service orchestration (NEW)
├── .dockerignore              # Docker build exclusions (NEW)
├── .env.example               # Environment template (NEW)
├── Caddyfile                  # Caddy config (NEW)
├── README-DOCKER.md           # Docker guide (NEW)
├── install.py                 # Interactive installer (UPDATED v5.1)
└── README.md                   # Main documentation
```

---

## 🔄 Pipeline Workflow

### 1. Discovery Phase
**Script:** `run_pipeline.py` → calls `etl.discover.google_places.discover()`

**Process:**
1. Reads queries from `config/settings.yaml`
2. Calls Google Places API for each query
3. Deduplicates by domain
4. Inserts into `companies` table with `user_id`
5. Sets `enrichment_status='pending'`

**Output:** Raw company records (name, address, phone, url)

### 2. Enrichment Phase
**Script:** `enrich_companies.py`

**Process:**
1. Fetches companies with `enrichment_status IN ('pending', 'partial')`
2. Runs 11 enrichers in sequence:
   - `DomainEnricher` - Extracts domain from URL
   - `AboutEnricher` - Scrapes website about page
   - `LinkedInFinder` - Finds LinkedIn company page
   - `EcommerceEnricher` - Detects e-commerce platforms
   - `IndustryEnricher` - Gets NAICS code
   - `FounderEnricher` - Finds founder/owner info
   - `NewsFinder` - Searches recent news
   - `AIClassifier` - Uses Gemini to classify industry
   - `OwnerFinder` - "Ghost hunting" to find owner name
   - `EmailFinder` - Scrapes contact emails
   - `RevenueEnricher` - Estimates revenue from employee count
3. Updates company record with enriched data
4. Sets `enrichment_status='complete'`

**Output:** Fully enriched company records (25+ fields)

### 3. Scoring Phase
**Script:** `etl/score/calculate_scores.py`

**Algorithm:**
```
Score (0-100) = Financial Size (30) + Quality (40) + Actionability (30) - Risk Penalty

Financial Size:
- Revenue $1-5M: +10 points
- Revenue $5-15M: +20 points
- Revenue >$15M: +30 points

Quality:
- Family owned: +20 points
- Franchise: -50 points (deal killer)
- B2B/Commercial focus: +20 points
- Residential only: +5 points

Actionability:
- Owner name found: +15 points
- LinkedIn found: +15 points

Risk:
- Any "ALERT" in risk_flags: -50 points
```

**Output:** `buyability_score` column updated (0-100)

---

## 🎯 User Roles & Permissions

### Admin Role
**Capabilities:**
- View all companies across all users
- Create/edit/delete users
- Reset user passwords
- Toggle user active/inactive status
- Manage API keys (view, update, enable/disable)
- View activity logs
- Export all data

**Access:**
- All routes
- `/admin/*` routes
- Global data view

### User Role
**Capabilities:**
- View only own companies
- Run pipeline (discover, enrich, score)
- Manage own discovery queries
- Export own data (CSV/Excel)
- Update own profile
- Change own password

**Restrictions:**
- Cannot access `/admin/*` routes
- Cannot view other users' companies
- Cannot manage API keys
- Cannot create users

---

## 🔒 Security Features

### Authentication
- JWT tokens (HS256 algorithm)
- 24-hour token expiration
- HTTP-only cookies (not accessible to JavaScript)
- Bcrypt password hashing (cost factor 12)
- Password requirements: min 8 chars, 1 number, 1 special char

### Authorization
- Role-based access control (RBAC)
- Route-level protection with FastAPI dependencies
- SQL-level data filtering (user_id WHERE clause)
- Admin-only routes protected with `require_admin()` dependency

### Audit Trail
- All user actions logged to `user_activity` table
- Activity types: LOGIN, LOGOUT, DISCOVERY_RUN, ENRICHMENT_RUN, EXPORT_DATA, API_KEY_UPDATE, USER_CREATED, USER_UPDATED, USER_DELETED, PASSWORD_CHANGED
- JSONB details field for flexible logging

### CSRF Protection
- CSRF tokens generated per form
- Validated on all state-changing operations
- Uses `itsdangerous` for secure token signing

### Self-Protection
- Admins cannot deactivate own account
- Admins cannot delete own account
- Prevents accidental lockout

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **No email notifications** - Password resets show temp password in browser (not emailed)
2. **No forgot password** - Must contact admin for reset
3. **No user groups/teams** - Only individual user isolation
4. **No custom permissions** - Only 2 roles (admin/user)
5. **No API tokens** - Only cookie-based auth (no API access)
6. **No rate limiting** - No protection against brute force
7. **No 2FA** - Single-factor authentication only

### Technical Debt
1. **No migration system** - Schema changes done via SQL files
2. **No database backups** - Must be done manually
3. **No automated tests** - All testing manual
4. **No CI/CD pipeline** - Manual deployment
5. **Hard-coded Metabase URL** - In templates (should be env var)

### Python 3.14 Compatibility
- All dependencies verified working with Python 3.14
- Required downgrades: `bcrypt<5.0` (version 5.0 incompatible)
- Required upgrades: `sqlalchemy>=2.0.35`, `lxml>=5.3.0`, `psycopg>=3.3.2`

---

## 📊 Database Schema Reference

### Core Tables

**companies** (main data table)
- `id` UUID PRIMARY KEY
- `name` TEXT NOT NULL
- `url` TEXT
- `phone`, `address`, `city`, `state`, `zip`, `country`
- `industry_tag`, `naics_code`, `customer_type`
- `revenue_estimate` NUMERIC
- `buyability_score` SMALLINT (0-100)
- `owner_name`, `owner_phone`, `founder_email`
- `linkedin_company_url`, `owner_linkedin_url`
- `is_family_owned`, `is_franchise` BOOLEAN
- `risk_flags` TEXT
- `enrichment_status` TEXT ('pending', 'partial', 'complete')
- `user_id` INT REFERENCES users(id) (NEW v5.1)
- `created_at`, `updated_at`, `last_enriched_at` TIMESTAMP

**users** (v5.1)
- `id` SERIAL PRIMARY KEY
- `email` VARCHAR(255) UNIQUE NOT NULL
- `hashed_password` VARCHAR(255) NOT NULL
- `full_name` VARCHAR(255)
- `role` VARCHAR(50) ('admin', 'user')
- `is_active` BOOLEAN
- `created_at`, `last_login` TIMESTAMP

**api_credentials** (v5.1)
- `id` SERIAL PRIMARY KEY
- `service_name` VARCHAR(100) UNIQUE (google_places, google_gemini, serper)
- `api_key` TEXT NOT NULL
- `is_active` BOOLEAN
- `updated_at` TIMESTAMP
- `updated_by` INT REFERENCES users(id)

**user_activity** (v5.1)
- `id` SERIAL PRIMARY KEY
- `user_id` INT REFERENCES users(id) ON DELETE CASCADE
- `activity_type` VARCHAR(100)
- `details` JSONB
- `created_at` TIMESTAMP

**Indexes:**
- `idx_companies_user_id` ON companies(user_id)
- `idx_users_email` ON users(email)
- `idx_user_activity_user_id` ON user_activity(user_id)

---

## 🚀 Deployment Instructions

### Development (dg server)
```bash
# Already deployed and running
ssh gpatkins@10.55.55.55
cd /opt/pe-sourcing-engine
sudo systemctl status pe-sourcing-gui.service

# Restart after changes
sudo systemctl restart pe-sourcing-gui.service

# View logs
sudo journalctl -u pe-sourcing-gui.service -f
```

### Docker (Production)
```bash
# Clone repository (requires GitHub access)
git clone https://github.com/gpatkins/pe-sourcing-engine.git
cd pe-sourcing-engine

# Run interactive installer
python3 install.py

# OR manual setup
cp .env.example .env
nano .env  # Configure
docker compose up -d

# Management commands
docker compose logs -f app
docker compose restart app
docker compose down
```

---

## 🔧 Common Tasks

### Add a New User (Admin)
1. Login as admin
2. Click user dropdown → Admin → Users
3. Click "Create User"
4. Fill in email, password, role
5. Submit

### Reset User Password (Admin)
1. Admin → Users
2. Find user, click "Reset Password"
3. Copy temporary password
4. Share with user securely
5. User must change on first login

### Update API Keys (Admin)
1. Admin → API Keys
2. Paste new key in field
3. Click "Update Key"

### Export Companies (Any User)
1. Navigate to Companies page
2. Choose filter (all, top_scored, family_owned)
3. Click "Export as CSV" or "Export as Excel"
4. File downloads with timestamp

### Run Pipeline
1. Dashboard → Click pipeline step button
2. OR via CLI: `docker compose exec app python run_pipeline.py`

### View Logs
- **In Browser:** Dashboard → Logs (last 200 lines)
- **In Terminal:** `tail -f /opt/pe-sourcing-engine/logs/pipeline.log`
- **Docker:** `docker compose logs -f app`

---

## 📈 Future Roadmap (v5.2+)

### Potential Features
1. **Email notifications** - Password resets, export completion
2. **Forgot password** - Self-service password reset
3. **User groups/teams** - Multi-tenant with org structure
4. **Custom permissions** - Granular access control
5. **API tokens** - RESTful API access
6. **Rate limiting** - Brute force protection
7. **2FA/MFA** - Enhanced security
8. **Scheduled exports** - Automated data delivery
9. **Webhook integrations** - External system notifications
10. **Advanced analytics** - Built-in dashboards (not just Metabase)
11. **Bulk operations** - Mass user actions
12. **Companies table view** - In-app company browsing (currently Metabase only)
13. **SSO/SAML** - Enterprise authentication
14. **Audit log viewer** - Admin activity review UI

---

## 🆘 Troubleshooting

### Login Issues
**Problem:** "Invalid email or password"
**Solution:** 
1. Verify email is `admin@dealgenome.local` (default)
2. Password is `admin123` (default)
3. If changed and forgotten, reset in database:
```bash
psql -U pe_sourcer -d pe_sourcing_db -h 10.55.55.55
UPDATE users SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRU8uXi' WHERE email = 'admin@dealgenome.local';
```

### Database Connection Errors
**Problem:** "Could not connect to database"
**Solution:**
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify credentials in `config/secrets.env`
3. Test connection: `psql -U pe_sourcer -d pe_sourcing_db -h 10.55.55.55`

### Docker Build Failures
**Problem:** Build fails with dependency errors
**Solution:**
1. Ensure Python 3.14 in Dockerfile
2. Clear cache: `docker compose build --no-cache`
3. Check requirements.txt matches documented versions

### Export Not Working
**Problem:** Internal server error on export
**Solution:**
1. Check logs: `docker compose logs app`
2. Verify openpyxl installed: `pip list | grep openpyxl`
3. Check database columns match export SQL query

### Permission Denied Errors
**Problem:** Cannot access certain pages
**Solution:**
1. Verify user role in database: `SELECT email, role FROM users;`
2. Ensure JWT token valid (logout/login)
3. Check if user is active: `SELECT is_active FROM users WHERE email = 'user@example.com';`

---

## 📞 Support & Contact

**Repository:** https://github.com/gpatkins/pe-sourcing-engine (Private)  
**Maintainer:** Gabriel Atkinson  
**Email:** gpatkins@[domain]  
**Version:** 5.1  
**Last Updated:** December 15, 2025

---

## ✅ Pre-Flight Checklist (For New Developer)

Before starting work:
- [ ] Clone repository (requires GitHub access)
- [ ] Install Python 3.14
- [ ] Install Docker & Docker Compose
- [ ] Read README.md and README-DOCKER.md
- [ ] Review schema.sql and schema_v5.1.sql
- [ ] Understand authentication flow (api/auth.py, api/dependencies.py)
- [ ] Familiarize with FastAPI structure (api/main.py)
- [ ] Test Docker deployment with install.py
- [ ] Login with default credentials and change password
- [ ] Create test user and verify data isolation
- [ ] Run full pipeline (discover → enrich → score)
- [ ] Test export functionality
- [ ] Review activity logs in database

---

**END OF CONTEXT FILE**
