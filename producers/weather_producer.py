#!/usr/bin/env python3
"""
Weather Producer for CrisisFlow
Fetches weather risk data from Tomorrow.io and publishes to Kafka
"""
import json
import time
import uuid
import requests
from datetime import datetime, timezone
from confluent_kafka import Producer
from config import (
    logger,
    TOMORROW_API_KEY,
    TOMORROW_BASE_URL,
    CONFLUENT_CONFIG,
    WEATHER_TOPIC,
    LOCATIONS,
    POLL_INTERVAL_SECONDS,
    calculate_risk_level,
    validate_config
)

class WeatherProducer:
    def __init__(self):
        """Initialize the weather producer"""
        validate_config()
        self.producer = Producer(CONFLUENT_CONFIG)
        self.session = requests.Session()
        logger.info("Weather Producer initialized")

    def delivery_report(self, err, msg):
        """Callback for message delivery reports"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def fetch_weather_data(self, location):
        """Fetch weather data from Tomorrow.io API"""
        try:
            url = f"{TOMORROW_BASE_URL}/weather/realtime"
            params = {
                'location': f"{location['lat']},{location['lon']}",
                'apikey': TOMORROW_API_KEY,
                'units': 'metric'
            }

            logger.debug(f"Fetching weather for {location['name']}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return self.parse_weather_data(data, location)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather for {location['name']}: {e}")
            return None

    def parse_weather_data(self, data, location):
        """Parse Tomorrow.io response and extract relevant fields"""
        try:
            values = data.get('data', {}).get('values', {})

            # Extract weather values
            temperature = values.get('temperature', 0)
            humidity = values.get('humidity', 0)
            wind_speed = values.get('windSpeed', 0)
            wind_direction = values.get('windDirection', 0)
            precipitation = values.get('precipitationIntensity', 0)

            # Calculate risk indices (simplified formulas)
            # Fire index: Higher temp, lower humidity, higher wind = higher risk
            fire_index = self.calculate_fire_index(temperature, humidity, wind_speed)

            # Flood index: Based on precipitation intensity and humidity
            flood_index = self.calculate_flood_index(precipitation, humidity)

            # Create event
            event = {
                "event_id": str(uuid.uuid4()),
                "source": "tomorrow.io",
                "location": {
                    "name": location['name'],
                    "lat": location['lat'],
                    "lon": location['lon']
                },
                "data": {
                    "fire_index": fire_index,
                    "flood_index": flood_index,
                    "temperature": temperature,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "wind_direction": wind_direction,
                    "precipitation_intensity": precipitation
                },
                "risk_level": calculate_risk_level(fire_index, flood_index),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return event

        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return None

    def calculate_fire_index(self, temperature, humidity, wind_speed):
        """
        Calculate fire risk index (0-100)
        Simplified version of Fire Weather Index
        """
        # Base fire risk from temperature (0-40°C mapped to 0-40 points)
        temp_factor = min(max(temperature, 0), 40)

        # Humidity factor (100% humidity = 0 risk, 0% = 40 points)
        humidity_factor = max(0, 40 - (humidity * 0.4))

        # Wind factor (0-20 m/s mapped to 0-20 points)
        wind_factor = min(wind_speed, 20)

        fire_index = temp_factor + humidity_factor + wind_factor

        # Normalize to 0-100
        return min(max(int(fire_index), 0), 100)

    def calculate_flood_index(self, precipitation, humidity):
        """
        Calculate flood risk index (0-100)
        Based on precipitation intensity and soil moisture (humidity proxy)
        """
        # Precipitation factor (mm/hr)
        # Light rain: 0-2.5mm/hr, Moderate: 2.5-10, Heavy: 10-50, Violent: >50
        if precipitation < 2.5:
            precip_factor = precipitation * 10  # 0-25 points
        elif precipitation < 10:
            precip_factor = 25 + (precipitation - 2.5) * 4  # 25-55 points
        elif precipitation < 50:
            precip_factor = 55 + (precipitation - 10) * 1  # 55-95 points
        else:
            precip_factor = 95  # Cap at 95

        # Humidity as soil moisture proxy (higher = more runoff potential)
        humidity_factor = humidity * 0.05  # 0-5 points

        flood_index = precip_factor + humidity_factor

        return min(max(int(flood_index), 0), 100)

    def publish_event(self, event):
        """Publish event to Kafka"""
        try:
            key = f"{event['location']['name']}_{event['event_id'][:8]}"
            value = json.dumps(event)

            self.producer.produce(
                topic=WEATHER_TOPIC,
                key=key,
                value=value,
                callback=self.delivery_report
            )

            logger.info(f"Published weather event for {event['location']['name']} - "
                       f"Fire: {event['data']['fire_index']}, "
                       f"Flood: {event['data']['flood_index']}, "
                       f"Risk: {event['risk_level']}")

        except Exception as e:
            logger.error(f"Error publishing event: {e}")

    def run_once(self):
        """Fetch and publish weather data for all locations once"""
        logger.info(f"Fetching weather data for {len(LOCATIONS)} locations")

        for location in LOCATIONS:
            event = self.fetch_weather_data(location)
            if event:
                self.publish_event(event)

            # Small delay between API calls
            time.sleep(1)

        # Flush any pending messages
        self.producer.flush()

    def run(self):
        """Main producer loop"""
        logger.info(f"Starting Weather Producer - Polling every {POLL_INTERVAL_SECONDS} seconds")

        while True:
            try:
                self.run_once()
                logger.info(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...")
                time.sleep(POLL_INTERVAL_SECONDS)

            except KeyboardInterrupt:
                logger.info("Shutting down Weather Producer...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(30)  # Wait before retrying

        # Clean shutdown
        self.producer.flush()
        logger.info("Weather Producer shutdown complete")

if __name__ == "__main__":
    producer = WeatherProducer()
    producer.run()