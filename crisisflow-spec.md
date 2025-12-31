# CrisisFlow — Technical Specification & Architecture

## Document Purpose
This is the complete technical specification for building CrisisFlow, a real-time disaster intelligence platform. Use this document with Claude Code to build the entire project.

---

## 1. Project Overview

### 1.1 What We're Building
A real-time disaster intelligence dashboard that:
- Streams fire risk, flood risk, and weather data from Tomorrow.io
- Streams simulated social signals (disaster tweets)
- Processes everything through Confluent Kafka
- Uses Google Gemini to synthesize situation reports
- Displays everything on a live map with actionable alerts

### 1.2 Hackathon Context
- **Competition:** AI Partner Catalyst (Devpost)
- **Challenge Track:** Confluent Challenge
- **Deadline:** 11 days
- **Prize:** $12,500 first place
- **Requirements:** Must use Google Cloud (Vertex AI/Gemini) + Confluent

### 1.3 One-Sentence Pitch
"CrisisFlow predicts where disasters will escalate before emergency calls flood in, by streaming real-time risk data through Confluent and synthesizing alerts with Gemini AI."

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                   │
│                                                                             │
│   ┌─────────────────────┐          ┌─────────────────────┐                 │
│   │   TOMORROW.IO API   │          │   CRISIS NLP DATA   │                 │
│   │                     │          │                     │                 │
│   │  • Fire Index       │          │  • Disaster tweets  │                 │
│   │  • Flood Index      │          │  • Geo-located      │                 │
│   │  • Weather data     │          │  • Pre-labeled      │                 │
│   └──────────┬──────────┘          └──────────┬──────────┘                 │
│              │                                 │                            │
└──────────────┼─────────────────────────────────┼────────────────────────────┘
               │                                 │
               ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCER LAYER                                    │
│                                                                             │
│   ┌─────────────────────┐          ┌─────────────────────┐                 │
│   │  weather_producer   │          │  social_producer    │                 │
│   │      (Python)       │          │     (Python)        │                 │
│   └──────────┬──────────┘          └──────────┬──────────┘                 │
│              │                                 │                            │
└──────────────┼─────────────────────────────────┼────────────────────────────┘
               │                                 │
               ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFLUENT CLOUD                                     │
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │  weather_risks  │    │  social_signals │    │    hotspots     │        │
│   │     (topic)     │    │     (topic)     │    │    (table)      │        │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│            │                      │                      │                  │
│            └──────────────────────┼──────────────────────┘                  │
│                                   │                                         │
│                          ┌────────▼────────┐                               │
│                          │     ksqlDB      │                               │
│                          │  (aggregation)  │                               │
│                          └────────┬────────┘                               │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                 │
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │  GET /events    │    │  GET /hotspots  │    │  GET /alert     │        │
│   │                 │    │                 │    │                 │        │
│   │ Returns latest  │    │ Returns ksqlDB  │    │ Calls Gemini    │        │
│   │ from all topics │    │ aggregations    │    │ for synthesis   │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
│                         Google Cloud Run                                    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                                                                 │      │
│   │   ┌─────────────────────────────┐  ┌─────────────────────────┐ │      │
│   │   │                             │  │                         │ │      │
│   │   │         MAP PANEL           │  │     ALERT PANEL         │ │      │
│   │   │                             │  │                         │ │      │
│   │   │   • Fire risk markers (🔥)  │  │  • AI situation report  │ │      │
│   │   │   • Flood risk markers (🌊) │  │  • Recommended actions  │ │      │
│   │   │   • Social markers (📱)     │  │  • Live statistics      │ │      │
│   │   │   • Hotspot highlights      │  │  • Regenerate button    │ │      │
│   │   │                             │  │                         │ │      │
│   │   └─────────────────────────────┘  └─────────────────────────┘ │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│                    Hosted on Cloud Run / Vercel / Netlify                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Data Source | Tomorrow.io API | Fire, flood, weather data |
| Data Source | CrisisNLP Dataset | Simulated disaster tweets |
| Streaming | Confluent Cloud | Managed Kafka + ksqlDB |
| Backend | Python FastAPI | API server |
| AI | Google Gemini API | Alert synthesis |
| Frontend | React + Leaflet | Dashboard UI |
| Hosting | Google Cloud Run | Backend deployment |
| Frontend Hosting | Vercel / Netlify | Frontend deployment |

