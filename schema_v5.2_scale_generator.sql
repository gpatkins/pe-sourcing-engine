-- v5.2: Scale Generator Configuration Table
-- Stores cities and states for the scale generator feature

CREATE TABLE IF NOT EXISTS scale_generator_config (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(city, state)
);

-- Insert default cities/states (from existing hard-coded list)
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
