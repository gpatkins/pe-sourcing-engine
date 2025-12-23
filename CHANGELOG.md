# Changelog

All notable changes to DealGenome / PE Sourcing Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.5.0] - 2025-12-23

### Added
- Schema directory with organized database documentation (`schema/`)
- `schema/current.sql` - Authoritative database schema
- `schema/README.md` - Complete schema documentation
- Docker helper scripts renamed for clarity
  - `docker-install.py` (formerly `install.py`)
  - `docker-manage.py` (formerly `manage.py`)
  - `docker-README.md` (formerly `README-DOCKER.md`)
- Enhanced `.gitignore` with comprehensive patterns
- `CHANGELOG.md` - Version history tracking (this file)
- `CONTRIBUTING.md` - Development workflow guide

### Changed
- Schema files moved from root to `schema/` directory
- Main `README.md` updated with v5.5 information and Docker section
- Docker documentation updated with new script names

### Fixed
- PostgreSQL schema compatibility issue (search_path configuration)

### Removed
- Old schema files from root directory (`schema.sql`, `schema_v5.1.sql`, `schema_v5.2_scale_generator.sql`)

---

## [5.4.0] - 2024-12-XX

### Added
- Application restart functionality with environment detection (systemd vs Docker)
- Enhanced admin dashboard with system management tools
- System cleanup endpoint (`/admin/system/cleanup`)
- Application restart endpoint (`/admin/app/restart`)

### Changed
- Environment variable management now available via UI
- System cleanup scripts integrated into dashboard

---

## [5.3.0] - 2024-11-XX

### Added
- Environment variable management via admin dashboard
- System cleanup scripts for memory management

---

## [5.2.0] - 2024-10-XX

### Added
- Scale Generator feature with database-driven location management
- `scale_generator_config` table for city/state configuration
- Scale generator UI in dashboard for managing locations
- Batch query generation across multiple cities

### Changed
- Discovery query generation now uses active locations from database
- Improved query creation workflow

---

## [5.1.0] - 2024-09-XX

### Added
- Multi-user authentication system with JWT tokens
- Role-based access control (admin vs user roles)
- User management dashboard (admin only)
- User activity logging and audit trails
- `users` table for authentication
- `user_activity` table for audit logs
- Password reset functionality (admin)
- User profile page with statistics

### Changed
- Companies table now includes `user_id` for data ownership
- Dashboard authentication required for all routes

### Security
- JWT-based authentication with HTTP-only cookies
- bcrypt password hashing
- CSRF protection on forms
- Secure session management

---

## [5.0.0] - 2024-08-XX

### Added
- Initial release of DealGenome PE Sourcing Engine
- Google Places API discovery pipeline
- AI-powered enrichment with Google Gemini
- Risk intelligence via Serper news search
- Owner "ghost hunting" functionality
- Buyability scoring system (0-100)
- FastAPI dashboard with real-time pipeline monitoring
- PostgreSQL database with comprehensive company schema
- Docker deployment support with installer
- Metabase analytics integration
- Multi-module enrichment pipeline:
  - Domain normalization
  - Website text extraction
  - LinkedIn profile discovery
  - E-commerce detection
  - Industry classification
  - News/risk scanning
  - AI classification
  - Owner identification
  - Email discovery
  - Revenue estimation

### Infrastructure
- Docker Compose orchestration
- Caddy reverse proxy with automatic HTTPS
- Systemd service for development server
- PostgreSQL 15 database

---

## [Unreleased]

### Planned
- Scoring model formalization with versioning
- Score component breakdown and history tracking
- Project layout normalization (organize scripts)
- Configuration centralization with validation
- Logging cleanup and standardization
- Dependency audit and cleanup

---

## Version History Summary

- **5.5.0** (Current) - Organization & hygiene improvements
- **5.4.0** - Admin system management tools
- **5.3.0** - Environment variable management
- **5.2.0** - Scale generator feature
- **5.1.0** - Multi-user authentication
- **5.0.0** - Initial release

---

**Note:** Dates marked with "XX" are approximate. Refer to git commit history for exact timestamps.

**Repository:** https://github.com/gpatkins/pe-sourcing-engine (Private)  
**Maintainer:** Gabriel Atkinson