---

## 3. Repository Structure

```
crisisflow/
│
├── README.md                      # Project overview + setup instructions
├── .env.example                   # Template for environment variables
├── .gitignore
├── docker-compose.yml             # Local development setup
├── architecture.png               # Architecture diagram for Devpost
│
├── producers/
│   ├── __init__.py
│   ├── requirements.txt           # confluent-kafka, requests, python-dotenv
│   ├── config.py                  # Shared configuration
│   ├── weather_producer.py        # Tomorrow.io → Kafka
│   ├── social_producer.py         # Simulated tweets → Kafka
│   └── data/
│       └── crisis_tweets.json     # Pre-loaded CrisisNLP data
│
├── backend/
│   ├── __init__.py
│   ├── requirements.txt           # fastapi, uvicorn, confluent-kafka, google-generativeai
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration management
│   ├── kafka_consumer.py          # Kafka consumption utilities
│   ├── gemini_client.py           # Gemini API wrapper
│   ├── models.py                  # Pydantic models
│   └── Dockerfile                 # For Cloud Run deployment
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js             # Using Vite for React
│   ├── index.html
│   ├── public/
│   │   └── favicon.ico
│   └── src/
│       ├── main.jsx               # Entry point
│       ├── App.jsx                # Main application
│       ├── App.css                # Global styles
│       ├── components/
│       │   ├── Map.jsx            # Leaflet map component
│       │   ├── AlertPanel.jsx     # AI alerts sidebar
│       │   ├── StatsPanel.jsx     # Live statistics
│       │   └── Legend.jsx         # Map legend
│       └── hooks/
│           └── useEvents.js       # Custom hook for polling API
│
├── ksqldb/
│   └── queries.sql                # ksqlDB stream/table definitions
│
└── scripts/
    ├── setup_confluent.sh         # Confluent Cloud setup helper
    └── deploy.sh                  # Deployment script
```

---

## 4. Data Models

### 4.1 Weather Risk Event (Tomorrow.io → Kafka)

```json
{
  "event_id": "uuid-v4",
  "source": "tomorrow.io",
  "location": {
    "name": "Houston",
    "lat": 29.7604,
    "lon": -95.3698
  },
  "data": {
    "fire_index": 72,
    "flood_index": 45,
    "temperature": 34.5,
    "humidity": 78,
    "wind_speed": 15.3,
    "wind_direction": 180,
    "precipitation_probability": 60
  },
  "risk_level": "high",
  "timestamp": "2025-12-20T14:30:00Z"
}
```

### 4.2 Social Signal Event (Simulated → Kafka)

```json
{
  "event_id": "uuid-v4",
  "source": "social",
  "location": {
    "lat": 29.7504,
    "lon": -95.3578
  },
  "data": {
    "text": "Massive flooding on Highway 45, cars stranded, need help!",
    "category": "flood",
    "urgency": "high",
    "verified": false
  },
  "timestamp": "2025-12-20T14:32:00Z"
}
```

### 4.3 Hotspot (ksqlDB Aggregation)

```json
{
  "grid_lat": 29.5,
  "grid_lon": -95.5,
  "event_count": 15,
  "avg_fire_index": 68,
  "avg_flood_index": 52,
  "social_count": 7,
  "risk_level": "critical",
  "window_start": "2025-12-20T14:00:00Z",
  "window_end": "2025-12-20T14:30:00Z"
}
```

### 4.4 AI Alert Response (Gemini)

