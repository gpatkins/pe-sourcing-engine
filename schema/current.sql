-- PE Sourcing Engine v5.7 - Consolidated Database Schema
-- Single authoritative source for database structure
-- Last updated: December 2024
-- See schema/README.md for documentation

-- Set search path for PostgreSQL compatibility
SET search_path TO public;

-- ============================================================================
-- TABLE: users
-- User authentication and authorization (v5.1)
-- MUST BE CREATED FIRST - other tables reference this
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- TABLE: companies
-- Core table storing all discovered and enriched company data
-- ============================================================================
CREATE TABLE IF NOT EXISTS companies (
    -- Core Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    legal_name TEXT,
    url TEXT,
    description TEXT,

    -- Location & Contact
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,

    -- Business Classification
    industry_tag TEXT,
    naics_code TEXT,
    naics_description TEXT,
    customer_type TEXT,
    revenue_model TEXT,
    is_ecommerce BOOLEAN DEFAULT FALSE,
    is_franchise BOOLEAN DEFAULT FALSE,
    is_family_owned BOOLEAN DEFAULT FALSE,

    -- Financial Metrics
    revenue_estimate NUMERIC,
    employee_count INTEGER,
    buyability_score SMALLINT CHECK (buyability_score >= 0 AND buyability_score <= 100),

    -- Ownership & Leadership
    owner_name TEXT,
    owner_phone TEXT,
    founder_email TEXT,
    owner_source TEXT,

    -- Digital Presence
    linkedin_company_url TEXT,
    owner_linkedin_url TEXT,
    hiring_page_url TEXT,
    facebook_url TEXT,
    instagram_url TEXT,
    twitter_url TEXT,
    youtube_url TEXT,

    -- Technology & Metrics
    website_tech_stack JSONB,
    google_rating NUMERIC,
    google_reviews INTEGER,

    -- Risk Analysis
    risk_flags TEXT,
    recent_news JSONB,

    -- AI Metadata
    ai_confidence NUMERIC,
    ai_evidence TEXT,

    -- System Metadata
    enrichment_status TEXT DEFAULT 'pending',
    date_added DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_enriched_at TIMESTAMP,

    -- Multi-user Support (v5.1)
    user_id INTEGER REFERENCES users(id)
);

