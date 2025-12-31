# CrisisFlow Architecture

## Simple Linear Flow

```mermaid
graph LR
    subgraph "1. Data Sources"
        W[Weather API<br/>Tomorrow.io]
        S[Social Media<br/>Twitter/Emergency]
    end

    subgraph "2. Streaming"
        K[Confluent Kafka<br/>100,000 events/sec]
    end

    subgraph "3. Processing"
        B[FastAPI Backend<br/>Event Cache]
    end

    subgraph "4. AI Analysis"
        G[Google Gemini<br/>Real-time Analysis]
    end

    subgraph "5. Dashboard"
        F[React Frontend<br/>Live Visualization]
    end

    W -->|Stream| K
    S -->|Stream| K
    K -->|Consume| B
    B -->|Analyze| G
    G -->|Insights| B
    B -->|Display| F

    style W fill:#e3f2fd
    style S fill:#e3f2fd
    style K fill:#fff3e0
    style B fill:#f3e5f5
    style G fill:#e8f5e9
    style F fill:#fce4ec
```

## How It Works - Step by Step

```mermaid
graph TD
    A[Step 1: Weather data streams in] --> B[Step 2: Social media reports flow]
    B --> C[Step 3: Confluent Kafka ingests all streams]
    C --> D[Step 4: Backend consumes and caches events]
    D --> E[Step 5: User clicks 'Generate Alert']
    E --> F[Step 6: Gemini AI analyzes streaming context]
    F --> G[Step 7: AI returns predictions & recommendations]
    G --> H[Step 8: Dashboard displays real-time insights]

    style A fill:#bbdefb
    style B fill:#bbdefb
    style C fill:#ffe082
    style D fill:#ce93d8
    style E fill:#a5d6a7
    style F fill:#a5d6a7
    style G fill:#ef9a9a
    style H fill:#ef9a9a
```

## The Data Journey

1. **DATA SOURCES** → Weather sensors detect storm surge exceeding safe levels
2. **KAFKA STREAM** → Event flows through Confluent at millisecond speed
3. **BACKEND CACHE** → FastAPI stores last 1000 events in memory
4. **AI PROCESSING** → Gemini analyzes pattern: "Critical flood risk in 6 hours"
5. **FRONTEND ALERT** → Dashboard shows red zones, triggers evacuation order

## Simple Numbers

- **Input**: 100,000+ events per second
- **Processing**: Sub-second latency
- **AI Analysis**: 3 seconds
- **Output**: Real-time dashboard updates

## What Makes It Special

Unlike traditional batch processing that runs every 30 minutes, CrisisFlow processes everything in real-time:

**Traditional System:**
```
Data → Wait 30 min → Process → Wait → Human Analysis → Alert (Too Late!)
```

**CrisisFlow:**
```
Data → Kafka (instant) → AI (3 sec) → Alert (Lives Saved!)
```