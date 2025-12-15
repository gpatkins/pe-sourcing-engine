# PE Sourcing Engine v5.1 - Docker Deployment Guide

Complete containerized deployment of the PE Sourcing Engine with PostgreSQL, FastAPI, and Metabase.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/gpatkins/pe-sourcing-engine.git
cd pe-sourcing-engine
```

2. **Create environment file:**
```bash
cp .env.example .env
nano .env  # Edit with your values
```

3. **Generate secrets:**
```bash
# JWT Secret
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))" >> .env

# CSRF Secret
python3 -c "import secrets; print('CSRF_SECRET=' + secrets.token_hex(32))" >> .env
```

4. **Start the services:**
```bash
# Without Caddy (HTTP only)
docker-compose up -d

# With Caddy (HTTPS)
docker-compose --profile with-caddy up -d
```

5. **Access the application:**
- Dashboard: http://localhost:8000
- Metabase: http://localhost:3000

6. **Login with default credentials:**
- Email: `admin@dealgenome.local`
- Password: `admin123`
- **⚠️ Change this password immediately!**

---

## 📦 Services

### Application (Port 8000)
- FastAPI dashboard
- JWT authentication
- User management
- Pipeline execution
- CSV/Excel exports

### PostgreSQL (Internal)
- Database storage
- User data
- Company data
- Activity logs

### Metabase (Port 3000)
- Data analytics
- Custom dashboards
- SQL queries
- Visualizations

### Caddy (Ports 80/443)
- Reverse proxy
- Automatic HTTPS
- Security headers
- Access logging

---

## 🔧 Configuration

### Environment Variables

**Required:**
- `DB_USER` - PostgreSQL username
- `DB_PASS` - PostgreSQL password
- `DB_NAME` - Database name
- `JWT_SECRET_KEY` - JWT signing secret
- `CSRF_SECRET` - CSRF token secret

**API Keys (Required for pipeline):**
- `GOOGLE_PLACES_API_KEY` - Google Places API
- `GOOGLE_GEMINI_API_KEY` - Google Gemini API
- `SERPER_API_KEY` - Serper.dev API

**Optional:**
- `AI_SERVER_URL` - External AI service
- `DOMAIN` - Domain for Caddy HTTPS

### Volumes

**Persistent Data:**
- `postgres_data` - Database files
- `metabase_data` - Metabase configuration
- `app_data` - Application data
- `caddy_data` - TLS certificates
- `caddy_config` - Caddy configuration

**Mounted:**
- `./config` - Application configuration
- `./logs` - Application logs

---

## 🛠️ Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f metabase
```

### Restart Service
```bash
docker-compose restart app
```

### Execute Commands in Container
```bash
# Access app shell
docker-compose exec app bash

# Run pipeline manually
docker-compose exec app python run_pipeline.py
```

### Database Access
```bash
# PostgreSQL shell
docker-compose exec db psql -U pe_sourcer -d pe_sourcing_db

# Backup database
docker-compose exec db pg_dump -U pe_sourcer pe_sourcing_db > backup.sql

# Restore database
docker-compose exec -T db psql -U pe_sourcer pe_sourcing_db < backup.sql
```

---

## 🔐 Security Recommendations

### Production Deployment

1. **Change Default Credentials:**
```bash
   # Login as admin@dealgenome.local
   # Go to Profile > Change Password
```

2. **Use Strong Secrets:**
```bash
   # Generate new secrets
   python3 -c "import secrets; print(secrets.token_hex(64))"
```

3. **Set Secure Database Password:**
```env
   DB_PASS=your-very-long-secure-password-here
```

4. **Enable HTTPS with Caddy:**
```bash
   # Update Caddyfile with your domain
   # Start with Caddy profile
   docker-compose --profile with-caddy up -d
```

5. **Restrict Network Access:**
```yaml
   # In docker-compose.yml, remove port mappings for internal services
```

6. **Regular Backups:**
```bash
   # Automate with cron
   0 2 * * * docker-compose exec db pg_dump -U pe_sourcer pe_sourcing_db > /backups/pe_$(date +\%Y\%m\%d).sql
```

---

## 🐛 Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs app

# Common issues:
# - Database not ready: Wait for health check
# - Missing secrets: Check .env file
# - Port conflict: Change port mapping
```

### Database connection errors
```bash
# Check database health
docker-compose ps db

# Restart database
docker-compose restart db

# Check connection
docker-compose exec db pg_isready -U pe_sourcer
```

### Permission errors
```bash
# Fix volume permissions
docker-compose down
sudo chown -R 1000:1000 ./logs ./config
docker-compose up -d
```

### Out of memory
```bash
# Check resource usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

---

## 📊 Monitoring

### Health Checks
```bash
# Check all services
docker-compose ps

# Application health
curl http://localhost:8000/api/status

# Database health
docker-compose exec db pg_isready -U pe_sourcer
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Disk usage
docker system df
```

### Logs
```bash
# Application logs
tail -f ./logs/pipeline.log

# Container logs
docker-compose logs -f --tail=100 app
```

---

## 🔄 Updates

### Update to New Version
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d
```

---

## 📚 Additional Resources

- **Main README:** `README.md`
- **Schema Documentation:** `schema_v5.1.sql`
- **GitHub Repository:** https://github.com/gpatkins/pe-sourcing-engine

---

## 🏗️ Architecture
```
┌─────────────┐
│   Caddy     │  ← HTTPS (443) / HTTP (80)
│  (Optional) │
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
┌──────▼──────┐              ┌────────▼────────┐
│  FastAPI    │              │   Metabase      │
│    App      │              │   Analytics     │
│  (Port 8000)│              │  (Port 3000)    │
└──────┬──────┘              └────────┬────────┘
       │                              │
       └──────────────┬───────────────┘
                      │
               ┌──────▼──────┐
               │ PostgreSQL  │
               │  Database   │
               │ (Port 5432) │
               └─────────────┘
```

---

**Version:** 5.1  
**Last Updated:** December 2025  
**Maintainer:** Gabriel Atkinson
