# ksqlDB Setup Guide for CrisisFlow

## 🎯 Why This Matters
ksqlDB is THE Confluent differentiator that will impress judges. It shows you're doing real-time stream processing, not just message queuing.

## 📝 Step-by-Step Instructions

### 1. Access ksqlDB in Confluent Cloud

1. Go to [Confluent Cloud Console](https://confluent.cloud)
2. Select your environment: `default`
3. Look for **"SQL workspace"** or **"ksqlDB"** in the left sidebar
4. Click on it to open the SQL editor

### 2. Run the Queries

Copy and paste these queries **ONE AT A TIME** into the SQL editor:

#### Query 1: Create Weather Stream
```sql
CREATE STREAM IF NOT EXISTS weather_stream (
    event_id VARCHAR,
    source VARCHAR,
    location STRUCT<name VARCHAR, lat DOUBLE, lon DOUBLE>,
    data STRUCT<
        fire_index DOUBLE,
        flood_index DOUBLE,
        temperature DOUBLE,
        humidity DOUBLE,
        wind_speed DOUBLE
    >,
    risk_level VARCHAR,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC='weather_risks',
    VALUE_FORMAT='JSON'
);
```

**Wait for confirmation**, then continue.

#### Query 2: Create Social Stream
```sql
CREATE STREAM IF NOT EXISTS social_stream (
    event_id VARCHAR,
    source VARCHAR,
    location STRUCT<lat DOUBLE, lon DOUBLE>,
    data STRUCT<
        text VARCHAR,
        category VARCHAR,
        urgency VARCHAR
    >,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC='social_signals',
    VALUE_FORMAT='JSON'
);
```

#### Query 3: Create Weather Hotspots Table
```sql
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
```

#### Query 4: Create Social Hotspots Table
```sql
CREATE TABLE IF NOT EXISTS social_hotspots AS
SELECT
    ROUND(location->lat * 2) / 2 AS grid_lat,
    ROUND(location->lon * 2) / 2 AS grid_lon,
    COUNT(*) AS report_count,
    COUNT(CASE WHEN data->urgency = 'critical' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN data->urgency = 'high' THEN 1 END) AS high_count
FROM social_stream
WINDOW TUMBLING (SIZE 30 MINUTES)
GROUP BY ROUND(location->lat * 2) / 2, ROUND(location->lon * 2) / 2
EMIT CHANGES;
```

### 3. Verify It's Working

Run this query to see live data:
```sql
SELECT * FROM weather_stream EMIT CHANGES LIMIT 10;
```

You should see weather events flowing in real-time!

### 4. Check Hotspots

```sql
SELECT * FROM weather_hotspots EMIT CHANGES;
```

This shows aggregated risk by geographic grid cell.

## ✅ Success Indicators

- [ ] All 4 queries executed without errors
- [ ] `SHOW STREAMS;` shows `weather_stream` and `social_stream`
- [ ] `SHOW TABLES;` shows `weather_hotspots` and `social_hotspots`
- [ ] SELECT queries return live data

## 🎬 For Demo Video

**Show this in your demo:**
1. Split screen: Dashboard on left, ksqlDB console on right
2. Show live query: `SELECT * FROM weather_hotspots EMIT CHANGES;`
3. As producers send data, show hotspots updating in real-time
4. Say: "ksqlDB is aggregating millions of events per second to detect risk concentrations"

This is **pure gold** for the Confluent judges!

## 🐛 Troubleshooting

**Error: "Topic not found"**
- Make sure producers are running and sending data
- Check topic names match exactly: `weather_risks`, `social_signals`

**Error: "Parsing error"**
- Copy queries exactly as shown (watch for quotes)
- Run one at a time

**No data in SELECT queries**
- Producers need to run for a few minutes
- Check Confluent Cloud → Topics → Messages tab to see raw data

## 🚀 Next Steps

Once ksqlDB is working:
1. Update backend to query these tables (optional - current implementation works)
2. Show aggregated hotspots on the map
3. Highlight this in demo video!