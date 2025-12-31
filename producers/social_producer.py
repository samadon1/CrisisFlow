#!/usr/bin/env python3
"""
Social Producer for CrisisFlow
Simulates disaster-related social media posts using CrisisNLP dataset
"""
import json
import time
import uuid
import random
from datetime import datetime, timezone
from confluent_kafka import Producer
from config import (
    logger,
    CONFLUENT_CONFIG,
    SOCIAL_TOPIC,
    SOCIAL_MIN_INTERVAL,
    SOCIAL_MAX_INTERVAL,
    validate_config
)

class SocialProducer:
    def __init__(self):
        """Initialize the social producer"""
        validate_config()
        self.producer = Producer(CONFLUENT_CONFIG)
        self.tweets = self.load_crisis_tweets()
        self.tweet_index = 0
        logger.info(f"Social Producer initialized with {len(self.tweets)} crisis tweets")

    def load_crisis_tweets(self):
        """Load crisis tweets from JSON file"""
        try:
            with open('data/crisis_tweets.json', 'r') as f:
                tweets = json.load(f)
                # Shuffle tweets for variety
                random.shuffle(tweets)
                return tweets
        except Exception as e:
            logger.error(f"Error loading crisis tweets: {e}")
            # Fallback tweets if file fails to load
            return [
                {
                    "text": "Emergency: Flooding reported in downtown area",
                    "category": "flood",
                    "base_lat": 29.76,
                    "base_lon": -95.36,
                    "urgency": "high"
                }
            ]

    def delivery_report(self, err, msg):
        """Callback for message delivery reports"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def generate_social_event(self):
        """Generate a social signal event from crisis tweets"""
        # Get next tweet (cycle through list)
        tweet = self.tweets[self.tweet_index]
        self.tweet_index = (self.tweet_index + 1) % len(self.tweets)

        # Add random offset to coordinates (simulate geographic spread)
        # About 0.01 degrees = ~1.1 km
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)

        event = {
            "event_id": str(uuid.uuid4()),
            "source": "social",
            "location": {
                "lat": round(tweet['base_lat'] + lat_offset, 6),
                "lon": round(tweet['base_lon'] + lon_offset, 6)
            },
            "data": {
                "text": tweet['text'],
                "category": tweet['category'],
                "urgency": tweet['urgency'],
                "verified": random.choice([True, False, False])  # 33% verified
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return event

    def publish_event(self, event):
        """Publish event to Kafka"""
        try:
            key = f"social_{event['event_id'][:8]}"
            value = json.dumps(event)

            self.producer.produce(
                topic=SOCIAL_TOPIC,
                key=key,
                value=value,
                callback=self.delivery_report
            )

            # Log with emoji for category
            emoji_map = {
                'flood': '🌊',
                'fire': '🔥',
                'storm': '⛈️',
                'evacuation': '🏃',
                'rescue': '🚁',
                'medical': '🏥',
                'infrastructure': '🏗️',
                'hazmat': '☢️',
                'landslide': '🏔️',
                'public_health': '⚕️',
                'security': '🚔',
                'response': '🚨',
                'missing': '🔍',
                'warning': '⚠️',
                'emergency': '🆘'
            }

            emoji = emoji_map.get(event['data']['category'], '📱')
            urgency_color = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(event['data']['urgency'], '⚪')

            logger.info(f"{emoji} Social signal: {urgency_color} [{event['data']['urgency']}] "
                       f"@ ({event['location']['lat']:.4f}, {event['location']['lon']:.4f}) - "
                       f"\"{event['data']['text'][:50]}...\"")

        except Exception as e:
            logger.error(f"Error publishing social event: {e}")

    def simulate_crisis_intensity(self):
        """
        Simulate varying crisis intensity by adjusting post frequency
        Returns sleep interval in seconds
        """
        hour = datetime.now().hour

        # Simulate higher activity during certain hours (disaster escalation)
        if 14 <= hour <= 18:  # Afternoon peak
            # More frequent posts during "crisis peak"
            return random.uniform(SOCIAL_MIN_INTERVAL / 2, SOCIAL_MAX_INTERVAL / 2)
        elif 6 <= hour <= 22:  # Daytime
            # Normal frequency
            return random.uniform(SOCIAL_MIN_INTERVAL, SOCIAL_MAX_INTERVAL)
        else:  # Night time
            # Less frequent
            return random.uniform(SOCIAL_MIN_INTERVAL * 2, SOCIAL_MAX_INTERVAL * 2)

    def run_burst(self, count=5):
        """Generate a burst of social signals (simulating sudden event)"""
        logger.warning(f"CRISIS BURST: Generating {count} rapid social signals")
        for i in range(count):
            event = self.generate_social_event()
            self.publish_event(event)
            time.sleep(random.uniform(0.5, 2))  # Rapid succession
        self.producer.flush()

    def run(self):
        """Main producer loop"""
        logger.info(f"Starting Social Producer - Posting every {SOCIAL_MIN_INTERVAL}-{SOCIAL_MAX_INTERVAL} seconds")
        burst_counter = 0

        while True:
            try:
                # Occasionally trigger a burst (simulating crisis escalation)
                burst_counter += 1
                if burst_counter % 20 == 0:  # Every ~20 posts
                    self.run_burst(random.randint(3, 7))
                else:
                    # Normal single post
                    event = self.generate_social_event()
                    self.publish_event(event)

                # Flush periodically
                if burst_counter % 10 == 0:
                    self.producer.flush()

                # Calculate next interval based on simulated intensity
                sleep_interval = self.simulate_crisis_intensity()
                logger.debug(f"Next social post in {sleep_interval:.1f} seconds...")
                time.sleep(sleep_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down Social Producer...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(10)  # Wait before retrying

        # Clean shutdown
        self.producer.flush()
        logger.info("Social Producer shutdown complete")

if __name__ == "__main__":
    producer = SocialProducer()
    producer.run()