# PE Sourcing Engine v5.7 - Docker Setup

**Clean Docker build mirroring dg (Fedora/systemd) production environment**

---

## Quick Start

### 1. Ensure config/secrets.env exists with your API keys
```bash
# Check if file exists
ls -la config/secrets.env

# If not, copy from example
cp .env.example config/secrets.env
nano config/secrets.env
# Add your API keys
```

### 2. Build and Start
```bash
cd docker-v5.7
docker compose -f docker-compose-v5.7.yml up -d
```

### 3. Access the Application

- **Dashboard:** http://YOUR_SERVER_IP:8001
- **Default Login:** 
  - Email: `admin@dealgenome.local`
  - Password: `admin123`
  - **⚠️ CHANGE THIS IMMEDIATELY**

---

## Key Differences from v5.6

### Ports (No Conflicts)
- App: **8001** (not 8000)
- Caddy HTTP: **8080** (not 80)
- Caddy HTTPS: **8443** (not 443)
- Metabase: **3001** (not 3000)

### Container Names (Isolated)
- Database: `pe-sourcing-db-v57`
- App: `pe-sourcing-app-v57`
- Metabase: `pe-sourcing-metabase-v57`
- Caddy: `pe-sourcing-caddy-v57`

### Volumes (Separate)
All volumes have `-v57` suffix to avoid conflicts with old setup.

### Metabase
- Uses **H2 database** (not PostgreSQL)
- Avoids schema migration conflicts
- Started with: `docker compose --profile with-metabase up -d`

---

## Common Commands

### Start/Stop
```bash
cd docker-v5.7

# Start all services
docker compose -f docker-compose-v5.7.yml up -d

# Stop all services
docker compose -f docker-compose-v5.7.yml down

# Restart app only
docker compose -f docker-compose-v5.7.yml restart app
```

### View Logs
```bash
# All services
docker compose -f docker-compose-v5.7.yml logs -f

# App only
docker compose -f docker-compose-v5.7.yml logs -f app

# Last 50 lines
docker compose -f docker-compose-v5.7.yml logs app --tail 50
```

### Database Access
```bash
# PostgreSQL shell
docker compose -f docker-compose-v5.7.yml exec db psql -U pe_sourcer -d pe_sourcing_db

# Backup database
docker compose -f docker-compose-v5.7.yml exec db pg_dump -U pe_sourcer pe_sourcing_db > backup-v57.sql

# Restore database
docker compose -f docker-compose-v5.7.yml exec -T db psql -U pe_sourcer pe_sourcing_db < backup-v57.sql
```

### Container Cleanup
```bash
# Run cleanup script inside app container
docker compose -f docker-compose-v5.7.yml exec app /app/docker-v5.7/docker-clean-v5.7.sh

# Check container stats
docker stats
```

---

## Testing v5.7 Alongside Old Setup

Both versions can run simultaneously:

| Component | Old (v5.6) | New (v5.7) |
|-----------|------------|------------|
| Dashboard | :8000 | :8001 |
| Metabase | :3000 | :3001 |
| Database | pe-sourcing-db | pe-sourcing-db-v57 |
| Volumes | postgres_data | postgres_data_v57 |

This allows you to:
1. Keep old setup running
2. Test v5.7 thoroughly
3. Switch over when confident
4. Delete old setup

---

## Migration from v5.6 to v5.7

### Option 1: Fresh Start (Recommended)
```bash
# Stop old version
docker compose down

# Start v5.7
cd docker-v5.7
docker compose -f docker-compose-v5.7.yml up -d
```

### Option 2: Migrate Data
```bash
# Backup old database
docker compose exec db pg_dump -U pe_sourcer pe_sourcing_db > backup.sql

# Start v5.7
cd docker-v5.7
docker compose -f docker-compose-v5.7.yml up -d

# Restore backup
docker compose -f docker-compose-v5.7.yml exec -T db psql -U pe_sourcer pe_sourcing_db < ../backup.sql
```

---

## Cleanup Old Setup (After Testing v5.7)
```bash
# Stop old containers
docker compose down

# Remove old volumes (⚠️ DELETES DATA)
docker volume rm pe-sourcing-engine_postgres_data
docker volume rm pe-sourcing-engine_metabase_data
docker volume rm pe-sourcing-engine_app_data
docker volume rm pe-sourcing-engine_caddy_data
docker volume rm pe-sourcing-engine_caddy_config

# Remove old images
docker rmi pe-sourcing-engine-app

# Delete old Docker files
rm docker-compose.yml Dockerfile docker-install.py docker-manage.py docker-README.md Caddyfile
```

---

## Production Deployment

### With Domain (HTTPS via Caddy)

1. Edit `Caddyfile-v5.7` - uncomment domain section
2. Update domain name
3. Ensure DNS points to your server
4. Start with Caddy:
```bash
docker compose -f docker-compose-v5.7.yml --profile with-caddy up -d
```

### Environment Variables

All configuration in `config/secrets.env`:
```bash
DB_USER=pe_sourcer
DB_PASS=your_secure_password
DB_NAME=pe_sourcing_db

JWT_SECRET_KEY=your_jwt_secret
CSRF_SECRET=your_csrf_secret

GOOGLE_PLACES_API_KEY=your_key
GOOGLE_GEMINI_API_KEY=your_key
GEMINI_API_KEY=your_key
SERPER_API_KEY=your_key
```

---

## Troubleshooting

### App won't start
```bash
# Check logs
docker compose -f docker-compose-v5.7.yml logs app

# Check if database is ready
docker compose -f docker-compose-v5.7.yml ps db
```

### Can't login
```bash
# Verify admin user exists
docker compose -f docker-compose-v5.7.yml exec db psql -U pe_sourcer -d pe_sourcing_db -c "SELECT email, role FROM users;"

# Reset admin password if needed
# (see main documentation)
```

### Port conflicts
If ports 8001, 8080, 8443, or 3001 are in use, edit `docker-compose-v5.7.yml` and change the port mappings.

---

## Support

- **GitHub:** https://github.com/gpatkins/pe-sourcing-engine (private)
- **Version:** 5.7
- **Build Date:** December 2025
