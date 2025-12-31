"""
Danger Zone Prediction Engine
Predicts and visualizes spreading crisis zones on the map
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import math
import logging

logger = logging.getLogger(__name__)

class DangerZonePredictor:
    """Predicts danger zones and their spreading patterns"""

    def __init__(self):
        self.zone_cache = {}
        self.last_calculation = None
        self.cache_ttl = timedelta(seconds=30)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in kilometers using Haversine formula
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2)**2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def calculate_zone_intensity(self, events: List[Dict], center_lat: float, center_lon: float, radius_km: float) -> float:
        """
        Calculate the intensity of a danger zone based on events within radius
        """
        intensity = 0.0
        event_count = 0

        for event in events:
            location = event.get('location', {})
            lat = location.get('lat')
            lon = location.get('lon')

            if lat and lon:
                distance = self.calculate_distance(center_lat, center_lon, lat, lon)

                if distance <= radius_km:
                    # Closer events contribute more to intensity
                    distance_factor = 1.0 - (distance / radius_km)

                    # Get event severity
                    risk_level = event.get('risk_level', '')
                    urgency = event.get('data', {}).get('urgency', '')

                    severity_score = {
                        'critical': 100,
                        'high': 75,
                        'moderate': 50,
                        'medium': 50,
                        'low': 25
                    }.get(risk_level or urgency, 25)

                    intensity += severity_score * distance_factor
                    event_count += 1

        # Normalize intensity
        if event_count > 0:
            intensity = intensity / event_count

        return intensity

    def predict_spreading(self, current_zone: Dict, velocity: float, time_horizon_minutes: int) -> Dict:
        """
        Predict how a danger zone will spread over time
        """
        # Calculate spread rate based on velocity (events per minute)
        # Higher velocity = faster spread
        spread_rate_km_per_hour = min(10, velocity * 0.5)  # Max 10 km/hour

        # Calculate new radius
        hours = time_horizon_minutes / 60.0
        radius_increase = spread_rate_km_per_hour * hours

        return {
            'center_lat': current_zone['center_lat'],
            'center_lon': current_zone['center_lon'],
            'current_radius_km': current_zone['radius_km'],
            'predicted_radius_km': current_zone['radius_km'] + radius_increase,
            'spread_rate_km_per_hour': round(spread_rate_km_per_hour, 2),
            'time_horizon_minutes': time_horizon_minutes,
            'intensity': current_zone['intensity']
        }

    def identify_danger_zones(self, events: List[Dict], hotspots: List[Dict]) -> List[Dict]:
        """
        Identify danger zones from events and hotspots
        """
        danger_zones = []

        # Create zones from hotspots
        for hotspot in hotspots[:5]:  # Top 5 hotspots
            lat = hotspot.get('lat', hotspot.get('grid_lat'))
            lon = hotspot.get('lon', hotspot.get('grid_lon'))

            if lat and lon:
                # Initial radius based on event density
                event_count = hotspot.get('event_count', 1)
                radius_km = min(50, 5 + event_count * 2)  # 5km base + 2km per event, max 50km

                # Calculate intensity
                intensity = self.calculate_zone_intensity(events, lat, lon, radius_km)

                # Determine threat level
                if intensity > 75:
                    threat_level = 'critical'
                elif intensity > 50:
                    threat_level = 'severe'
                elif intensity > 30:
                    threat_level = 'high'
                elif intensity > 15:
                    threat_level = 'moderate'
                else:
                    threat_level = 'low'

                danger_zones.append({
                    'zone_id': f"zone_{lat:.2f}_{lon:.2f}",
                    'center_lat': lat,
                    'center_lon': lon,
                    'radius_km': radius_km,
                    'intensity': round(intensity, 1),
                    'threat_level': threat_level,
                    'event_count': event_count,
                    'primary_type': hotspot.get('primary_type', 'multi-hazard')
                })

        # Sort by intensity
        danger_zones.sort(key=lambda x: x['intensity'], reverse=True)

        return danger_zones

    def calculate_evacuation_zones(self, danger_zones: List[Dict]) -> List[Dict]:
        """
        Calculate evacuation zones based on danger zones
        """
        evacuation_zones = []

        for zone in danger_zones:
            if zone['threat_level'] in ['critical', 'severe']:
                # Evacuation radius is larger than danger zone
                evacuation_radius = zone['radius_km'] * 1.5

                # Estimate population (simplified - ~1000 people per sq km in urban areas)
                area_sq_km = math.pi * evacuation_radius ** 2
                estimated_population = int(area_sq_km * 100)  # Assuming moderate density

                evacuation_zones.append({
                    'zone_id': zone['zone_id'],
                    'center_lat': zone['center_lat'],
                    'center_lon': zone['center_lon'],
                    'evacuation_radius_km': round(evacuation_radius, 1),
                    'danger_radius_km': zone['radius_km'],
                    'estimated_population': estimated_population,
                    'threat_level': zone['threat_level'],
                    'primary_threat': zone['primary_type'],
                    'priority': 'immediate' if zone['threat_level'] == 'critical' else 'urgent'
                })

        return evacuation_zones

    def get_danger_zones(self, events: List[Dict], hotspots: List[Dict], predictions: Dict) -> Dict:
        """
        Get comprehensive danger zone analysis with caching
        """
        now = datetime.now(timezone.utc)

        # Check cache
        if self.last_calculation and (now - self.last_calculation) < self.cache_ttl:
            if self.zone_cache:
                return self.zone_cache

        # Identify current danger zones
        current_zones = self.identify_danger_zones(events, hotspots)

        # Get velocity from predictions
        velocity = predictions.get('metrics', {}).get('velocity', 0)

        # Predict spreading for each zone at different time horizons
        spreading_predictions = []
        for zone in current_zones[:3]:  # Top 3 zones
            for time_horizon in [30, 60, 120]:
                spread = self.predict_spreading(zone, velocity, time_horizon)
                spread['zone_id'] = zone['zone_id']
                spread['threat_level'] = zone['threat_level']
                spreading_predictions.append(spread)

        # Calculate evacuation zones
        evacuation_zones = self.calculate_evacuation_zones(current_zones)

        # Prepare response
        result = {
            'current_zones': current_zones,
            'spreading_predictions': spreading_predictions,
            'evacuation_zones': evacuation_zones,
            'total_zones': len(current_zones),
            'critical_zones': len([z for z in current_zones if z['threat_level'] == 'critical']),
            'generated_at': now.isoformat()
        }

        # Cache result
        self.zone_cache = result
        self.last_calculation = now

        return result

# Global instance
danger_zone_predictor = DangerZonePredictor()