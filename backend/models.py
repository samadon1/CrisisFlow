"""
Pydantic models for CrisisFlow API
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Request Models

class FocusArea(BaseModel):
    """Focus area for alert generation"""
    lat: float = Field(..., description="Latitude of focus area")
    lon: float = Field(..., description="Longitude of focus area")
    radius_km: float = Field(default=50, description="Radius in kilometers")

class AlertGenerationRequest(BaseModel):
    """Request to generate an AI alert"""
    include_recommendations: bool = Field(default=True, description="Include AI recommendations")
    focus_area: Optional[FocusArea] = Field(None, description="Optional geographic focus area")

# Response Models

class Location(BaseModel):
    """Geographic location"""
    name: Optional[str] = None
    lat: float
    lon: float

class WeatherData(BaseModel):
    """Weather risk data"""
    fire_index: float
    flood_index: float
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float
    precipitation_intensity: float

class WeatherEvent(BaseModel):
    """Weather risk event"""
    event_id: str
    source: str
    location: Location
    data: WeatherData
    risk_level: str
    timestamp: str

class SocialData(BaseModel):
    """Social signal data"""
    text: str
    category: str
    urgency: str
    verified: bool

class SocialEvent(BaseModel):
    """Social signal event"""
    event_id: str
    source: str
    location: Location
    data: SocialData
    timestamp: str

class EventsResponse(BaseModel):
    """Response containing latest events"""
    weather: List[WeatherEvent]
    social: List[SocialEvent]
    last_updated: str

class Hotspot(BaseModel):
    """Aggregated risk hotspot"""
    grid_lat: float
    grid_lon: float
    event_count: int
    avg_fire_index: float
    avg_flood_index: float
    social_count: int
    risk_level: str
    window_start: str
    window_end: str

class HotspotsResponse(BaseModel):
    """Response containing hotspots"""
    hotspots: List[Hotspot]
    count: int

class RecommendedAction(BaseModel):
    """AI-recommended action"""
    priority: str
    action: str
    reason: str

class RiskSummary(BaseModel):
    """Risk level summary"""
    fire: str
    flood: str
    overall: str

class Prediction(BaseModel):
    """AI prediction"""
    timeframe: str
    event: str
    probability: int
    severity: str

class ResourceDispatch(BaseModel):
    """Resource dispatch recommendation"""
    resource: str
    quantity: int
    priority: str
    deployment_location: str
    reason: str

class EvacuationZone(BaseModel):
    """Evacuation zone"""
    location: str
    radius_miles: float
    priority: str
    estimated_population: int
    primary_threat: str
    evacuation_routes: List[str]

class AlertResponse(BaseModel):
    """AI-generated alert response"""
    alert_id: str
    generated_at: str
    situation_report: str
    recommended_actions: List[RecommendedAction]
    risk_summary: RiskSummary
    predictions: Optional[List[Prediction]] = []
    resource_dispatch: Optional[List[ResourceDispatch]] = []
    evacuation_zones: Optional[List[EvacuationZone]] = []
    focus_area: Optional[FocusArea] = None
    fallback: Optional[bool] = Field(False, description="True if using fallback (non-AI) generation")

class LocationInfo(BaseModel):
    """Location information"""
    name: str
    lat: float
    lon: float

class LocationsResponse(BaseModel):
    """Response containing monitored locations"""
    locations: List[LocationInfo]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    kafka_connected: bool
    timestamp: str

class StatsResponse(BaseModel):
    """Statistics response"""
    weather: Dict
    social: Dict
    cache_time: str

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    timestamp: str

class ChatRequest(BaseModel):
    """AI chat request"""
    question: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    """AI chat response"""
    answer: str
    timestamp: str

class WeatherAlert(BaseModel):
    """Weather alert from Tomorrow.io"""
    alert_id: str
    type: str  # wind, heat, precipitation, etc.
    severity: str  # critical, high, moderate, low
    headline: str
    description: str
    location: LocationInfo
    onset: str  # ISO timestamp
    expires: str  # ISO timestamp
    source: str
    data: Optional[Dict] = None

class WeatherAlertsResponse(BaseModel):
    """Response containing weather alerts"""
    alerts: List[WeatherAlert]
    count: int
    last_updated: str

# Prediction Models

class PredictionMetrics(BaseModel):
    """Real-time metrics for prediction engine"""
    velocity: float = Field(..., description="Events per minute rate of change")
    trend: str = Field(..., description="Trend direction: escalating_rapidly, escalating, stable, decreasing")
    acceleration: float = Field(..., description="Rate of change acceleration")
    hotspot_count: int = Field(..., description="Number of geographic hotspots")
    data_points: int = Field(..., description="Number of events analyzed")

class CrisisHotspot(BaseModel):
    """Geographic hotspot of crisis activity"""
    lat: float
    lon: float
    intensity: float = Field(..., description="Crisis intensity score 0-100")
    event_count: int
    primary_type: str = Field(..., description="Primary crisis type: fire, flood, etc")

class CrisisPrediction(BaseModel):
    """Prediction for crisis escalation"""
    time_horizon: int = Field(..., description="Prediction time in minutes (30, 60, 120)")
    probability: float = Field(..., description="Probability of escalation 0-100")
    confidence: float = Field(..., description="Confidence in prediction 0-100")
    severity: str = Field(..., description="Predicted severity: critical, high, moderate, low")
    affected_population: int = Field(..., description="Estimated affected population")
    key_factors: List[str] = Field(..., description="Key factors driving prediction")
    recommended_actions: List[str] = Field(..., description="Recommended response actions")
    location: Dict[str, float] = Field(..., description="Primary location of predicted crisis")
    crisis_type: str = Field(..., description="Type of crisis: fire, flood, multi-hazard")

class PredictionsResponse(BaseModel):
    """Response containing crisis predictions"""
    predictions: List[CrisisPrediction]
    metrics: PredictionMetrics
    hotspots: List[CrisisHotspot]
    generated_at: str

# Stream Analytics Models

class StreamMetrics(BaseModel):
    """Real-time stream processing metrics"""
    events_per_second: float = Field(..., description="Current events processing rate")
    peak_events_per_second: float = Field(..., description="Peak rate in last hour")
    processing_latency_ms: float = Field(..., description="Average processing latency")
    total_events_processed: int = Field(..., description="Total events since startup")
    uptime_seconds: int = Field(..., description="System uptime")
    predictions_ahead_minutes: int = Field(..., description="How far ahead predictions are")
    accuracy_score: float = Field(..., description="Prediction accuracy percentage")

class StreamMetricsResponse(BaseModel):
    """Response containing stream metrics"""
    current: StreamMetrics
    performance_vs_batch: Dict[str, str] = Field(..., description="Comparison with batch processing")
    timestamp: str

# Danger Zone Models

class DangerZone(BaseModel):
    """A geographic danger zone"""
    zone_id: str
    center_lat: float
    center_lon: float
    radius_km: float
    intensity: float = Field(..., description="Intensity score 0-100")
    threat_level: str = Field(..., description="Threat level: critical, severe, high, moderate, low")
    event_count: int
    primary_type: str

class SpreadingPrediction(BaseModel):
    """Prediction of danger zone spreading"""
    zone_id: str
    center_lat: float
    center_lon: float
    current_radius_km: float
    predicted_radius_km: float
    spread_rate_km_per_hour: float
    time_horizon_minutes: int
    intensity: float
    threat_level: str

class EvacuationRecommendation(BaseModel):
    """Evacuation recommendation for a danger zone"""
    zone_id: str
    center_lat: float
    center_lon: float
    evacuation_radius_km: float
    danger_radius_km: float
    estimated_population: int
    threat_level: str
    primary_threat: str
    priority: str = Field(..., description="Priority: immediate, urgent, moderate")

class DangerZonesResponse(BaseModel):
    """Response containing danger zone analysis"""
    current_zones: List[DangerZone]
    spreading_predictions: List[SpreadingPrediction]
    evacuation_zones: List[EvacuationRecommendation]
    total_zones: int
    critical_zones: int
    generated_at: str