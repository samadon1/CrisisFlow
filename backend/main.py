#!/usr/bin/env python3
"""
CrisisFlow API - Real-time Disaster Intelligence Platform
Built with FastAPI, Confluent Kafka, and Google Gemini
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import (
    logger,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    CORS_ORIGINS,
    LOCATIONS,
    validate_config
)
from models import (
    HealthResponse,
    EventsResponse,
    HotspotsResponse,
    AlertGenerationRequest,
    AlertResponse,
    LocationsResponse,
    StatsResponse,
    ErrorResponse,
    ChatRequest,
    ChatResponse,
    WeatherAlertsResponse,
    PredictionsResponse,
    StreamMetricsResponse,
    DangerZonesResponse
)
from kafka_consumer import consumer
from gemini_client import gemini_client
from agents.multi_agent_coordinator import MultiAgentCoordinator
from weather_alerts import weather_alerts_service
from prediction_engine import prediction_engine
from stream_analytics import stream_analytics
from danger_zones import danger_zone_predictor

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting CrisisFlow API...")
    try:
        validate_config()
        await consumer.start()
        # Initialize Multi-Agent System
        app.state.agent_coordinator = MultiAgentCoordinator(gemini_client)
        logger.info("CrisisFlow API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CrisisFlow API...")
    await consumer.stop()
    logger.info("CrisisFlow API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# =====================================================
# API Endpoints
# =====================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns the current status of the API and its connections
    """
    try:
        kafka_connected = consumer.consumer is not None and consumer.running
        return HealthResponse(
            status="healthy" if kafka_connected else "degraded",
            kafka_connected=kafka_connected,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/events", response_model=EventsResponse, tags=["Events"])
async def get_events(limit: int = Query(200, ge=1, le=500, description="Maximum events per category")):
    """
    Get latest events from all streams
    Returns weather risk events and social signals
    """
    try:
        events = consumer.get_latest_events(limit=limit)
        return EventsResponse(**events)
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hotspots", response_model=HotspotsResponse, tags=["Hotspots"])
async def get_hotspots():
    """
    Get aggregated risk hotspots
    Returns geographic grid cells with highest risk concentrations
    """
    try:
        hotspots = await consumer.get_hotspots()
        return HotspotsResponse(
            hotspots=hotspots,
            count=len(hotspots)
        )
    except Exception as e:
        logger.error(f"Error getting hotspots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alert/generate", response_model=AlertResponse, tags=["AI"])
async def generate_alert(request: AlertGenerationRequest = AlertGenerationRequest()):
    """
    Generate AI situation report using Gemini
    Analyzes current conditions and provides actionable recommendations
    """
    try:
        # Get latest data
        events = consumer.get_latest_events(limit=100)
        hotspots = await consumer.get_hotspots()

        # Generate AI alert
        alert = await gemini_client.generate_alert(
            weather_events=events["weather"],
            social_events=events["social"],
            hotspots=hotspots,
            focus_area=request.focus_area.dict() if request.focus_area else None
        )

        return AlertResponse(**alert)

    except Exception as e:
        logger.error(f"Error generating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations", response_model=LocationsResponse, tags=["Locations"])
async def get_locations():
    """
    Get list of monitored locations
    Returns all cities/regions being monitored for disasters
    """
    try:
        return LocationsResponse(locations=LOCATIONS)
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/cycle", tags=["Admin"])
async def cycle_cache(keep_percentage: float = Query(0.2, ge=0, le=0.5, description="Percentage of events to keep")):
    """
    Cycle the event cache to prevent stagnation

    Clears old events while keeping a percentage of recent ones for continuity.
    Useful for demos and keeping the data fresh.
    """
    try:
        result = consumer.clear_cache(keep_percentage)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error cycling cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics():
    """
    Get current statistics
    Returns counts and breakdowns of events by category
    """
    try:
        stats = consumer.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/chat", response_model=ChatResponse, tags=["AI"])
async def ai_chat(request: ChatRequest):
    """
    Interactive AI Q&A about current crisis situation
    Ask questions and get context-aware answers from Gemini
    """
    try:
        logger.info(f"AI Chat query: {request.question}")

        # Get current context if not provided
        if not request.context:
            events = consumer.get_latest_events(limit=50)
            hotspots = await consumer.get_hotspots()
            stats = consumer.get_stats()
            request.context = {
                "events": events,
                "hotspots": hotspots,
                "stats": stats
            }

        # Generate AI response
        answer = await gemini_client.answer_question(
            question=request.question,
            context=request.context
        )

        return ChatResponse(
            answer=answer,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts", response_model=WeatherAlertsResponse, tags=["Alerts"])
async def get_weather_alerts():
    """
    Get active weather alerts from Tomorrow.io
    Returns severe weather warnings for all monitored locations
    """
    try:
        alerts = await weather_alerts_service.fetch_all_alerts()
        return WeatherAlertsResponse(
            alerts=alerts,
            count=len(alerts),
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting weather alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# Multi-Agent System Endpoints
# =====================================================

@app.post("/api/agents/analyze")
async def run_agent_analysis():
    """
    Run Multi-Agent System analysis on current events

    This orchestrates all 5 agents:
    - Scout: Monitors and detects patterns
    - Analyst: Deep crisis analysis
    - Predictor: Forecasts evolution
    - Coordinator: Makes decisions
    - Communicator: Generates alerts
    """
    try:
        # Get current events
        events = consumer.get_latest_events()

        # Run multi-agent analysis
        result = await app.state.agent_coordinator.analyze_situation(events)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error in agent analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_agent_status():
    """Get current status of all agents"""
    try:
        status = app.state.agent_coordinator.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/collaboration")
async def get_collaboration_history(limit: int = Query(50, ge=1, le=200)):
    """Get agent collaboration chat history"""
    try:
        history = app.state.agent_coordinator.get_collaboration_history(limit)
        return JSONResponse(content={"messages": history})
    except Exception as e:
        logger.error(f"Error getting collaboration history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# Prediction Engine Endpoints
# =====================================================

@app.get("/api/predictions", response_model=PredictionsResponse, tags=["Predictions"])
async def get_predictions():
    """
    Get crisis escalation predictions

    Uses real-time stream analysis to predict:
    - Crisis escalation probability at 30, 60, 120 minute horizons
    - Geographic hotspots and spreading patterns
    - Affected population estimates
    - Recommended response actions
    """
    try:
        # Get latest events and stats for prediction
        events = consumer.get_latest_events(limit=200)
        stats = consumer.get_stats()

        # Combine weather and social events for analysis
        all_events = []
        for event in events.get("weather", []):
            all_events.append(event)
        for event in events.get("social", []):
            all_events.append(event)

        # Get predictions
        predictions = await prediction_engine.get_predictions(all_events, stats)

        return PredictionsResponse(**predictions)

    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics", response_model=StreamMetricsResponse, tags=["Analytics"])
async def get_stream_metrics():
    """
    Get real-time stream processing metrics

    Shows streaming performance compared to traditional batch processing:
    - Events per second processing rate
    - Processing latency (streaming vs batch)
    - Prediction accuracy and horizon
    - System uptime and total events processed
    """
    try:
        metrics = stream_analytics.get_metrics()
        return StreamMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error getting stream metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/danger-zones", response_model=DangerZonesResponse, tags=["Predictions"])
async def get_danger_zones():
    """
    Get danger zone predictions and evacuation recommendations

    Analyzes current crisis hotspots to predict:
    - Current danger zones with threat levels
    - Spreading predictions at 30, 60, 120 minute horizons
    - Evacuation zone recommendations
    - Population impact estimates
    """
    try:
        # Get current data
        events = consumer.get_latest_events(limit=200)
        hotspots = await consumer.get_hotspots()
        stats = consumer.get_stats()

        # Combine events for analysis
        all_events = []
        for event in events.get("weather", []):
            all_events.append(event)
        for event in events.get("social", []):
            all_events.append(event)

        # Get predictions for velocity data
        predictions = await prediction_engine.get_predictions(all_events, stats)

        # Get danger zones
        danger_zones = danger_zone_predictor.get_danger_zones(all_events, hotspots, predictions)

        return DangerZonesResponse(**danger_zones)

    except Exception as e:
        logger.error(f"Error getting danger zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# WebSocket Endpoint (Optional - for real-time updates)
# =====================================================

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming
    Sends new events to connected clients as they arrive
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            # Send latest events every 5 seconds
            events = consumer.get_latest_events(limit=10)
            await websocket.send_json(events)
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# =====================================================
# Main entry point
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )