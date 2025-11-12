-- Advanced Project AEGIS Schema - Enhanced Architecture
-- Supports NCRP integration, bank transaction logs, I4C data, and AI features

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Data Source Tables
CREATE TABLE IF NOT EXISTS ncrp_complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id VARCHAR(50) UNIQUE NOT NULL,
    scam_type VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    victim_location GEOGRAPHY(POINT, 4326),
    anonymized_location GEOGRAPHY(POINT, 4326), -- k=50 anonymity
    victim_age_group VARCHAR(20),
    victim_gender VARCHAR(20),
    digital_footprint JSONB, -- Browser, device info
    ip_address INET,
    complaint_timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'received',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    bank_code VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    account_hash VARCHAR(64) NOT NULL, -- Hashed account number
    upi_id VARCHAR(100), -- Hashed if PII
    merchant_hash VARCHAR(64), -- Hashed merchant name
    location GEOGRAPHY(POINT, 4326),
    risk_score DECIMAL(3,2) DEFAULT 0.0,
    fraud_signals JSONB,
    is_suspicious BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    batch_id UUID DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS i4c_crime_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crime_id VARCHAR(50) UNIQUE NOT NULL,
    modus_operandi TEXT,
    repeat_offender BOOLEAN DEFAULT FALSE,
    criminal_network VARCHAR(100),
    location GEOGRAPHY(POINT, 4326),
    date_range_start DATE,
    date_range_end DATE,
    scam_type VARCHAR(100),
    victim_profile JSONB,
    outcome VARCHAR(50),
    conviction_rate DECIMAL(5,2),
    severity_score INTEGER CHECK (severity_score >= 1 AND severity_score <= 10),
    data_source VARCHAR(50),
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS atm_gis_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atm_id VARCHAR(50) UNIQUE NOT NULL,
    bank_name VARCHAR(100),
    operator VARCHAR(100),
    location GEOGRAPHY(POINT, 4326),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    pincode VARCHAR(6),
    atm_type VARCHAR(50),
    daily_avg_transactions INTEGER DEFAULT 0,
    weekly_avg_transactions INTEGER DEFAULT 0,
    monthly_avg_transactions INTEGER DEFAULT 0,
    high_risk_score DECIMAL(3,2) DEFAULT 0.0,
    nearby_points JSONB, -- Railway stations, bus stops, highways
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transport_gis_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transport_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200),
    type VARCHAR(50) CHECK (type IN ('railway_station', 'bus_stop', 'metro_station', 'airport', 'highway_toll')),
    location GEOGRAPHY(POINT, 4326),
    city VARCHAR(100),
    state VARCHAR(50),
    daily_footfall INTEGER DEFAULT 0,
    peak_hours JSONB, -- Peak traffic hours
    connectivity_score DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature Store Tables
CREATE TABLE IF NOT EXISTS spatial_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location GEOGRAPHY(POINT, 4326),
    feature_type VARCHAR(50),
    feature_value DECIMAL(10,2),
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    window_size INTEGER DEFAULT 3600, -- 1 hour window
    feature_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS temporal_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_name VARCHAR(100),
    time_bucket TIMESTAMPTZ,
    feature_value DECIMAL(10,2),
    confidence DECIMAL(3,2),
    model_version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Prediction Tables
CREATE TABLE IF NOT EXISTS ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    input_data JSONB,
    prediction JSONB,
    confidence DECIMAL(3,2) NOT NULL,
    risk_score DECIMAL(3,2) NOT NULL,
    top_hotspots JSONB, -- Top 3 predictions
    uncertainty_bounds JSONB,
    prediction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    model_path TEXT,
    hyperparameters JSONB,
    performance_metrics JSONB,
    training_data_size INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    trained_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Digital Cordon System
