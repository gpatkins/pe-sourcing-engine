-- 1. CLEANUP (Wipe everything)
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS signals_job_postings CASCADE;
DROP TABLE IF EXISTS signals_revenue_history CASCADE;
DROP TABLE IF EXISTS scoring_components CASCADE;

-- 2. REBUILD (Logical Grouping)
CREATE TABLE companies (
    -- GROUP 1: CORE IDENTITY (Who are they?)
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    legal_name TEXT,
    url TEXT,
    description TEXT,
    
    -- GROUP 2: LOCATION & CONTACT (Where are they?)
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    
    -- GROUP 3: BUSINESS LOGIC (What do they do?)
    industry_tag TEXT,          -- AI Derived (e.g. "Commercial HVAC")
    naics_code TEXT,            -- AI Derived (e.g. "238220")
    naics_description TEXT,
    customer_type TEXT,         -- "B2B", "B2C", "Both"
    revenue_model TEXT,         -- "Recurring", "Project"
    is_ecommerce BOOLEAN,
    is_franchise BOOLEAN,
    is_family_owned BOOLEAN,

    -- GROUP 4: FINANCIALS & SCORING (What are they worth?)
    revenue_estimate NUMERIC,   -- Calculated Estimate
    employee_count INT,
    buyability_score SMALLINT,  -- 0-100 Score
    
    -- GROUP 5: OWNER & LEADERSHIP (Who owns it?)
    owner_name TEXT,
    owner_phone TEXT,
    founder_email TEXT,
    owner_source TEXT,          -- "Website" or "Serper Ghost Search"
    
    -- GROUP 6: SOCIAL & WEB PRESENCE (Digital Footprint)
    linkedin_company_url TEXT,
    owner_linkedin_url TEXT,
    hiring_page_url TEXT,
    facebook_url TEXT,
    instagram_url TEXT,
    twitter_url TEXT,
    youtube_url TEXT,
    
    -- GROUP 7: TECH & METRICS (Sophistication)
    website_tech_stack JSONB,   -- ["Shopify", "Klaviyo"]
    google_rating NUMERIC,
    google_reviews INT,
    
    -- GROUP 8: RISK ENGINE (Red Flags)
    risk_flags TEXT,            -- "Clean" or "ALERT: Lawsuit"
    recent_news JSONB,          -- Raw news articles
    
    -- GROUP 9: AI METADATA (Audit Trail)
    ai_confidence NUMERIC,      -- 0.0 - 1.0
    ai_evidence TEXT,           -- Quote used for reasoning
    
    -- GROUP 10: SYSTEM META (Pipeline Status)
    enrichment_status TEXT DEFAULT 'pending', -- pending, partial, complete
    date_added DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    last_enriched_at TIMESTAMP
);

-- OPTIONAL: History Tables (Future Proofing)
CREATE TABLE signals_job_postings (
    id SERIAL PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    posting_title TEXT,
    posting_location TEXT,
    posting_url TEXT,
    scraped_at TIMESTAMP DEFAULT now()
);

CREATE TABLE signals_revenue_history (
    id SERIAL PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    revenue_estimate NUMERIC,
    employee_count INT,
    source TEXT,
    collected_at TIMESTAMP DEFAULT now()
);
