# PE Sourcing Engine - Current State

**Last Updated:** December 15, 2025

**Updated By:** Gabriel Atkinson

## ✅ What's Working

### Development Environment (dg - 10.55.55.55)

- ✅ FastAPI app running on port 8000
- ✅ PostgreSQL database operational
- ✅ All v5.1 features deployed and tested
- ✅ Systemd service running (pe-sourcing-gui.service)
- ✅ Authentication system working
- ✅ User management working
- ✅ API key management working
- ✅ CSV/Excel exports working
- ✅ Pipeline execution working (discover, enrich, score)

### Docker Deployment

- ✅ Dockerfile created and tested
- ✅ docker-compose.yml configured
- ✅ [install.py](http://install.py/) interactive installer ready
- ✅ All documentation complete
- ✅ Files committed to GitHub (private repo)

### Code Quality

- ✅ Python 3.14 compatible
- ✅ All dependencies up to date
- ✅ psycopg3 migration complete
- ✅ No known bugs

## ⚠️ Known Issues

### Minor Issues

- ⚠️ Metabase URL hard-coded in templates (should be env var)
- ⚠️ No email notifications for password resets
- ⚠️ No forgot password functionality
- ⚠️ No rate limiting on login attempts

### Technical Debt

- ⚠️ No automated tests
- ⚠️ No CI/CD pipeline
- ⚠️ No database migration system (using SQL files)
- ⚠️ No automated backups

## 🚫 What's NOT Working

### Not Implemented (Future Features)

- ❌ Email notifications
- ❌ 2FA/MFA
- ❌ API token authentication
- ❌ User groups/teams
- ❌ Custom permissions
- ❌ In-app companies table (currently Metabase only)
- ❌ Webhook integrations
- ❌ SSO/SAML

### Not Tested

- ❌ Docker deployment on fresh server (created but not tested)
- ❌ Caddy HTTPS with real domain
- ❌ High-volume user scenarios
- ❌ Concurrent pipeline execution

## 📊 System Status

### Services Status

```bash
# Check on dg server
sudo systemctl status pe-sourcing-gui.service  # Should be: active (running)
sudo systemctl status postgresql              # Should be: active (running)

```

### Database Status

```bash
# Connect to database
psql -U pe_sourcer -d pe_sourcing_db -h 10.55.55.55

# Check user count
SELECT COUNT(*) FROM users;  # Should be: 1+ (at least admin)

# Check company count
SELECT COUNT(*) FROM companies;  # Varies based on discovery runs

```

### Git Status

```bash
cd /opt/pe-sourcing-engine
git status  # Should be: clean working tree (if not, pending changes)
git log --oneline -5  # See recent commits

```

### Last Known Good State

- **Commit:** [Run `git log --oneline -1` to see]
- **Date:** December 15, 2025
- **Version:** 5.1
- **Status:** Production ready

## 🔧 Configuration

### Environment Files

- `/opt/pe-sourcing-engine/config/secrets.env` - API keys and DB credentials
- `/opt/pe-sourcing-engine/config/settings.yaml` - Pipeline configuration
- `/opt/pe-sourcing-engine/.env` - Docker environment (if using Docker)

### Active API Keys

- Google Places: [Check admin dashboard or secrets.env]
- Google Gemini: [Check admin dashboard or secrets.env]
- Serper: [Check admin dashboard or secrets.env]

### Users

- Admin: admin@dealgenome.local (active)
- Other users: [Check via Admin > Users page]

## 🐛 Recent Bugs Fixed

- ✅ CSV/Excel export column mismatch (Dec 12)
- ✅ psycopg3 cursor compatibility (Dec 12)
- ✅ Dashboard template styling (Dec 12)
- ✅ Discovery queries page styling (Dec 12)

## 📝 Recent Changes

- **Dec 15:** Added Docker deployment files
- **Dec 15:** Created context documentation
- **Dec 12:** Completed v5.1 authentication system
- **Dec 12:** Migrated to psycopg3

## 🎯 Active Development

**Current Focus:** None - v5.1 complete and stable

**Blocked On:** Nothing

**Waiting For:** Nothing

---

## 📞 Quick Commands Reference

### Development Server (dg)

```bash
# SSH to server
ssh gpatkins@10.55.55.55

# Navigate to project
cd /opt/pe-sourcing-engine

# Restart service
sudo systemctl restart pe-sourcing-gui.service

# View logs
sudo journalctl -u pe-sourcing-gui.service -f

# Database access
psql -U pe_sourcer -d pe_sourcing_db -h 10.55.55.55

```

### Docker Commands

```bash
# Build
docker compose build

# Start all services
docker compose up -d

# Start with Caddy
docker compose --profile with-caddy up -d

# View logs
docker compose logs -f app

# Stop all
docker compose down

# Restart app only
docker compose restart app

```

### Git Commands
# Check status
git status

# Pull latest
git pull origin main

# Commit changes
git add .
git commit -m "Description"
git push origin main

# View history
git log --oneline -10