```json
{
  "alert_id": "uuid-v4",
  "generated_at": "2025-12-20T14:35:00Z",
  "situation_report": "Critical conditions detected in Houston metropolitan area. Fire risk index elevated to 72 in northwest sector due to high temperatures and low humidity. Flood warnings active along Buffalo Bayou with 12 social media reports of road flooding. Conditions expected to worsen over next 6 hours.",
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Deploy fire prevention crews to northwest Houston",
      "reason": "Fire index above 70 threshold"
    },
    {
      "priority": 2,
      "action": "Issue flash flood warning for Buffalo Bayou area",
      "reason": "Rising flood index combined with social reports"
    },
    {
      "priority": 3,
      "action": "Pre-position rescue boats at Highway 45 and I-10 junction",
      "reason": "Historical flooding location with active reports"
    }
  ],
  "risk_summary": {
    "fire": "high",
    "flood": "critical",
    "overall": "critical"
  }
}
```

---

## 5. API Specifications

### 5.1 Backend API Endpoints

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "kafka_connected": true,
  "timestamp": "2025-12-20T14:30:00Z"
}
```

#### GET /api/events
Returns latest events from all streams.

**Query Parameters:**
- `limit` (optional): Max events per category (default: 50)

**Response:**
```json
{
  "weather": [
    { /* Weather Risk Event */ }
  ],
  "social": [
    { /* Social Signal Event */ }
  ],
  "last_updated": "2025-12-20T14:30:00Z"
}
```

#### GET /api/hotspots
Returns aggregated hotspots from ksqlDB.

**Response:**
```json
{
  "hotspots": [
    { /* Hotspot */ }
  ],
  "count": 5
}
```

#### POST /api/alert/generate
Generates AI situation report using Gemini.

**Request Body:**
```json
{
  "include_recommendations": true,
  "focus_area": {
    "lat": 29.76,
    "lon": -95.36,
    "radius_km": 50
  }
}
```

**Response:**
```json
{ /* AI Alert Response */ }
```

#### GET /api/locations
Returns monitored locations.

**Response:**
```json
{
  "locations": [
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321}
  ]
}
```

---

## 6. Component Specifications

### 6.1 Weather Producer (`producers/weather_producer.py`)

**Purpose:** Poll Tomorrow.io API and publish to Kafka.

**Behavior:**
1. Load list of monitored locations (5 US cities)
2. Every 5 minutes:
   - For each location, call Tomorrow.io realtime API
   - Extract: fireIndex, floodIndex, temperature, humidity, windSpeed
   - Calculate risk_level based on thresholds
   - Publish to `weather_risks` Kafka topic
3. Handle rate limiting (Tomorrow.io free tier: ~500 calls/day)
4. Log all activity

**Risk Level Calculation:**
```python
def calculate_risk_level(fire_index, flood_index):
    max_index = max(fire_index or 0, flood_index or 0)
    if max_index >= 70:
        return "critical"
    elif max_index >= 50:
        return "high"
    elif max_index >= 30:
        return "moderate"
    else:
        return "low"
```

**Configuration:**
```python
LOCATIONS = [
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
]

