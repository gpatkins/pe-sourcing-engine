-- =============================================================================
-- DealGenome / PE Sourcing Engine - Database Schema
-- Version: 5.5 (Current)
-- Last Updated: December 2025
-- =============================================================================
-- This is the authoritative, complete schema for the PE Sourcing Engine.
-- For historical migrations, see schema/migrations/
-- =============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET search_path = public;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- companies - Primary company data table
-- -----------------------------------------------------------------------------
-- Stores all discovered and enriched company information.
-- Organized into 10 logical groups (see inline comments).
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS companies (
    -- GROUP 1: CORE IDENTITY (Who are they?)
    id uuid PRIMARY KEY,
    name text NOT NULL,
    legal_name text,
    url text,
    description text,

    -- GROUP 2: LOCATION & CONTACT (Where are they?)
    phone text,
    address text,
    city text,
    state text,
    zip text,
    country text,

    -- GROUP 3: BUSINESS LOGIC (What do they do?)
    industry_tag text,          -- AI Derived (e.g. "Commercial HVAC")
    naics_code text,            -- AI Derived (e.g. "238220")
    naics_description text,
    customer_type text,         -- "B2B", "B2C", "Both"
    revenue_model text,         -- "Recurring", "Project", "Retail"
    is_ecommerce boolean,
    is_franchise boolean,
    is_family_owned boolean,

    -- GROUP 4: FINANCIALS & SCORING (What are they worth?)
    revenue_estimate numeric,   -- Calculated Estimate
    employee_count integer,
    buyability_score smallint,  -- 0-100 Score

    -- GROUP 5: OWNER & LEADERSHIP (Who owns it?)
    owner_name text,
    owner_phone text,
    founder_email text,
    owner_source text,          -- "Website" or "Serper Ghost Search"

    -- GROUP 6: SOCIAL & WEB PRESENCE (Digital Footprint)
    linkedin_company_url text,
    owner_linkedin_url text,
    hiring_page_url text,
    facebook_url text,
    instagram_url text,
    twitter_url text,
    youtube_url text,

    -- GROUP 7: TECH & METRICS (Sophistication)
    website_tech_stack jsonb,   -- ["Shopify", "Klaviyo"]
    google_rating numeric,
    google_reviews integer,

    -- GROUP 8: RISK ENGINE (Red Flags)
    risk_flags text,            -- "Clean" or "ALERT: Lawsuit"
    recent_news jsonb,          -- Raw news articles

    -- GROUP 9: AI METADATA (Audit Trail)
    ai_confidence numeric,      -- 0.0 - 1.0
    ai_evidence text,           -- Quote used for reasoning

    -- GROUP 10: SYSTEM META (Pipeline Status)
    enrichment_status text DEFAULT 'pending', -- pending, partial, complete
    date_added date DEFAULT CURRENT_DATE,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    last_enriched_at timestamp without time zone,
    user_id integer             -- FK to users table
);

COMMENT ON COLUMN companies.user_id IS 'Links company to the user who discovered it (data isolation)';

-- -----------------------------------------------------------------------------
-- signals_job_postings - Job posting history (future use)
-- -----------------------------------------------------------------------------
-- Tracks job postings as growth signals.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS signals_job_postings (
    id SERIAL PRIMARY KEY,
    company_id uuid REFERENCES companies(id) ON DELETE CASCADE,
    posting_title text,
    posting_location text,
    posting_url text,
    scraped_at timestamp without time zone DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- signals_revenue_history - Revenue tracking over time (future use)
-- -----------------------------------------------------------------------------
-- Tracks changes in revenue estimates and employee counts.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS signals_revenue_history (
    id SERIAL PRIMARY KEY,
    company_id uuid REFERENCES companies(id) ON DELETE CASCADE,
    revenue_estimate numeric,
    employee_count integer,
    source text,
    collected_at timestamp without time zone DEFAULT now()
);

-- =============================================================================
-- USER MANAGEMENT (v5.1)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- users - Authentication and authorization
-- -----------------------------------------------------------------------------
-- Stores user accounts with role-based access control.
-- Roles: 'admin' (full access) or 'user' (limited access)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email character varying(255) UNIQUE NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50) DEFAULT 'user'::character varying,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    last_login timestamp without time zone,
    CONSTRAINT users_role_check CHECK (role::text = ANY (ARRAY['admin'::character varying, 'user'::character varying]::text[]))
);

COMMENT ON TABLE users IS 'User authentication and authorization table';
COMMENT ON COLUMN users.role IS 'admin: full access, can manage users and API keys | user: can discover and view own companies';

-- -----------------------------------------------------------------------------
-- user_activity - Audit log for user actions
-- -----------------------------------------------------------------------------
-- Tracks all user activities for compliance and analytics.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id integer REFERENCES users(id) ON DELETE CASCADE,
    activity_type character varying(100) NOT NULL,
    details jsonb,
    created_at timestamp without time zone DEFAULT now()
);

