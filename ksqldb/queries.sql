-- CrisisFlow ksqlDB Queries
-- Run these queries in Confluent Cloud ksqlDB interface

-- =====================================================
-- STEP 1: Create Streams for Raw Events
-- =====================================================

-- Create stream for weather risk events
CREATE STREAM IF NOT EXISTS weather_stream (
    event_id VARCHAR,
    source VARCHAR,
    location STRUCT<
        name VARCHAR,
        lat DOUBLE,
        lon DOUBLE
    >,
    data STRUCT<
        fire_index DOUBLE,
        flood_index DOUBLE,
        temperature DOUBLE,
        humidity DOUBLE,
        wind_speed DOUBLE,
        wind_direction DOUBLE,
        precipitation_intensity DOUBLE
    >,
    risk_level VARCHAR,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC='weather_risks',
    VALUE_FORMAT='JSON',
    PARTITIONS=3
);

-- Create stream for social signals
CREATE STREAM IF NOT EXISTS social_stream (
    event_id VARCHAR,
    source VARCHAR,
    location STRUCT<
        lat DOUBLE,
        lon DOUBLE
    >,
    data STRUCT<
        text VARCHAR,
        category VARCHAR,
        urgency VARCHAR,
        verified BOOLEAN
    >,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC='social_signals',
    VALUE_FORMAT='JSON',
    PARTITIONS=3
);

-- =====================================================
-- STEP 2: Create Aggregation Tables (Hotspots)
-- =====================================================

-- Aggregate weather risks by grid cell (0.5 degree ~ 55km)
-- This creates a continuously updating table of weather hotspots
CREATE TABLE IF NOT EXISTS weather_hotspots AS
SELECT
    ROUND(location->lat * 2) / 2 AS grid_lat,
    ROUND(location->lon * 2) / 2 AS grid_lon,
    COUNT(*) AS event_count,
    AVG(data->fire_index) AS avg_fire_index,
    AVG(data->flood_index) AS avg_flood_index,
    MAX(data->fire_index) AS max_fire_index,
    MAX(data->flood_index) AS max_flood_index,
    COLLECT_LIST(risk_level) AS risk_levels,
    MAX(CASE
        WHEN risk_level = 'critical' THEN 4
        WHEN risk_level = 'high' THEN 3
        WHEN risk_level = 'moderate' THEN 2
        WHEN risk_level = 'low' THEN 1
        ELSE 0
    END) AS max_risk_score
FROM weather_stream
WINDOW TUMBLING (SIZE 30 MINUTES)
GROUP BY ROUND(location->lat * 2) / 2, ROUND(location->lon * 2) / 2
EMIT CHANGES;

-- Aggregate social signals by grid cell
CREATE TABLE IF NOT EXISTS social_hotspots AS
SELECT
    ROUND(location->lat * 2) / 2 AS grid_lat,
    ROUND(location->lon * 2) / 2 AS grid_lon,
    COUNT(*) AS report_count,
    COUNT(CASE WHEN data->urgency = 'critical' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN data->urgency = 'high' THEN 1 END) AS high_count,
    COUNT(CASE WHEN data->verified = true THEN 1 END) AS verified_count,
    COLLECT_LIST(STRUCT(
        text := data->text,
        category := data->category,
        urgency := data->urgency
    )) AS recent_reports
FROM social_stream
WINDOW TUMBLING (SIZE 30 MINUTES)
GROUP BY ROUND(location->lat * 2) / 2, ROUND(location->lon * 2) / 2
EMIT CHANGES;

-- =====================================================
-- STEP 3: Create Combined Hotspot View
-- =====================================================

