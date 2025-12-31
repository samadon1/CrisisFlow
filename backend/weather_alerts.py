"""
Tomorrow.io Weather Alerts Service
Fetches real-time weather alerts from Tomorrow.io API
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import logger, TOMORROW_IO_API_KEY, LOCATIONS

class WeatherAlertsService:
    """Service for fetching weather alerts from Tomorrow.io"""

    def __init__(self):
        self.api_key = TOMORROW_IO_API_KEY
        self.base_url = "https://api.tomorrow.io/v4"
        self.alerts_cache = []
        self.cache_time = None
        self.cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes

    async def fetch_alerts_for_location(self, location: Dict) -> List[Dict]:
        """
        Fetch weather alerts for a specific location

        Args:
            location: Dict with 'name', 'lat', 'lon'

        Returns:
            List of alert dictionaries
        """
        if not self.api_key:
            logger.warning("TOMORROW_IO_API_KEY not configured, skipping alerts fetch")
            return []

        try:
            # Tomorrow.io Alerts API endpoint
            # Note: The actual endpoint might be different - check Tomorrow.io docs
            url = f"{self.base_url}/weather/realtime"
            params = {
                "location": f"{location['lat']},{location['lon']}",
                "apikey": self.api_key,
                "units": "metric"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Process alerts from response
                        # Note: This structure depends on Tomorrow.io's actual response format
                        alerts = self._process_weather_data(data, location)
                        return alerts
                    elif response.status == 401:
                        logger.error("Tomorrow.io API key is invalid")
                        return []
                    else:
                        logger.warning(f"Tomorrow.io API returned status {response.status}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching alerts for {location['name']}")
            return []
        except Exception as e:
            logger.error(f"Error fetching alerts for {location['name']}: {e}")
            return []

    def _process_weather_data(self, data: Dict, location: Dict) -> List[Dict]:
        """
        Process weather data and create alerts for severe conditions

        Args:
            data: Raw weather data from Tomorrow.io
            location: Location info

        Returns:
            List of alert dictionaries
        """
        alerts = []

        try:
            # Extract current weather data
            if 'data' not in data:
                return alerts

            weather_data = data['data']
            values = weather_data.get('values', {})

            # Create alerts based on severe weather conditions
            # These thresholds are examples - adjust based on real criteria

            # High wind alert
            wind_speed = values.get('windSpeed', 0)
            if wind_speed > 20:  # > 20 m/s (~45 mph)
                alerts.append({
                    "alert_id": f"wind-{location['name']}-{datetime.utcnow().timestamp()}",
                    "type": "wind",
                    "severity": "high" if wind_speed > 30 else "moderate",
                    "headline": f"High Wind Warning - {location['name']}",
                    "description": f"Wind speeds of {wind_speed:.1f} m/s ({wind_speed * 2.237:.1f} mph) detected. Secure loose objects and avoid outdoor activities.",
                    "location": location,
                    "onset": datetime.utcnow().isoformat(),
                    "expires": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
                    "source": "tomorrow.io",
                    "data": {"windSpeed": wind_speed}
                })

            # High temperature / heat alert
            temperature = values.get('temperature', 0)
            if temperature > 35:  # > 35°C (~95°F)
                alerts.append({
                    "alert_id": f"heat-{location['name']}-{datetime.utcnow().timestamp()}",
                    "type": "heat",
                    "severity": "moderate",
                    "headline": f"Heat Advisory - {location['name']}",
                    "description": f"Temperature of {temperature:.1f}°C ({temperature * 9/5 + 32:.1f}°F). Stay hydrated and limit outdoor exposure.",
                    "location": location,
                    "onset": datetime.utcnow().isoformat(),
                    "expires": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                    "source": "tomorrow.io",
                    "data": {"temperature": temperature}
                })

            # Heavy precipitation alert
            precip_intensity = values.get('precipitationIntensity', 0)
            if precip_intensity > 5:  # Heavy rain
                alerts.append({
                    "alert_id": f"precip-{location['name']}-{datetime.utcnow().timestamp()}",
                    "type": "precipitation",
                    "severity": "high" if precip_intensity > 10 else "moderate",
                    "headline": f"Heavy Precipitation Warning - {location['name']}",
                    "description": f"Heavy precipitation detected. Flash flooding possible. Avoid low-lying areas.",
                    "location": location,
                    "onset": datetime.utcnow().isoformat(),
                    "expires": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                    "source": "tomorrow.io",
                    "data": {"precipitationIntensity": precip_intensity}
                })

        except Exception as e:
            logger.error(f"Error processing weather data: {e}")

        return alerts

    async def fetch_all_alerts(self) -> List[Dict]:
        """
        Fetch alerts for all monitored locations

        Returns:
            List of all active alerts
        """
        # Check cache first
        if self.cache_time and datetime.utcnow() - self.cache_time < self.cache_ttl:
            logger.debug(f"Returning cached alerts ({len(self.alerts_cache)} alerts)")
            return self.alerts_cache

        logger.info("Fetching weather alerts for all locations...")
        all_alerts = []

        # Fetch alerts for each location concurrently
        tasks = [self.fetch_alerts_for_location(loc) for loc in LOCATIONS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all alerts
        for result in results:
            if isinstance(result, list):
                all_alerts.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in fetch task: {result}")

        # Update cache
        self.alerts_cache = all_alerts
        self.cache_time = datetime.utcnow()

        logger.info(f"Fetched {len(all_alerts)} weather alerts")
        return all_alerts

    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        """Get cached alerts filtered by severity"""
        return [a for a in self.alerts_cache if a.get('severity') == severity]

    def get_alerts_by_type(self, alert_type: str) -> List[Dict]:
        """Get cached alerts filtered by type"""
        return [a for a in self.alerts_cache if a.get('type') == alert_type]


# Global instance
weather_alerts_service = WeatherAlertsService()
