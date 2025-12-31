"""
Crisis Prediction Engine
Analyzes real-time event streams to predict crisis escalation
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from collections import deque
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CrisisPrediction:
    """Prediction for crisis escalation"""
    time_horizon: int  # minutes (30, 60, 120)
    probability: float  # 0-100
    confidence: float  # 0-100
    severity: str  # critical, high, moderate, low
    affected_population: int
    key_factors: List[str]
    recommended_actions: List[str]
    location: Dict[str, float]  # lat, lon
    crisis_type: str  # fire, flood, multi-hazard

class PredictionEngine:
    """Engine for predicting crisis escalation using streaming data"""

    def __init__(self):
        self.event_window = deque(maxlen=1000)  # Last 1000 events
        self.time_window = timedelta(minutes=30)  # Analysis window
        self.prediction_cache = {}
        self.last_calculation = None

    def add_event(self, event: Dict) -> None:
        """Add new event to the analysis window"""
        self.event_window.append({
            **event,
            'processed_at': datetime.now(timezone.utc)
        })

    def calculate_velocity(self, events: List[Dict]) -> Tuple[float, str]:
        """
        Calculate the velocity (rate of change) of crisis events
        Returns: (events_per_minute, trend_direction)
        """
        if len(events) < 2:
            return 0.0, 'stable'

        # Group events by time buckets (5-minute windows)
        time_buckets = {}
        now = datetime.now(timezone.utc)

        for event in events:
            # Parse timestamp
            if isinstance(event.get('timestamp'), str):
                timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = event.get('timestamp', now)

            bucket = timestamp.replace(minute=(timestamp.minute // 5) * 5, second=0, microsecond=0)
            time_buckets[bucket] = time_buckets.get(bucket, 0) + 1

        if len(time_buckets) < 2:
            return 0.0, 'stable'

        # Calculate trend
        sorted_buckets = sorted(time_buckets.items())
        recent_count = sum(count for time, count in sorted_buckets[-3:])
        older_count = sum(count for time, count in sorted_buckets[:-3]) if len(sorted_buckets) > 3 else 0

        # Calculate events per minute (rate of change)
        time_span_minutes = 15  # 3 buckets * 5 minutes each

        # Calculate actual rate of events per minute
        if len(sorted_buckets) > 0:
            # Events per minute in recent period
            recent_rate = recent_count / time_span_minutes if time_span_minutes > 0 else 0
            # Events per minute in older period (if we have older data)
            if len(sorted_buckets) > 3:
                older_time_span = (len(sorted_buckets) - 3) * 5
                older_rate = older_count / older_time_span if older_time_span > 0 else 0
                # Velocity is the change in rate (can be negative)
                velocity = (recent_rate - older_rate) * 60  # Convert to events per hour
            else:
                # No older data, just use recent rate
                velocity = recent_rate * 60  # Convert to events per hour
        else:
            velocity = 0.0

        # Determine trend based on velocity (events per hour)
        if velocity > 30:  # More than 30 events/hour increase
            trend = 'escalating_rapidly'
        elif velocity > 10:  # More than 10 events/hour increase
            trend = 'escalating'
        elif velocity < -10:  # More than 10 events/hour decrease
            trend = 'decreasing'
        else:
            trend = 'stable'

        return velocity, trend

    def calculate_risk_acceleration(self, events: List[Dict]) -> float:
        """
        Calculate acceleration of risk (second derivative)
        Positive = getting worse faster, Negative = improving
        """
        if len(events) < 10:
            return 0.0

        # Calculate velocities for different time periods
        recent_velocity, _ = self.calculate_velocity(events[-50:] if len(events) > 50 else events)
        older_velocity, _ = self.calculate_velocity(events[-100:-50] if len(events) > 100 else events[:len(events)//2])

        acceleration = recent_velocity - older_velocity
        return acceleration

    def identify_hotspots(self, events: List[Dict]) -> List[Dict]:
        """Identify geographic hotspots of crisis activity"""
        from collections import defaultdict

        # Grid size (approximately 5km)
        grid_size = 0.05

        hotspot_grid = defaultdict(lambda: {'count': 0, 'severity_sum': 0, 'events': []})

        for event in events:
            location = event.get('location', {})
            lat = location.get('lat')
            lon = location.get('lon')

            if lat and lon:
                # Snap to grid
                grid_lat = round(lat / grid_size) * grid_size
                grid_lon = round(lon / grid_size) * grid_size
                grid_key = (grid_lat, grid_lon)

                # Calculate severity score
                severity_score = self._get_severity_score(event)

                hotspot_grid[grid_key]['count'] += 1
                hotspot_grid[grid_key]['severity_sum'] += severity_score
                hotspot_grid[grid_key]['events'].append(event)

        # Find top hotspots
        hotspots = []
        for (lat, lon), data in hotspot_grid.items():
            if data['count'] >= 3:  # Minimum events for hotspot
                hotspots.append({
                    'lat': lat,
                    'lon': lon,
                    'intensity': data['severity_sum'] / data['count'],
                    'event_count': data['count'],
                    'primary_type': self._get_primary_crisis_type(data['events'])
                })

        return sorted(hotspots, key=lambda x: x['intensity'], reverse=True)[:10]

    def _get_severity_score(self, event: Dict) -> float:
        """Calculate numeric severity score for an event"""
        # Check for risk level or urgency
        risk_level = event.get('risk_level', '')
        urgency = event.get('data', {}).get('urgency', '')

        severity_map = {
            'critical': 100,
            'high': 75,
            'moderate': 50,
            'medium': 50,
            'low': 25
        }

        return severity_map.get(risk_level, severity_map.get(urgency, 25))

    def _get_primary_crisis_type(self, events: List[Dict]) -> str:
        """Determine primary crisis type from events"""
        from collections import Counter

        types = []
        for event in events:
            # Check social event category
            category = event.get('data', {}).get('category')
            if category:
                types.append(category)
            # Check weather event type
            elif event.get('data', {}).get('fire_index', 0) > event.get('data', {}).get('flood_index', 0):
                types.append('fire')
            else:
                types.append('flood')

        if types:
            return Counter(types).most_common(1)[0][0]
        return 'unknown'

    def predict_escalation(self, events: List[Dict], stats: Dict) -> List[CrisisPrediction]:
        """
        Generate predictions for crisis escalation at different time horizons
        """
        predictions = []

        # Calculate metrics
        velocity, trend = self.calculate_velocity(events)
        acceleration = self.calculate_risk_acceleration(events)
        hotspots = self.identify_hotspots(events)

        # Get current crisis levels
        current_critical = stats.get('social', {}).get('by_urgency', {}).get('critical', 0)
        current_high = stats.get('social', {}).get('by_urgency', {}).get('high', 0)

        # Generate predictions for different time horizons
        for time_horizon in [30, 60, 120]:
            # Base probability on current trend and acceleration
            base_probability = 50.0

            if trend == 'escalating_rapidly':
                base_probability = 85.0
            elif trend == 'escalating':
                base_probability = 70.0
            elif trend == 'stable':
                base_probability = 40.0
            else:
                base_probability = 20.0

            # Adjust for acceleration
            if acceleration > 10:
                base_probability = min(100, base_probability + 15)
            elif acceleration < -10:
                base_probability = max(0, base_probability - 15)

            # Adjust probability based on time horizon
            time_factor = 1.0 - (time_horizon / 240.0)  # Decreases with time
            probability = base_probability * (0.5 + 0.5 * time_factor)

            # Calculate confidence based on data quality
            confidence = min(100, len(events) / 2.0)  # More events = more confidence
            if trend == 'stable':
                confidence *= 0.8  # Less confident in stable predictions

            # Determine severity
            if probability > 75:
                severity = 'critical'
            elif probability > 50:
                severity = 'high'
            elif probability > 30:
                severity = 'moderate'
            else:
                severity = 'low'

            # Estimate affected population (simplified)
            affected_population = 0
            if hotspots:
                # Each hotspot affects ~5000 people in urban areas
                affected_population = len(hotspots) * 5000 * (probability / 100)

            # Key factors
            key_factors = []
            if velocity > 20:
                key_factors.append(f"Event velocity: {velocity:.1f} events/min")
            if acceleration > 5:
                key_factors.append(f"Accelerating at {acceleration:.1f} events/min²")
            if current_critical > 20:
                key_factors.append(f"{current_critical} critical events active")
            if len(hotspots) > 3:
                key_factors.append(f"{len(hotspots)} geographic hotspots detected")

            # Recommended actions
            actions = []
            if severity in ['critical', 'high']:
                actions.append("Initiate emergency response protocols")
                actions.append("Pre-deploy resources to hotspot areas")
                if time_horizon <= 30:
                    actions.append("Issue immediate evacuation orders")
            elif severity == 'moderate':
                actions.append("Increase monitoring frequency")
                actions.append("Alert response teams")
            else:
                actions.append("Continue standard monitoring")

            # Get primary location from hotspots
            location = {'lat': 0, 'lon': 0}
            if hotspots:
                location = {'lat': hotspots[0]['lat'], 'lon': hotspots[0]['lon']}

            predictions.append(CrisisPrediction(
                time_horizon=time_horizon,
                probability=round(probability, 1),
                confidence=round(confidence, 1),
                severity=severity,
                affected_population=int(affected_population),
                key_factors=key_factors,
                recommended_actions=actions,
                location=location,
                crisis_type=hotspots[0]['primary_type'] if hotspots else 'multi-hazard'
            ))

        return predictions

    async def get_predictions(self, events: List[Dict], stats: Dict) -> Dict:
        """
        Get current predictions with caching
        """
        current_time = datetime.now(timezone.utc)

        # Cache predictions for 1 minute
        if self.last_calculation and \
           (current_time - self.last_calculation).seconds < 60 and \
           self.prediction_cache:
            return self.prediction_cache

        # Generate new predictions
        predictions = self.predict_escalation(events, stats)

        # Calculate additional metrics
        velocity, trend = self.calculate_velocity(events)
        acceleration = self.calculate_risk_acceleration(events)
        hotspots = self.identify_hotspots(events)

        result = {
            'predictions': [
                {
                    'time_horizon': p.time_horizon,
                    'probability': p.probability,
                    'confidence': p.confidence,
                    'severity': p.severity,
                    'affected_population': p.affected_population,
                    'key_factors': p.key_factors,
                    'recommended_actions': p.recommended_actions,
                    'location': p.location,
                    'crisis_type': p.crisis_type
                }
                for p in predictions
            ],
            'metrics': {
                'velocity': round(velocity, 2),
                'trend': trend,
                'acceleration': round(acceleration, 2),
                'hotspot_count': len(hotspots),
                'data_points': len(events)
            },
            'hotspots': hotspots[:5],  # Top 5 hotspots
            'generated_at': current_time.isoformat()
        }

        self.prediction_cache = result
        self.last_calculation = current_time

        return result

# Global instance
prediction_engine = PredictionEngine()