CREATE TABLE IF NOT EXISTS digital_cordons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cordon_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES ai_predictions(id),
    center_location GEOGRAPHY(POINT, 4326) NOT NULL,
    radius_meters INTEGER DEFAULT 2000,
    shape_type VARCHAR(20) DEFAULT 'circle',
    status VARCHAR(20) DEFAULT 'active',
    activation_source VARCHAR(50),
    npc_request_id VARCHAR(100),
    npc_response JSONB,
    affected_accounts INTEGER DEFAULT 0,
    blocked_transactions INTEGER DEFAULT 0,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit & Compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    actor_id VARCHAR(100),
    actor_type VARCHAR(50),
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    action VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blockchain_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_hash VARCHAR(64) UNIQUE NOT NULL,
    transaction_hash VARCHAR(64),
    smart_contract_address VARCHAR(42),
    event_signature VARCHAR(132),
    block_number BIGINT,
    block_timestamp TIMESTAMPTZ,
    event_data JSONB,
    previous_state_hash VARCHAR(64),
    gas_used BIGINT,
    gas_price BIGINT,
    transaction_index INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning and Feedback
CREATE TABLE IF NOT EXISTS feedback_loop (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES ai_predictions(id),
    cordon_id UUID REFERENCES digital_cordons(id),
    lea_officer_id VARCHAR(50),
    outcome VARCHAR(50) NOT NULL,
    outcome_details TEXT,
    confidence_rating INTEGER CHECK (confidence_rating >= 1 AND confidence_rating <= 5),
    response_time_minutes INTEGER,
    actual_result VARCHAR(100),
    lessons_learned TEXT,
    feedback_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ai_model_versions(id),
    evaluation_date DATE NOT NULL,
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_score DECIMAL(5,4),
    true_positives INTEGER,
    false_positives INTEGER,
    true_negatives INTEGER,
    false_negatives INTEGER,
    total_predictions INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ncrp_complaints_location ON ncrp_complaints USING GIST (victim_location);
CREATE INDEX IF NOT EXISTS idx_ncrp_complaints_timestamp ON ncrp_complaints (complaint_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_hash ON bank_transactions (account_hash);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_timestamp ON bank_transactions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_i4c_crime_location ON i4c_crime_data USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_confidence ON ai_predictions (confidence DESC);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_timestamp ON ai_predictions (prediction_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_spatial_features_location ON spatial_features USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_temporal_features_time ON temporal_features (time_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_cordons_status ON digital_cordons (status, expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp DESC);

-- Enable Row Level Security for sensitive tables
ALTER TABLE ncrp_complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE digital_cordons ENABLE ROW_LEVEL SECURITY;

-- RLS Policies (simplified for MVP)
CREATE POLICY IF NOT EXISTS "LEA read access on complaints" ON ncrp_complaints
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "LEA read access on cordons" ON digital_cordons
    FOR SELECT USING (true);

-- Functions for advanced analytics
CREATE OR REPLACE FUNCTION calculate_spatial_features(
    center_lat DECIMAL,
    center_lng DECIMAL,
    radius_meters INTEGER DEFAULT 2000
)
RETURNS TABLE (
    feature_type TEXT,
    feature_value DECIMAL,
    feature_metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    -- ATM density within radius
    SELECT 'atm_density'::TEXT,
        COUNT(atm.id)::DECIMAL,
        jsonb_build_object(
            'radius_meters', radius_meters,
            'count', COUNT(atm.id)
        )
    FROM atm_gis_data atm
    WHERE ST_DWithin(
        atm.location,
        ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
        radius_meters
    )
    GROUP BY 1, 2, radius_meters

    UNION ALL

    -- Transport hub proximity
    SELECT 'transport_proximity'::TEXT,
        CASE
            WHEN MIN(ST_Distance(
                ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
                transport.location
            )) = 0 THEN 100
            ELSE 100 - MIN(ST_Distance(
                ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
                transport.location
            )) * 10
        END::DECIMAL,
        jsonb_build_object(
            'nearest_transport',
            (SELECT transport.name
             FROM transport_gis_data transport
             ORDER BY ST_Distance(
                 ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
                 transport.location
             )
             LIMIT 1),
            'distance_meters', MIN(ST_Distance(
                ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
                transport.location
            ))
        )
    FROM transport_gis_data transport
    WHERE ST_DWithin(
        transport.location,
        ST_GeomFromText('POINT(' || center_lng || ' ' || center_lat || ')', 4326),
        5000
    )
    GROUP BY 1, 2;
END;
$$ LANGUAGE plpgsql;

-- Function for k-anonymity
CREATE OR REPLACE FUNCTION apply_k_anonymity(
    exact_location GEOGRAPHY(POINT, 4324),
    k_threshold INTEGER DEFAULT 50
)
RETURNS GEOGRAPHY(POINT, 4324) AS $$
DECLARE
    anonymized_location GEOGRAPHY(POINT, 4324);
BEGIN
    -- Add random noise within a reasonable radius (approximately 100m)
    -- This is a simplified implementation - in production, use more sophisticated k-anonymity
    anonymized_location := ST_Transform(
        exact_location,
        ST_Scale(ST_Translate(
            exact_location,
            (random() - 0.5) * 0.001, -- Approximately 50m latitude noise
            (random() - 0.5) * 0.001  -- Approximately 50m longitude noise
        ),
        1.0
    );

    RETURN anonymized_location;
END;
$$ LANGUAGE plpgsql;

-- Differential Privacy functions
CREATE OR REPLACE FUNCTION add_differential_privacy_noise(
    value DECIMAL,
    epsilon DECIMAL DEFAULT 0.5,
    sensitivity DECIMAL DEFAULT 1.0
)
RETURNS DECIMAL AS $$
BEGIN
    -- Laplace mechanism implementation
    -- Scale parameter = sensitivity / epsilon
    RETURN value + (CASE WHEN random() < 0.5 THEN -1 ELSE 1 END) * (sensitivity / epsilon);
END;
$$ LANGUAGE plpgsql;

-- Automated cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old predictions
    DELETE FROM ai_predictions WHERE expires_at < NOW() - INTERVAL '1 day';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Archive old audit logs (move to separate table in production)
    DELETE FROM audit_log WHERE timestamp < NOW() - INTERVAL '90 days';

    -- Clean up expired cordons
    UPDATE digital_cordons
    SET status = 'expired', deactivated_at = NOW()
    WHERE expires_at < NOW() AND status = 'active';

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automated updates
CREATE OR REPLACE FUNCTION update_analytics()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_ncrp_timestamp BEFORE UPDATE ON ncrp_complaints
    FOR EACH ROW EXECUTE FUNCTION update_analytics();

CREATE TRIGGER update_bank_transactions_timestamp BEFORE UPDATE ON bank_transactions
    FOR EACH ROW EXECUTE FUNCTION update_analytics();

-- Views for analytics
CREATE OR REPLACE VIEW real_time_intelligence AS
SELECT
    c.id,
    c.complaint_id,
    c.scam_type,
    c.amount,
    c.anonymized_location,
    c.complaint_timestamp,
    p.prediction_id,
    p.risk_score,
    p.confidence,
    p.top_hotspots,
    dc.status as cordon_status,
    dc.expires_at as cordon_expires
FROM ncrp_complaints c
LEFT JOIN ai_predictions p ON ST_DWithin(c.anonymized_location, ST_GeomFromText(ST_AsText(p.top_hotpoints->>0->'location'), 4326), 5000)
LEFT JOIN digital_cordons dc ON dc.prediction_id = p.id AND dc.status = 'active'
WHERE c.created_at >= NOW() - INTERVAL '24 hours';

CREATE OR REPLACE VIEW performance_dashboard AS
SELECT
    DATE_TRUNC('hour', a.created_at) as hour_bucket,
    COUNT(*) as total_predictions,
    AVG(a.confidence) as avg_confidence,
    AVG(a.risk_score) as avg_risk_score,
    COUNT(CASE WHEN f.outcome = 'confirmed' THEN 1 END) as confirmed_cases,
    COUNT(CASE WHEN f.outcome = 'false' THEN 1 END) as false_cases,
    AVG(CASE WHEN f.outcome = 'confirmed' THEN 1 WHEN f.outcome = 'false' THEN 0 ELSE NULL END)::DECIMAL as accuracy_rate
FROM ai_predictions a
LEFT JOIN feedback_loop f ON f.prediction_id = a.id
WHERE a.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', a.created_at)
ORDER BY hour_bucket DESC;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO aegis_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO aegis_user;