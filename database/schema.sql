-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Complaints table - stores anonymized scam reports
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scam_type TEXT NOT NULL CHECK (scam_type IN ('UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION', 'LOTTERY_SCAM', 'INVESTMENT_FRAUD')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 100),
    victim_location GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- High-risk ATMs table - pre-seeded with known high-risk locations
CREATE TABLE high_risk_atms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    tags TEXT[] NOT NULL,
    city TEXT NOT NULL
);

-- Hotspots table - AI prediction results
CREATE TABLE hotspots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    hotspot_location GEOGRAPHY(POINT, 4326) NOT NULL,
    location_name TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    time_window_mins INTEGER NOT NULL DEFAULT 90,
    predicted_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'interdicted', 'false_alert'))
);

-- Digital cordons table - geofenced areas
CREATE TABLE cordons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    center_location GEOGRAPHY(POINT, 4326) NOT NULL,
    radius_meters INTEGER NOT NULL DEFAULT 2000,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired'))
);

-- LEA feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
    lea_action TEXT NOT NULL CHECK (lea_action IN ('confirmed', 'false', 'interdicted')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System learning metrics table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    total_predictions INTEGER NOT NULL DEFAULT 0,
    confirmed_predictions INTEGER NOT NULL DEFAULT 0,
    false_predictions INTEGER NOT NULL DEFAULT 0,
    accuracy_rate DOUBLE PRECISION GENERATED ALWAYS AS (
        CASE
            WHEN total_predictions > 0 THEN
                CAST(confirmed_predictions AS DOUBLE PRECISION) / total_predictions
            ELSE 0
        END
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial indexes for performance
CREATE INDEX idx_complaints_location ON complaints USING GIST (victim_location);
CREATE INDEX idx_high_risk_atms_location ON high_risk_atms USING GIST (location);
CREATE INDEX idx_hotspots_location ON hotspots USING GIST (hotspot_location);
CREATE INDEX idx_cordons_location ON cordons USING GIST (center_location);

-- Create temporal indexes
CREATE INDEX idx_complaints_created_at ON complaints (created_at DESC);
CREATE INDEX idx_hotspots_predicted_at ON hotspots (predicted_at DESC);
CREATE INDEX idx_cordons_expires_at ON cordons (expires_at);

-- Create composite indexes for common queries
CREATE INDEX idx_hotspots_status_predicted ON hotspots (status, predicted_at DESC);
CREATE INDEX idx_cordons_status_expires ON cordons (status, expires_at);

-- Row Level Security (RLS) policies for privacy compliance
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotspots ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Public read access for LEA dashboard (no PII exposed)
CREATE POLICY "Public read access for complaints" ON complaints
    FOR SELECT USING (true);

CREATE POLICY "Public read access for hotspots" ON hotspots
    FOR SELECT USING (true);

CREATE POLICY "Public read access for feedback" ON feedback
    FOR SELECT USING (true);

-- Function to automatically clean expired cordons
CREATE OR REPLACE FUNCTION cleanup_expired_cordons()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cordons
    SET status = 'expired'
    WHERE expires_at < NOW() AND status = 'active';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to cleanup expired cordons every 5 minutes
CREATE TRIGGER trigger_cleanup_cordons
    AFTER INSERT ON cordons
    FOR EACH ROW
    EXECUTE FUNCTION cleanup_expired_cordons();