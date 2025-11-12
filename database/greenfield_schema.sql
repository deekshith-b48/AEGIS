-- Project AEGIS Greenfield Implementation Database Schema
-- Supabase PostgreSQL + PostGIS (RLS disabled for MVP)

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Core Tables for Greenfield Implementation

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

-- 3. hotspots table - AI prediction results (one per complaint max)
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

-- Create spatial indexes for performance (GIST indexes on all GEOGRAPHY columns)
CREATE INDEX idx_complaints_location ON complaints USING GIST (victim_location);
CREATE INDEX idx_high_risk_atms_location ON high_risk_atms USING GIST (location);
CREATE INDEX idx_hotspots_location ON hotspots USING GIST (hotspot_location);
CREATE INDEX idx_cordons_center ON cordons USING GIST (center);

-- Create temporal indexes for performance
CREATE INDEX idx_complaints_created_at ON complaints (created_at DESC);
CREATE INDEX idx_hotspots_predicted_at ON hotspots (predicted_at DESC);
CREATE INDEX idx_cordons_expires_at ON cordons (expires_at DESC);

-- RLS DISABLED for MVP as per specification
-- Note: Row Level Security is disabled for demonstration purposes

-- PostGIS Functions for Spatial Queries

-- Function to find ATMs within radius using ST_DWithin
CREATE OR REPLACE FUNCTION find_atms_within_radius(
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

-- Function to find nearest ATM in same city
CREATE OR REPLACE FUNCTION find_nearest_city_atm(
    victim_lat FLOAT,
    victim_lon FLOAT
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
    WITH nearest_city AS (
        SELECT city, MIN(ST_Distance(
            location,
            ST_GeomFromText('POINT(' || victim_lon || ' ' || victim_lat || ')', 4326)
        )) as min_distance
        FROM high_risk_atms
        GROUP BY city
        ORDER BY min_distance
        LIMIT 1
    )
    SELECT
        atm.id,
        atm.name,
        atm.location,
        atm.tags,
        atm.city,
        ST_Distance(
            atm.location,
            ST_GeomFromText('POINT(' || victim_lon || ' ' || victim_lat || ')', 4326)
        ) as distance_meters
    FROM high_risk_atms atm, nearest_city nc
    WHERE atm.city = nc.city
    ORDER BY distance_meters
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old data (7 days retention)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete complaints older than 7 days (cascade will delete related records)
    DELETE FROM complaints
    WHERE created_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get complaints and hotspots for risk heatmap (last 90 minutes)
CREATE OR REPLACE FUNCTION get_risk_heatmap()
RETURNS TABLE (
    complaints_geojson JSONB,
    hotspots_geojson JSONB,
    cordons_geojson JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(victim_location),
                    'properties', jsonb_build_object(
                        'id', id,
                        'fraud_type', fraud_type,
                        'amount', amount,
                        'created_at', created_at
                    )
                )
            )
        ) as complaints_geojson,
        jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(hotspot_location),
                    'properties', jsonb_build_object(
                        'id', id,
                        'complaint_id', complaint_id,
                        'location_name', location_name,
                        'confidence', confidence,
                        'time_window_mins', time_window_mins,
                        'predicted_at', predicted_at
                    )
                )
            )
        ) as hotspots_geojson,
        jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', jsonb_build_object(
                        'type', 'Polygon',
                        'coordinates', Array[
                            -- Simplified circle generation for cordons
                            Array[
                                -- This would be generated properly in the application
                                [ST_X(center) - 0.02, ST_Y(center) - 0.02],
                                [ST_X(center) + 0.02, ST_Y(center) - 0.02],
                                [ST_X(center) + 0.02, ST_Y(center) + 0.02],
                                [ST_X(center) - 0.02, ST_Y(center) + 0.02],
                                [ST_X(center) - 0.02, ST_Y(center) - 0.02]
                            ]
                        ]
                    ),
                    'properties', jsonb_build_object(
                        'id', id,
                        'hotspot_id', hotspot_id,
                        'radius_meters', radius_meters,
                        'expires_at', expires_at,
                        'activated_at', activated_at
                    )
                )
            )
        ) as cordons_geojson
    FROM (
        SELECT id, victim_location, fraud_type, amount, created_at,
               NULL as hotspot_location, NULL as complaint_id, NULL as location_name,
               NULL as confidence, NULL as time_window_mins, NULL as predicted_at,
               NULL as center, NULL as hotspot_id, NULL as radius_meters,
               NULL as expires_at, NULL as activated_at
        FROM complaints
        WHERE created_at >= NOW() - INTERVAL '90 minutes'

        UNION ALL

        SELECT NULL, NULL, NULL, NULL, NULL,
               hotspot_location, complaint_id, location_name, confidence, time_window_mins, predicted_at,
               NULL, NULL, NULL, NULL, NULL
        FROM hotspots
        WHERE predicted_at >= NOW() - INTERVAL '90 minutes'

        UNION ALL

        SELECT NULL, NULL, NULL, NULL, NULL,
               NULL, NULL, NULL, NULL, NULL, NULL,
               center, hotspot_id, radius_meters, expires_at, activated_at
        FROM cordons
        WHERE expires_at > NOW()
    ) combined_data;
END;
$$ LANGUAGE plpgsql;