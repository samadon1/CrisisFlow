#!/usr/bin/env python3
"""
Time Travel Mode for CrisisFlow Demo
Simulates 6 hours of disaster escalation in 2 minutes
Perfect for demo videos and presentations
"""
import json
import time
import uuid
import random
from datetime import datetime, timezone, timedelta
from confluent_kafka import Producer
from config import (
    logger,
    CONFLUENT_CONFIG,
    WEATHER_TOPIC,
    SOCIAL_TOPIC,
    LOCATIONS,
    calculate_risk_level,
    validate_config
)

class TimeTravelSimulator:
    def __init__(self):
        """Initialize time travel simulator"""
        validate_config()
        self.producer = Producer(CONFLUENT_CONFIG)
        self.base_time = datetime.now(timezone.utc)
        self.load_crisis_tweets()
        logger.info("Time Travel Simulator initialized")

    def load_crisis_tweets(self):
        """Load crisis tweets from JSON file"""
        try:
            with open('data/crisis_tweets.json', 'r') as f:
                self.tweets = json.load(f)
        except Exception as e:
            logger.error(f"Error loading crisis tweets: {e}")
            self.tweets = []

    def delivery_report(self, err, msg):
        """Callback for message delivery"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')

    def simulate_time_period(self, hour_offset, intensity):
        """
        Simulate disaster at a specific time with given intensity
        hour_offset: 0-6 (hours into the disaster)
        intensity: 0.0-1.0 (how severe the disaster is)
        """
        simulated_time = self.base_time + timedelta(hours=hour_offset)

        # Weather events - intensity increases over time
        for location in LOCATIONS:
            # Base indices increase with intensity
            base_fire = 20 + (intensity * 60)  # 20-80
            base_flood = 15 + (intensity * 55)  # 15-70

            # Add randomness
            fire_index = base_fire + random.uniform(-10, 10)
            flood_index = base_flood + random.uniform(-10, 10)

            # Clamp to 0-100
            fire_index = max(0, min(100, fire_index))
            flood_index = max(0, min(100, flood_index))

            # Temperature and humidity correlate with fire risk
            temperature = 25 + (fire_index / 100 * 15)  # 25-40°C
            humidity = 80 - (fire_index / 100 * 40)     # 80-40%
            wind_speed = 5 + (intensity * 15)            # 5-20 m/s

            event = {
                "event_id": str(uuid.uuid4()),
                "source": "tomorrow.io",
                "location": {
                    "name": location['name'],
                    "lat": location['lat'],
                    "lon": location['lon']
                },
                "data": {
                    "fire_index": round(fire_index, 1),
                    "flood_index": round(flood_index, 1),
                    "temperature": round(temperature, 1),
                    "humidity": round(humidity, 1),
                    "wind_speed": round(wind_speed, 1),
                    "wind_direction": random.randint(0, 360),
                    "precipitation_intensity": flood_index / 100 * 20
                },
                "risk_level": calculate_risk_level(fire_index, flood_index),
                "timestamp": simulated_time.isoformat()
            }

            self.producer.produce(
                topic=WEATHER_TOPIC,
                key=f"{location['name']}_{uuid.uuid4().hex[:8]}",
                value=json.dumps(event),
                callback=self.delivery_report
            )

        # Social signals - more frequent as intensity increases
        num_social_events = int(5 + (intensity * 20))  # 5-25 events

        for _ in range(num_social_events):
            tweet = random.choice(self.tweets)

            # Urgency correlates with intensity
            if intensity > 0.7:
                urgency_choices = ['critical', 'critical', 'high']
            elif intensity > 0.4:
                urgency_choices = ['high', 'high', 'medium']
            else:
                urgency_choices = ['medium', 'low', 'low']

            event = {
                "event_id": str(uuid.uuid4()),
                "source": "social",
                "location": {
                    "lat": round(tweet['base_lat'] + random.uniform(-0.02, 0.02), 6),
                    "lon": round(tweet['base_lon'] + random.uniform(-0.02, 0.02), 6)
                },
                "data": {
                    "text": tweet['text'],
                    "category": tweet['category'],
                    "urgency": random.choice(urgency_choices),
                    "verified": random.choice([True, False, False])
                },
                "timestamp": simulated_time.isoformat()
            }

            self.producer.produce(
                topic=SOCIAL_TOPIC,
                key=f"social_{uuid.uuid4().hex[:8]}",
                value=json.dumps(event),
                callback=self.delivery_report
            )

        self.producer.flush()

    def run_demo_sequence(self):
        """
        Run a complete demo sequence showing disaster escalation
        Timeline: 6 hours compressed into 2 minutes (20 seconds per hour)
        """
        logger.info("🎬 Starting Time Travel Demo Sequence...")
        logger.info("=" * 60)
        logger.info("This simulates 6 hours of disaster escalation in 2 minutes")
        logger.info("=" * 60)

        scenarios = [
            {"hour": 0, "intensity": 0.2, "label": "10:00 AM - Initial signals detected"},
            {"hour": 1, "intensity": 0.35, "label": "11:00 AM - Risk levels rising"},
            {"hour": 2, "intensity": 0.55, "label": "12:00 PM - HOTSPOT DETECTED"},
            {"hour": 3, "intensity": 0.70, "label": "1:00 PM - Multiple critical reports"},
            {"hour": 4, "intensity": 0.85, "label": "2:00 PM - ESCALATION CRITICAL"},
            {"hour": 5, "intensity": 0.95, "label": "3:00 PM - Peak disaster conditions"},
            {"hour": 6, "intensity": 0.75, "label": "4:00 PM - Response underway"}
        ]

        for scenario in scenarios:
            logger.info(f"\n⏰ {scenario['label']}")
            logger.info(f"   Intensity: {scenario['intensity']*100:.0f}%")

            self.simulate_time_period(scenario['hour'], scenario['intensity'])

            logger.info(f"   ✅ Events published to Kafka")

            # Wait 20 seconds before next hour (total 140 seconds = ~2.3 minutes)
            if scenario != scenarios[-1]:
                time.sleep(20)

        logger.info("\n" + "=" * 60)
        logger.info("🎉 Time Travel Demo Complete!")
        logger.info("=" * 60)
        logger.info("\nYou just saw 6 hours of disaster escalation in 2 minutes!")
        logger.info("Check your dashboard to see the prediction timeline.")

if __name__ == "__main__":
    print("🚀 CrisisFlow Time Travel Mode")
    print("=" * 60)
    print("This will simulate a complete disaster escalation")
    print("Perfect for demo videos and presentations")
    print("=" * 60)

    input("Press ENTER to start the simulation...")

    simulator = TimeTravelSimulator()
    simulator.run_demo_sequence()

    print("\n✅ Simulation complete! Check your CrisisFlow dashboard.")