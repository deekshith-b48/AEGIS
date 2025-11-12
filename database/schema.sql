-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Core Tables for Project AEGIS MVP

-- 1. complaints table - stores citizen scam reports (zero PII)
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fraud_type TEXT NOT NULL CHECK (fraud_type IN ('UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION', 'LOTTERY_SCAM', 'INVESTMENT_FRAUD')),
    amount NUMERIC(12,2) CHECK (amount > 100),
    victim_location GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. high_risk_atms table - pre-seeded ATM data for predictions
CREATE TABLE high_risk_atms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    tags TEXT[] NOT NULL,
    city TEXT NOT NULL
);

-- 3. hotspots table - AI prediction results
CREATE TABLE hotspots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    hotspot_location GEOGRAPHY(POINT, 4326) NOT NULL,
    location_name TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    time_window_mins INTEGER NOT NULL,
    predicted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. alerts table - tracks alert dispatch
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id),
    channel TEXT NOT NULL CHECK (channel IN ('sms', 'email')),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed'))
);

-- 5. feedback table - LEA outcomes for learning loop
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id),
    outcome TEXT NOT NULL CHECK (outcome IN ('confirmed', 'false')),
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. cordons table - digital cordon management
CREATE TABLE cordons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id),
    center GEOGRAPHY(POINT, 4326) NOT NULL,
    radius_meters INTEGER DEFAULT 2000,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Create spatial indexes for performance
CREATE INDEX idx_complaints_location ON complaints USING GIST (victim_location);
CREATE INDEX idx_high_risk_atms_location ON high_risk_atms USING GIST (location);
CREATE INDEX idx_hotspots_location ON hotspots USING GIST (hotspot_location);
CREATE INDEX idx_cordons_center ON cordons USING GIST (center);

-- Create temporal indexes
CREATE INDEX idx_complaints_created_at ON complaints (created_at DESC);
CREATE INDEX idx_hotspots_predicted_at ON hotspots (predicted_at DESC);
CREATE INDEX idx_cordons_expires_at ON cordons (expires_at);

-- RLS DISABLED for MVP as per specification
-- Note: Row Level Security is disabled for demonstration purposes

-- Function to get ATMs within radius using PostGIS
CREATE OR REPLACE FUNCTION get_nearby_atms(
    victim_lat FLOAT,
    victim_lon FLOAT,
    radius_meters INTEGER
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    location GEOGRAPHY(POINT, 4326),
    tags TEXT[],
    city TEXT,
    distance_meters FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        atm.id,
        atm.name,
        atm.location,
        atm.tags,
        atm.city,
        ST_Distance(
            atm.location::geography,
            ST_GeomFromText('POINT(' || victim_lon || ' ' || victim_lat || ')', 4326)::geography
        ) as distance_meters
    FROM high_risk_atms atm
    WHERE ST_DWithin(
        atm.location,
        ST_GeomFromText('POINT(' || victim_lon || ' ' || victim_lat || ')', 4326),
        radius_meters
    )
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;

-- Function to get ATMs by tags
CREATE OR REPLACE FUNCTION get_atms_by_tags(
    required_tags TEXT[]
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    location GEOGRAPHY(POINT, 4326),
    tags TEXT[],
    city TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT atm.id, atm.name, atm.location, atm.tags, atm.city
    FROM high_risk_atms atm
    WHERE atm.tags && required_tags;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old data (7 days retention for MVP)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete complaints older than 7 days
    DELETE FROM complaints
    WHERE created_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;