-- Combined hotspots with both weather and social data
CREATE TABLE IF NOT EXISTS combined_hotspots AS
SELECT
    w.grid_lat AS grid_lat,
    w.grid_lon AS grid_lon,
    w.event_count AS weather_event_count,
    w.avg_fire_index AS avg_fire_index,
    w.avg_flood_index AS avg_flood_index,
    w.max_fire_index AS max_fire_index,
    w.max_flood_index AS max_flood_index,
    w.max_risk_score AS weather_risk_score,
    COALESCE(s.report_count, 0) AS social_report_count,
    COALESCE(s.critical_count, 0) AS social_critical_count,
    COALESCE(s.high_count, 0) AS social_high_count,
    COALESCE(s.verified_count, 0) AS social_verified_count,
    -- Calculate combined risk score
    CASE
        WHEN w.max_risk_score = 4 OR COALESCE(s.critical_count, 0) > 2 THEN 'critical'
        WHEN w.max_risk_score >= 3 OR COALESCE(s.critical_count, 0) > 0 THEN 'high'
        WHEN w.max_risk_score >= 2 OR COALESCE(s.high_count, 0) > 2 THEN 'moderate'
        ELSE 'low'
    END AS combined_risk_level,
    w.ROWTIME AS window_time
FROM weather_hotspots w
LEFT JOIN social_hotspots s
    ON w.grid_lat = s.grid_lat AND w.grid_lon = s.grid_lon
EMIT CHANGES;

-- =====================================================
-- STEP 4: Create Real-time Alert Stream
-- =====================================================

-- Create stream of critical alerts (for immediate notification)
CREATE STREAM IF NOT EXISTS critical_alerts AS
SELECT
    grid_lat,
    grid_lon,
    combined_risk_level AS risk_level,
    weather_event_count,
    social_report_count,
    social_critical_count,
    avg_fire_index,
    avg_flood_index,
    TIMESTAMPTOSTRING(window_time, 'yyyy-MM-dd HH:mm:ss') AS alert_time,
    'CRITICAL: High risk detected at grid ' + CAST(grid_lat AS STRING) + ',' + CAST(grid_lon AS STRING) AS alert_message
FROM combined_hotspots
WHERE combined_risk_level = 'critical'
EMIT CHANGES;

-- =====================================================
-- STEP 5: Create Statistics Table
-- =====================================================

-- Overall statistics table (for dashboard metrics)
CREATE TABLE IF NOT EXISTS crisis_statistics AS
SELECT
    'global' AS region,
    COUNT(*) AS total_hotspots,
    COUNT(CASE WHEN combined_risk_level = 'critical' THEN 1 END) AS critical_hotspots,
    COUNT(CASE WHEN combined_risk_level = 'high' THEN 1 END) AS high_hotspots,
    AVG(avg_fire_index) AS global_avg_fire_index,
    AVG(avg_flood_index) AS global_avg_flood_index,
    SUM(social_report_count) AS total_social_reports,
    SUM(social_critical_count) AS total_critical_reports
FROM combined_hotspots
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY 'global'
EMIT CHANGES;

-- =====================================================
-- EXAMPLE QUERIES (for testing)
-- =====================================================

-- Query latest weather events
-- SELECT * FROM weather_stream EMIT CHANGES LIMIT 10;

-- Query latest social signals
-- SELECT * FROM social_stream EMIT CHANGES LIMIT 10;

-- Query current hotspots
-- SELECT * FROM combined_hotspots WHERE combined_risk_level IN ('critical', 'high');

-- Query critical alerts
-- SELECT * FROM critical_alerts EMIT CHANGES;

-- Query global statistics
-- SELECT * FROM crisis_statistics;

-- =====================================================
-- CLEANUP (if needed to restart)
-- =====================================================

-- DROP TABLE IF EXISTS crisis_statistics;
-- DROP TABLE IF EXISTS combined_hotspots;
-- DROP TABLE IF EXISTS social_hotspots;
-- DROP TABLE IF EXISTS weather_hotspots;
-- DROP STREAM IF EXISTS critical_alerts;
-- DROP STREAM IF EXISTS social_stream;
-- DROP STREAM IF EXISTS weather_stream;