POLL_INTERVAL_SECONDS = 300  # 5 minutes
KAFKA_TOPIC = "weather_risks"
```

### 6.2 Social Producer (`producers/social_producer.py`)

**Purpose:** Simulate disaster-related social media posts.

**Behavior:**
1. Load pre-built crisis tweets from CrisisNLP dataset
2. Every 30-60 seconds (randomized):
   - Select random tweet from dataset
   - Add small random offset to coordinates (simulate spread)
   - Publish to `social_signals` Kafka topic
3. Vary frequency based on "disaster intensity" setting

**Crisis Tweet Dataset Structure:**
```json
[
  {
    "text": "Massive flooding on Highway 45, cars stranded!",
    "category": "flood",
    "base_lat": 29.76,
    "base_lon": -95.36,
    "urgency": "high"
  },
  {
    "text": "Smoke visible from downtown, fire trucks heading north",
    "category": "fire",
    "base_lat": 34.05,
    "base_lon": -118.24,
    "urgency": "medium"
  }
]
```

**Include 50-100 pre-written crisis tweets covering:**
- Floods (road flooding, rising water, evacuations)
- Fires (smoke sightings, evacuations, air quality)
- Storms (wind damage, power outages, debris)
- General distress (trapped, need help, injuries)

### 6.3 ksqlDB Queries (`ksqldb/queries.sql`)

```sql
-- Create stream for weather risk events
CREATE STREAM weather_stream (
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

-- Create stream for social signals
CREATE STREAM social_stream (
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

-- Aggregate weather risks by grid cell (0.5 degree ~ 55km)
CREATE TABLE weather_hotspots AS
SELECT 
    ROUND(location->lat * 2) / 2 AS grid_lat,
    ROUND(location->lon * 2) / 2 AS grid_lon,
    COUNT(*) AS event_count,
    AVG(data->fire_index) AS avg_fire_index,
    AVG(data->flood_index) AS avg_flood_index,
    MAX(risk_level) AS max_risk_level
FROM weather_stream
WINDOW TUMBLING (SIZE 30 MINUTES)
GROUP BY ROUND(location->lat * 2) / 2, ROUND(location->lon * 2) / 2
EMIT CHANGES;

-- Aggregate social signals by grid cell
CREATE TABLE social_hotspots AS
SELECT 
    ROUND(location->lat * 2) / 2 AS grid_lat,
    ROUND(location->lon * 2) / 2 AS grid_lon,
    COUNT(*) AS report_count,
    COLLECT_LIST(data->text) AS recent_reports
FROM social_stream
WINDOW TUMBLING (SIZE 30 MINUTES)
GROUP BY ROUND(location->lat * 2) / 2, ROUND(location->lon * 2) / 2
EMIT CHANGES;

-- Combined hotspots view (for querying)
CREATE TABLE combined_hotspots AS
SELECT 
    w.grid_lat,
    w.grid_lon,
    w.avg_fire_index,
    w.avg_flood_index,
    w.max_risk_level,
    s.report_count AS social_count
FROM weather_hotspots w
LEFT JOIN social_hotspots s 
    ON w.grid_lat = s.grid_lat AND w.grid_lon = s.grid_lon
EMIT CHANGES;
```

### 6.4 Backend API (`backend/main.py`)

**FastAPI Application Structure:**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Kafka consumer
    await kafka_consumer.start()
    yield
    # Shutdown: Close connections
    await kafka_consumer.stop()

app = FastAPI(
    title="CrisisFlow API",
    description="Real-time disaster intelligence platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/api/health")
@app.get("/api/events")
@app.get("/api/hotspots")
@app.post("/api/alert/generate")
@app.get("/api/locations")
```

### 6.5 Gemini Client (`backend/gemini_client.py`)

**Prompt Template:**

```python
ALERT_PROMPT_TEMPLATE = """
You are CrisisFlow AI, a disaster response intelligence system. Analyze the following real-time data and generate a situation report.

## CURRENT CONDITIONS

### Weather Risk Data (Last 30 minutes)
{weather_data}

### Social Media Signals (Last 30 minutes)
{social_data}

### Aggregated Hotspots
{hotspot_data}

## YOUR TASK

Generate a response in the following JSON format:
{{
    "situation_report": "A 2-3 sentence summary of the current situation, highlighting the most critical threats and their locations.",
    "recommended_actions": [
        {{
            "priority": 1,
            "action": "Specific actionable recommendation",
            "reason": "Why this action is needed"
        }},
        {{
            "priority": 2,
            "action": "Second recommendation",
            "reason": "Why this action is needed"
        }},
        {{
            "priority": 3,
            "action": "Third recommendation",
            "reason": "Why this action is needed"
        }}
    ],
    "risk_summary": {{
        "fire": "low|moderate|high|critical",
        "flood": "low|moderate|high|critical",
        "overall": "low|moderate|high|critical"
    }}
}}

Be specific about locations. Prioritize life safety. Be concise but actionable.
"""
```

### 6.6 Frontend Components

#### App.jsx (Main Layout)
```jsx
function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>🚨 CrisisFlow</h1>
        <span className="live-indicator">● LIVE</span>
      </header>
      <main className="main">
        <div className="map-container">
          <Map />
          <Legend />
        </div>
        <aside className="sidebar">
          <AlertPanel />
          <StatsPanel />
        </aside>
      </main>
    </div>
  );
}
```

#### Map.jsx (Leaflet Map)
```jsx
// Features:
// - Centered on US (lat: 39.8, lon: -98.5, zoom: 4)
// - Fire risk markers: Red circles, size based on fire_index
// - Flood risk markers: Blue circles, size based on flood_index  
// - Social markers: Orange circles, smaller
// - Hotspot highlights: Semi-transparent polygons for grid cells
// - Popups on click showing details
// - Auto-refresh every 10 seconds
```

#### AlertPanel.jsx (AI Alerts)
```jsx
// Features:
// - Display situation_report text
// - List recommended_actions as cards
// - Show risk_summary as colored badges
// - "Regenerate Alert" button
// - Loading state while generating
// - Timestamp of last generation
```

#### StatsPanel.jsx (Live Statistics)
```jsx
// Features:
// - Count of active fire risks (by severity)
// - Count of flood warnings (by severity)
// - Count of social reports (last 30 min)
// - Count of critical hotspots
// - Auto-refresh every 10 seconds
```

---

## 7. Configuration & Environment Variables

### 7.1 Environment Variables (`.env`)

```bash
# Tomorrow.io
TOMORROW_API_KEY=your_api_key_here

# Confluent Cloud
CONFLUENT_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
CONFLUENT_API_KEY=your_api_key
CONFLUENT_API_SECRET=your_api_secret

# Google Cloud / Gemini
GOOGLE_API_KEY=your_gemini_api_key

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
POLL_INTERVAL=300
```

### 7.2 Confluent Cloud Setup

1. Create account at confluent.cloud
2. Create a Basic cluster (free tier works)
3. Create topics:
   - `weather_risks` (partitions: 3, retention: 24 hours)
   - `social_signals` (partitions: 3, retention: 24 hours)
4. Create API key with full access
5. Enable ksqlDB (if using aggregations)
6. Note bootstrap server URL

---

## 8. Build Order (Step by Step)

### Phase 1: Foundation (Day 1-2)

```
Step 1: Project Setup
├── Create repository structure
├── Initialize Python virtual environments
├── Initialize React app with Vite
├── Create .env.example and .gitignore
└── Write README with setup instructions

Step 2: Configuration
├── Create config.py for producers
├── Create config.py for backend
├── Test all API keys work
└── Verify Confluent Cloud connection
```

### Phase 2: Data Pipeline (Day 3-4)

```
Step 3: Weather Producer
├── Implement Tomorrow.io API client
├── Implement Kafka producer
├── Add risk level calculation
├── Test with single location
└── Expand to all 5 locations

Step 4: Social Producer
├── Create crisis_tweets.json dataset (50+ tweets)
├── Implement simulated producer
├── Add randomization for coordinates
├── Test publication to Kafka
└── Verify messages in Confluent Cloud UI
```

### Phase 3: Stream Processing (Day 5-6)

```
Step 5: ksqlDB Setup
├── Connect to ksqlDB in Confluent Cloud
├── Create weather_stream
├── Create social_stream
├── Create weather_hotspots table
├── Create social_hotspots table
└── Test queries return data

Step 6: Backend API - Basic
├── Create FastAPI application
├── Implement /api/health endpoint
├── Implement Kafka consumer utility
├── Implement /api/events endpoint
├── Test endpoints return data
└── Add CORS middleware
```

### Phase 4: AI Integration (Day 7-8)

```
Step 7: Gemini Integration
├── Create Gemini client wrapper
├── Implement prompt template
├── Implement /api/alert/generate endpoint
├── Test alert generation
└── Refine prompt for better outputs

Step 8: Backend API - Complete
├── Implement /api/hotspots endpoint
├── Implement /api/locations endpoint
├── Add error handling
├── Add request logging
└── Test all endpoints end-to-end
```

### Phase 5: Frontend (Day 9-10)

```
Step 9: Frontend - Map
├── Set up React + Vite project
├── Install Leaflet dependencies
├── Create Map component
├── Add marker rendering for weather events
├── Add marker rendering for social events
├── Add popup details
└── Implement auto-refresh

Step 10: Frontend - Panels
├── Create AlertPanel component
├── Create StatsPanel component
├── Create Legend component
├── Style with CSS (dark theme)
├── Connect to backend API
└── Test full UI flow
```

### Phase 6: Polish & Deploy (Day 11)

```
Step 11: Deployment
├── Create Dockerfile for backend
├── Deploy backend to Cloud Run
├── Deploy frontend to Vercel/Netlify
├── Update frontend API URL
├── Test production deployment
└── Fix any production issues

Step 12: Submission
├── Record 3-minute demo video
├── Create architecture diagram (PNG)
├── Write Devpost submission
├── Final testing
└── Submit before deadline
```

---

## 9. Demo Video Script (3 Minutes)

### 0:00 - 0:20 | Opening
**Visual:** Title card with CrisisFlow logo
**Script:** "Every year, disasters kill thousands of people who could have been saved with better information. This is CrisisFlow — real-time disaster intelligence that predicts where crises will escalate before emergency calls flood in."

### 0:20 - 0:45 | Architecture
**Visual:** Architecture diagram
**Script:** "CrisisFlow streams fire risk, flood risk, and social signals through Confluent Kafka, processes them with ksqlDB, and uses Google's Gemini AI to synthesize actionable alerts. Let me show you how it works."

### 0:45 - 1:30 | Live Demo - Map
**Visual:** Dashboard with map
**Script:** "Here's our live dashboard. Red markers show areas with elevated fire risk from Tomorrow.io — this one in Los Angeles has a fire index of 78. Blue markers indicate flood warnings. And these orange dots? Real-time social signals — people on the ground reporting what they're seeing."

### 1:30 - 2:00 | Live Demo - Data Flow
**Visual:** Show data updating, click on markers
**Script:** "All of this data streams through Confluent Kafka in real-time. Every 5 minutes, we pull fresh weather risk data. Social signals come in continuously. Click any marker to see details — this flood warning shows humidity at 85% and rising water reports nearby."

### 2:00 - 2:40 | Live Demo - AI Alert
**Visual:** Click "Generate Alert" button, show response
**Script:** "Here's the magic. When I click 'Generate Alert', Gemini AI synthesizes all this data into a situation report. It says: 'Critical conditions in Houston — fire index elevated, flood risk rising, 12 social reports of road flooding.' And it recommends specific actions: deploy fire crews here, issue flood warning there. Responders get actionable intelligence, not just data."

### 2:40 - 3:00 | Closing
**Visual:** Return to wide shot of dashboard
**Script:** "CrisisFlow helps emergency responders see the next hotspot before the first 911 call. Built with Confluent, Google Cloud, and Gemini AI. Because when disasters strike, minutes matter. Thank you."

---

## 10. Judging Criteria Alignment

| Criteria | How CrisisFlow Addresses It |
|----------|----------------------------|
| **Technological Implementation** | Full Confluent stack (Kafka, ksqlDB) + Vertex AI/Gemini + Tomorrow.io integration |
| **Design** | Clean, intuitive dashboard that actual responders could use |
| **Potential Impact** | Directly saves lives by enabling faster disaster response |
| **Quality of the Idea** | Novel combination of real-time streaming + predictive AI for emergencies |

---

## 11. Submission Checklist

- [ ] Public GitHub repository with open source license
- [ ] Working hosted demo URL
- [ ] 3-minute demo video on YouTube (public)
- [ ] Devpost submission form completed
- [ ] Selected "Confluent Challenge" track
- [ ] README with setup instructions
- [ ] Architecture diagram included

---

## 12. Quick Reference Commands

### Start Producers
```bash
cd producers
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python weather_producer.py &
python social_producer.py &
```

### Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Deploy Backend to Cloud Run
```bash
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/crisisflow-api
gcloud run deploy crisisflow-api --image gcr.io/PROJECT_ID/crisisflow-api --platform managed
```

---

## End of Specification

This document contains everything needed to build CrisisFlow. Start with Phase 1, Step 1 and work through sequentially. Good luck! 🚀
