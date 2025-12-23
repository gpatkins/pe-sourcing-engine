# Database Schema Documentation

## Overview
This directory contains the authoritative database schema for the DealGenome PE Sourcing Engine.

## Files

### current.sql
**The single source of truth for the database schema.**

- Complete, up-to-date schema definition
- Includes all tables, indexes, constraints, and views
- Safe to run multiple times (uses `IF NOT EXISTS`)
- Contains inline documentation and comments

**When to use:**
- Setting up a new database
- Verifying schema matches expectations
- Reference for development

---

## Schema Structure

### Core Tables

#### `companies`
Primary data table storing all discovered and enriched company information.

**Organized into 10 logical groups:**
1. Core Identity (name, legal_name, url, description)
2. Location & Contact (address, city, state, phone)
3. Business Logic (industry, NAICS, customer type, franchise status)
4. Financials (revenue, employees, buyability score)
5. Ownership (owner name, contact info)
6. Social Presence (LinkedIn, Facebook, etc.)
7. Tech & Metrics (tech stack, Google ratings)
8. Risk Intelligence (risk flags, news)
9. AI Metadata (confidence, evidence)
10. System Meta (enrichment status, timestamps, user assignment)

#### `signals_job_postings`
Job posting history for growth signal detection (future use).

#### `signals_revenue_history`
Revenue and employee count tracking over time (future use).

---

### User Management (v5.1)

#### `users`
User authentication and role-based access control.
- Roles: `admin` (full access) or `user` (limited access)
- bcrypt password hashing
- Activity tracking via foreign key

#### `user_activity`
Audit log for all user actions (logins, exports, pipeline runs).

---

### Scale Generator (v5.2)

#### `scale_generator_config`
City/state configuration for batch discovery query generation.
- Enable/disable locations
- Supports 80+ US cities by default

---

### Views

#### `user_stats`
Aggregated user statistics for dashboard display.
- Total companies per user
- Companies added in last 30 days
- Last activity timestamps

---

## Usage

### Creating a Fresh Database
```bash
# Create database
createdb -U postgres pe_sourcing_db

# Create user
psql -U postgres -c "CREATE USER pe_sourcer WITH PASSWORD 'your_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE pe_sourcing_db TO pe_sourcer;"

# Apply schema
psql -U pe_sourcer -d pe_sourcing_db -f schema/current.sql
```

### Verifying Schema
```bash
# Dump current schema and compare
pg_dump -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db --schema-only > /tmp/live_schema.sql
diff schema/current.sql /tmp/live_schema.sql
```

### Backing Up Data
```bash
# Full backup (schema + data)
pg_dump -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db > backup_$(date +%Y%m%d).sql

# Data only
pg_dump -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db --data-only > data_backup_$(date +%Y%m%d).sql
```

### Restoring from Backup
```bash
# Restore full backup
psql -U pe_sourcer -d pe_sourcing_db < backup_20241223.sql

# Restore data only (schema must already exist)
psql -U pe_sourcer -d pe_sourcing_db < data_backup_20241223.sql
```

---

## Schema Modifications

### Adding a New Column

1. **Update `schema/current.sql`** with the new column
2. **Create a migration file** in `schema/migrations/` (if needed for existing databases)
3. **Test on development (dg) first**
4. **Document in CHANGELOG.md**

**Example:**
```sql
-- In current.sql
ALTER TABLE companies ADD COLUMN IF NOT EXISTS new_field text;

-- Create schema/migrations/v5.5_add_new_field.sql
ALTER TABLE companies ADD COLUMN IF NOT EXISTS new_field text;
COMMENT ON COLUMN companies.new_field IS 'Description of new field';
```

### Modifying Existing Structure

**⚠️ Warning:** Be extremely careful with modifications that could cause data loss.

Always:
1. Backup database first
2. Test on non-production environment
3. Use transactions
4. Have rollback plan

---

## Indexes

### Current Indexes
- `idx_companies_user_id` - Filter companies by user
- `idx_users_email` - Fast user lookup by email
- `idx_users_role` - Filter users by role
- `idx_user_activity_user_id` - User activity queries
- `idx_user_activity_created_at` - Time-based activity queries

### Adding New Indexes

Consider adding indexes when:
- Query performance is slow
- Filtering/sorting on specific columns frequently
- Foreign key lookups are common

**Example:**
```sql
CREATE INDEX IF NOT EXISTS idx_companies_buyability_score 
ON companies(buyability_score) 
WHERE buyability_score IS NOT NULL;
```

---

## Foreign Key Relationships
```
users (1) ──────────────> (*) companies
  │                            │
  │                            ├──> (*) signals_job_postings
  │                            └──> (*) signals_revenue_history
  │
  └──────────────> (*) user_activity
```

**Cascade Behavior:**
- Deleting a user → cascades to companies (careful!)
- Deleting a company → cascades to signals tables
- Deleting a user → cascades to user_activity

---

## Default Data

The schema includes default data insertions:

1. **Admin User**
   - Email: `admin@dealgenome.local`
   - Password: `admin123` (⚠️ CHANGE IMMEDIATELY)
   - Role: `admin`

2. **Scale Generator Locations**
   - 80+ US cities pre-populated
   - All active by default

---

## Troubleshooting

### Schema Drift Detection

If your live database doesn't match `current.sql`:
```bash
# Dump live schema
pg_dump -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db --schema-only > /tmp/live.sql

# Compare
diff schema/current.sql /tmp/live.sql
```

### Permission Issues
```bash
# Grant all permissions to pe_sourcer
psql -U postgres -d pe_sourcing_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pe_sourcer;"
psql -U postgres -d pe_sourcing_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pe_sourcer;"
```

### Connection Issues
```bash
# Test connection
psql -U pe_sourcer -h 10.55.55.55 -d pe_sourcing_db -c "SELECT version();"
```

---

## Version History

- **v5.4** - Current schema (companies, users, scale_generator_config)
- **v5.2** - Added scale_generator_config table
- **v5.1** - Added user authentication (users, user_activity)
- **v5.0** - Base schema (companies, signals tables)

---

## Contact

For schema questions or issues:
- Developer: Gabriel Atkinson
- Repository: https://github.com/gpatkins/pe-sourcing-engine (private)