COMMENT ON TABLE user_activity IS 'Audit log for user actions';

-- =============================================================================
-- SCALE GENERATOR (v5.2)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- scale_generator_config - City/state configuration for discovery
-- -----------------------------------------------------------------------------
-- Stores locations for the scale generator feature.
-- Enables/disables cities for batch query generation.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS scale_generator_config (
    id SERIAL PRIMARY KEY,
    city character varying(100) NOT NULL,
    state character varying(2) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    UNIQUE(city, state)
);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- user_stats - User statistics view
-- -----------------------------------------------------------------------------
-- Aggregates user activity and company counts for dashboard display.
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.email,
    u.full_name,
    u.role,
    COUNT(DISTINCT c.id) AS total_companies,
    COUNT(DISTINCT CASE WHEN c.created_at > NOW() - INTERVAL '30 days' THEN c.id END) AS companies_last_30_days,
    MAX(c.created_at) AS last_company_added,
    u.last_login,
    u.created_at AS user_created_at
FROM users u
LEFT JOIN companies c ON c.user_id = u.id
GROUP BY u.id, u.email, u.full_name, u.role, u.last_login, u.created_at;

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- User activity indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at);

-- =============================================================================
-- FOREIGN KEY CONSTRAINTS
-- =============================================================================

-- Companies foreign keys
ALTER TABLE companies
    DROP CONSTRAINT IF EXISTS companies_user_id_fkey,
    ADD CONSTRAINT companies_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id);

-- Signals foreign keys
ALTER TABLE signals_job_postings
    DROP CONSTRAINT IF EXISTS signals_job_postings_company_id_fkey,
    ADD CONSTRAINT signals_job_postings_company_id_fkey
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE signals_revenue_history
    DROP CONSTRAINT IF EXISTS signals_revenue_history_company_id_fkey,
    ADD CONSTRAINT signals_revenue_history_company_id_fkey
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

-- User activity foreign keys
ALTER TABLE user_activity
    DROP CONSTRAINT IF EXISTS user_activity_user_id_fkey,
    ADD CONSTRAINT user_activity_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- =============================================================================
-- DEFAULT DATA
-- =============================================================================

-- Insert default admin user (if not exists)
-- Password: admin123 (CHANGE IMMEDIATELY AFTER FIRST LOGIN)
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
    'admin@dealgenome.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRU8uXi',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Insert default scale generator locations (if not exists)
INSERT INTO scale_generator_config (city, state) VALUES
('Birmingham', 'AL'), ('Montgomery', 'AL'), ('Mobile', 'AL'),
('Phoenix', 'AZ'), ('Tucson', 'AZ'), ('Little Rock', 'AR'),
('Los Angeles', 'CA'), ('San Francisco', 'CA'), ('San Diego', 'CA'), ('Sacramento', 'CA'),
('Denver', 'CO'), ('Colorado Springs', 'CO'), ('Hartford', 'CT'),
('Wilmington', 'DE'), ('Jacksonville', 'FL'), ('Miami', 'FL'), ('Tampa', 'FL'),
('Atlanta', 'GA'), ('Savannah', 'GA'), ('Honolulu', 'HI'),
('Boise', 'ID'), ('Chicago', 'IL'), ('Springfield', 'IL'),
('Indianapolis', 'IN'), ('Fort Wayne', 'IN'), ('Des Moines', 'IA'),
('Wichita', 'KS'), ('Louisville', 'KY'), ('New Orleans', 'LA'),
('Portland', 'ME'), ('Baltimore', 'MD'), ('Boston', 'MA'),
('Detroit', 'MI'), ('Minneapolis', 'MN'), ('Jackson', 'MS'),
('Kansas City', 'MO'), ('St. Louis', 'MO'), ('Billings', 'MT'),
('Omaha', 'NE'), ('Las Vegas', 'NV'), ('Manchester', 'NH'),
('Newark', 'NJ'), ('Albuquerque', 'NM'), ('New York', 'NY'),
('Charlotte', 'NC'), ('Raleigh', 'NC'), ('Fargo', 'ND'),
('Columbus', 'OH'), ('Cleveland', 'OH'), ('Oklahoma City', 'OK'),
('Portland', 'OR'), ('Philadelphia', 'PA'), ('Pittsburgh', 'PA'),
('Providence', 'RI'), ('Charleston', 'SC'), ('Sioux Falls', 'SD'),
('Nashville', 'TN'), ('Memphis', 'TN'), ('Houston', 'TX'),
('Dallas', 'TX'), ('San Antonio', 'TX'), ('Austin', 'TX'),
('Salt Lake City', 'UT'), ('Burlington', 'VT'), ('Virginia Beach', 'VA'),
('Seattle', 'WA'), ('Charleston', 'WV'), ('Milwaukee', 'WI'),
('Cheyenne', 'WY')
ON CONFLICT (city, state) DO NOTHING;

-- =============================================================================
-- SCHEMA VERSION COMPLETE
-- =============================================================================
