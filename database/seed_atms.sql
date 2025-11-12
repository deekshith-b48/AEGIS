-- Seed high-risk ATMs in major Indian cities
-- Delhi NCR
INSERT INTO high_risk_atms (name, location, tags, city) VALUES
('Connaught Place ATM', 'POINT(77.2084 28.6314)', ARRAY['commercial', 'high_traffic'], 'Delhi'),
('New Delhi Railway Station ATM', 'POINT(77.2160 28.6448)', ARRAY['railway_station', 'high_traffic'], 'Delhi'),
('ISBT Kashmere Gate ATM', 'POINT(77.2295 28.6692)', ARRAY['bus_stand', 'highway'], 'Delhi'),
('IGI Airport Terminal 3 ATM', 'POINT(77.1036 28.5665)', ARRAY['airport', 'high_traffic'], 'Delhi'),
('Karol Bagh Market ATM', 'POINT(77.1902 28.6514)', ARRAY['commercial', 'market'], 'Delhi'),
('Lajpat Nagar Market ATM', 'POINT(77.2428 28.5674)', ARRAY['commercial', 'market'], 'Delhi'),
('Dwarka Sector 21 ATM', 'POINT(77.0582 28.5814)', ARRAY['metro_station', 'commercial'], 'Delhi'),
('Anand Vihar ISBT ATM', 'POINT(77.3150 28.6474)', ARRAY['bus_stand', 'highway'], 'Delhi'),
('Sarojini Nagar Market ATM', 'POINT(77.2075 28.5711)', ARRAY['market', 'commercial'], 'Delhi'),
('Chandni Chowk ATM', 'POINT(77.2306 28.6506)', ARRAY['commercial', 'high_traffic'], 'Delhi'),

-- Mumbai
('CSMT Railway Station ATM', 'POINT(72.8351 18.9402)', ARRAY['railway_station', 'high_traffic'], 'Mumbai'),
('Dadar Railway Station ATM', 'POINT(72.8440 19.0190)', ARRAY['railway_station', 'high_traffic'], 'Mumbai'),
('Bandra-Worli Sea Link ATM', 'POINT(72.8182 19.0538)', ARRAY['highway', 'high_traffic'], 'Mumbai'),
('Andheri Railway Station ATM', 'POINT(72.8466 19.1196)', ARRAY['railway_station', 'commercial'], 'Mumbai'),
('Thane Railway Station ATM', 'POINT(72.9781 19.1971)', ARRAY['railway_station', 'high_traffic'], 'Mumbai'),

-- Bengaluru
('Majestic Bus Stand ATM', 'POINT(77.5810 12.9767)', ARRAY['bus_stand', 'highway'], 'Bengaluru'),
('KSR Railway Station ATM', 'POINT(77.5696 12.9784)', ARRAY['railway_station', 'high_traffic'], 'Bengaluru'),
('Koramangala Commercial ATM', 'POINT(77.6238 12.9345)', ARRAY['commercial', 'market'], 'Bengaluru'),
('Whitefield ATM', 'POINT(77.7487 12.9698)', ARRAY['commercial', 'highway'], 'Bengaluru'),
('Electronic City ATM', 'POINT(77.6783 12.8356)', ARRAY['commercial', 'highway'], 'Bengaluru'),

-- Hyderabad
('Secunderabad Railway Station ATM', 'POINT(78.4968 17.4403)', ARRAY['railway_station', 'high_traffic'], 'Hyderabad'),
('MG Bus Station ATM', 'POINT(78.4747 17.4132)', ARRAY['bus_stand', 'highway'], 'Hyderabad'),
('HITEC City ATM', 'POINT(78.3741 17.4485)', ARRAY['commercial', 'highway'], 'Hyderabad'),
('Banjara Hills ATM', 'POINT(78.4513 17.4275)', ARRAY['commercial', 'high_traffic'], 'Hyderabad'),

-- Chennai
('Chennai Central Railway Station ATM', 'POINT(80.2799 13.0827)', ARRAY['railway_station', 'high_traffic'], 'Chennai'),
('Koyambedu Bus Stand ATM', 'POINT(80.1955 13.0647)', ARRAY['bus_stand', 'highway'], 'Chennai'),
('T Nagar Commercial ATM', 'POINT(80.2341 13.0410)', ARRAY['commercial', 'market'], 'Chennai'),
('OMR IT Corridor ATM', 'POINT(80.2425 12.8942)', ARRAY['commercial', 'highway'], 'Chennai'),

-- Kolkata
('Howrah Railway Station ATM', 'POINT(88.3426 22.5778)', ARRAY['railway_station', 'high_traffic'], 'Kolkata'),
('Sealdah Railway Station ATM', 'POINT(88.3710 22.5441)', ARRAY['railway_station', 'high_traffic'], 'Kolkata'),
('Esplanade Bus Stand ATM', 'POINT(88.3493 22.5645)', ARRAY['bus_stand', 'highway'], 'Kolkata'),
('Salt Lake City ATM', 'POINT(88.4279 22.6005)', ARRAY['commercial', 'market'], 'Kolkata'),

-- Additional high-risk locations
('Delhi-Gurgaon Highway ATM', 'POINT(77.0835 28.4604)', ARRAY['highway', 'commercial'], 'Gurgaon'),
('Noida Expressway ATM', 'POINT(77.3511 28.5355)', ARRAY['highway', 'commercial'], 'Noida'),
('Pune Railway Station ATM', 'POINT(73.8567 18.5295)', ARRAY['railway_station', 'high_traffic'], 'Pune'),
('Ahmedabad Railway Station ATM', 'POINT(72.6369 23.0304)', ARRAY['railway_station', 'high_traffic'], 'Ahmedabad'),
('Jaipur Railway Station ATM', 'POINT(75.7940 26.9124)', ARRAY['railway_station', 'high_traffic'], 'Jaipur');

-- Insert initial system metrics record
INSERT INTO system_metrics (metric_date, total_predictions, confirmed_predictions, false_predictions)
VALUES (CURRENT_DATE, 0, 0, 0);