-- Indexes for companies table
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);
CREATE INDEX IF NOT EXISTS idx_companies_enrichment_status ON companies(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_companies_buyability_score ON companies(buyability_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_companies_industry_tag ON companies(industry_tag);
CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(state);

-- ============================================================================
-- TABLE: user_activity
-- Audit log for user actions (v5.1)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for user_activity table
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at DESC);

-- ============================================================================
-- TABLE: scale_generator_config
-- Manages cities/states for scale generator feature (v5.2)
-- ============================================================================
CREATE TABLE IF NOT EXISTS scale_generator_config (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(city, state)
);

-- Index for scale_generator_config
CREATE INDEX IF NOT EXISTS idx_scale_generator_active ON scale_generator_config(is_active);

-- ============================================================================
-- TABLE: signals_job_postings
-- Future-proofing: Track job postings as expansion signals
-- ============================================================================
CREATE TABLE IF NOT EXISTS signals_job_postings (
    id SERIAL PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    posting_title TEXT,
    posting_location TEXT,
    posting_url TEXT,
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Index for signals_job_postings
CREATE INDEX IF NOT EXISTS idx_signals_job_postings_company_id ON signals_job_postings(company_id);

-- ============================================================================
-- TABLE: signals_revenue_history
-- Future-proofing: Track revenue changes over time
-- ============================================================================
CREATE TABLE IF NOT EXISTS signals_revenue_history (
    id SERIAL PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    revenue_estimate NUMERIC,
    employee_count INTEGER,
    source TEXT,
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Index for signals_revenue_history
CREATE INDEX IF NOT EXISTS idx_signals_revenue_history_company_id ON signals_revenue_history(company_id);

-- ============================================================================
-- VIEW: user_stats
-- Aggregated statistics for user dashboard (v5.1)
-- ============================================================================
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.email,
    u.full_name,
    u.role,
    COUNT(DISTINCT c.id) as total_companies,
    COUNT(DISTINCT CASE WHEN c.created_at > NOW() - INTERVAL '30 days' THEN c.id END) as companies_last_30_days,
    MAX(c.created_at) as last_company_added,
    u.last_login,
    u.created_at as user_created_at
FROM users u
LEFT JOIN companies c ON c.user_id = u.id
GROUP BY u.id, u.email, u.full_name, u.role, u.last_login, u.created_at;

-- ============================================================================
-- DEFAULT DATA
-- ============================================================================

-- Default admin user (Password: admin123 - CHANGE AFTER FIRST LOGIN!)
-- Hash generated with bcrypt for password 'admin123'
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
    'admin@dealgenome.local',
    '$2b$12$jt7SB4jspFfPFHGypV80RuZsFOTmRlO0G7icgZb8OvqYk64xMY6Me',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Default scale generator locations (80 cities across US)
INSERT INTO scale_generator_config (city, state) VALUES
-- Alabama
('Birmingham', 'AL'), ('Montgomery', 'AL'), ('Mobile', 'AL'),
-- Arizona
('Phoenix', 'AZ'), ('Tucson', 'AZ'),
-- Arkansas
('Little Rock', 'AR'),
-- California
('Los Angeles', 'CA'), ('San Francisco', 'CA'), ('San Diego', 'CA'), ('Sacramento', 'CA'),
-- Colorado
('Denver', 'CO'), ('Colorado Springs', 'CO'),
-- Connecticut
('Hartford', 'CT'),
-- Delaware
('Wilmington', 'DE'),
-- Florida
('Jacksonville', 'FL'), ('Miami', 'FL'), ('Tampa', 'FL'),
-- Georgia
('Atlanta', 'GA'), ('Savannah', 'GA'),
-- Hawaii
('Honolulu', 'HI'),
-- Idaho
('Boise', 'ID'),
-- Illinois
('Chicago', 'IL'), ('Springfield', 'IL'),
-- Indiana
('Indianapolis', 'IN'), ('Fort Wayne', 'IN'),
-- Iowa
('Des Moines', 'IA'),
-- Kansas
('Wichita', 'KS'),
-- Kentucky
('Louisville', 'KY'),
-- Louisiana
('New Orleans', 'LA'),
-- Maine
('Portland', 'ME'),
-- Maryland
('Baltimore', 'MD'),
-- Massachusetts
('Boston', 'MA'),
-- Michigan
('Detroit', 'MI'),
-- Minnesota
('Minneapolis', 'MN'),
-- Mississippi
('Jackson', 'MS'),
-- Missouri
('Kansas City', 'MO'), ('St. Louis', 'MO'),
-- Montana
('Billings', 'MT'),
-- Nebraska
('Omaha', 'NE'),
-- Nevada
('Las Vegas', 'NV'),
-- New Hampshire
('Manchester', 'NH'),
-- New Jersey
('Newark', 'NJ'),
-- New Mexico
('Albuquerque', 'NM'),
-- New York
('New York', 'NY'),
-- North Carolina
('Charlotte', 'NC'), ('Raleigh', 'NC'),
-- North Dakota
('Fargo', 'ND'),
-- Ohio
('Columbus', 'OH'), ('Cleveland', 'OH'),
-- Oklahoma
('Oklahoma City', 'OK'),
-- Oregon
('Portland', 'OR'),
-- Pennsylvania
('Philadelphia', 'PA'), ('Pittsburgh', 'PA'),
-- Rhode Island
('Providence', 'RI'),
-- South Carolina
('Charleston', 'SC'),
-- South Dakota
('Sioux Falls', 'SD'),
-- Tennessee
('Nashville', 'TN'), ('Memphis', 'TN'),
-- Texas
('Houston', 'TX'), ('Dallas', 'TX'), ('San Antonio', 'TX'), ('Austin', 'TX'),
-- Utah
('Salt Lake City', 'UT'),
-- Vermont
('Burlington', 'VT'),
-- Virginia
('Virginia Beach', 'VA'),
-- Washington
('Seattle', 'WA'),
-- West Virginia
('Charleston', 'WV'),
-- Wisconsin
('Milwaukee', 'WI'),
-- Wyoming
('Cheyenne', 'WY')
ON CONFLICT (city, state) DO NOTHING;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE companies IS 'Core table for company discovery and enrichment data';
COMMENT ON TABLE users IS 'User authentication and authorization (v5.1)';
COMMENT ON TABLE user_activity IS 'Audit log for user actions (v5.1)';
COMMENT ON TABLE scale_generator_config IS 'City/state configuration for scale generator (v5.2)';
COMMENT ON TABLE signals_job_postings IS 'Job posting signals for company growth tracking';
COMMENT ON TABLE signals_revenue_history IS 'Historical revenue tracking for trend analysis';

COMMENT ON COLUMN companies.id IS 'UUID primary key (deterministic based on domain or name+address)';
COMMENT ON COLUMN companies.enrichment_status IS 'pending, partial, or complete';
COMMENT ON COLUMN companies.buyability_score IS 'PE acquisition score (0-100)';
COMMENT ON COLUMN companies.user_id IS 'Links company to user who discovered it (NULL for legacy data)';
COMMENT ON COLUMN users.role IS 'admin: full access | user: can discover and view own companies';

-- ============================================================================
-- SCHEMA COMPLETE v5.7 - Table order fixed for proper foreign key resolution
-- ============================================================================
