-- PE Sourcing Engine v5.1 - User Authentication & Multi-Tenancy Migration
-- This migration adds user management, role-based access control

-- Create users table
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

-- Create user activity tracking table
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add user_id to companies table for data isolation
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE companies ADD COLUMN user_id INT REFERENCES users(id);
        CREATE INDEX idx_companies_user_id ON companies(user_id);
    END IF;
END $$;

-- Add user_id to discovery_queries table (if it exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'discovery_queries'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'discovery_queries' AND column_name = 'user_id'
        ) THEN
            ALTER TABLE discovery_queries ADD COLUMN user_id INT REFERENCES users(id);
            CREATE INDEX idx_discovery_queries_user_id ON discovery_queries(user_id);
        END IF;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at);

-- Insert default admin user
-- Password: admin123 (CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN)
-- This uses a pre-hashed bcrypt password for 'admin123'
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
    'admin@dealgenome.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRU8uXi',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Create a view for user statistics (useful for dashboard)
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

-- Add comment documentation
COMMENT ON TABLE users IS 'User authentication and authorization table';
COMMENT ON TABLE user_activity IS 'Audit log for user actions';
COMMENT ON COLUMN users.role IS 'admin: full access, can manage users | user: can discover and view own companies';
COMMENT ON COLUMN companies.user_id IS 'Links company to the user who discovered it (data isolation)';

-- Migration complete
SELECT 'v5.1 Migration Complete!' as status;
SELECT 'Default Admin Credentials: admin@dealgenome.local / admin123' as notice;
SELECT 'IMPORTANT: Change the admin password immediately after first login!' as warning;
