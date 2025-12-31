"""
Kafka Consumer for CrisisFlow Backend
Manages connection to Confluent Cloud and event consumption
"""
import json
import asyncio
import os
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from confluent_kafka import Consumer, KafkaError
from config import (
    logger,
    CONFLUENT_CONSUMER_CONFIG,
    WEATHER_TOPIC,
    SOCIAL_TOPIC,
    EVENT_CACHE_SIZE
)

class KafkaEventConsumer:
    def __init__(self):
        """Initialize Kafka consumer with in-memory cache"""
        self.consumer = None
        self.running = False

        # Cache directory setup
        self.cache_dir = Path(__file__).parent / "data"
        self.cache_dir.mkdir(exist_ok=True)

        # Cache file paths
        self.weather_cache_file = self.cache_dir / "weather_events.json"
        self.social_cache_file = self.cache_dir / "social_events.json"
        self.hotspots_cache_file = self.cache_dir / "hotspots.json"

        # In-memory caches for latest events
        self.weather_events = deque(maxlen=EVENT_CACHE_SIZE)
        self.social_events = deque(maxlen=EVENT_CACHE_SIZE)

        # Cache for aggregated data
        self.hotspots_cache = None
        self.hotspots_cache_time = None

        # Load cached data from disk on startup
        self._load_cache_from_disk()

        # Start periodic cache saving
        self.last_cache_save = datetime.utcnow()

        logger.info("Kafka consumer initialized with persistent cache")

    def _load_cache_from_disk(self):
        """Load cached events from disk on startup"""
        try:
            # Load weather events
            if self.weather_cache_file.exists():
                with open(self.weather_cache_file, 'r') as f:
                    cached_weather = json.load(f)
                    for event in cached_weather[-EVENT_CACHE_SIZE:]:  # Only load up to cache size
                        self.weather_events.append(event)
                logger.info(f"Loaded {len(self.weather_events)} weather events from cache")

            # Load social events
            if self.social_cache_file.exists():
                with open(self.social_cache_file, 'r') as f:
                    cached_social = json.load(f)
                    for event in cached_social[-EVENT_CACHE_SIZE:]:
                        self.social_events.append(event)
                logger.info(f"Loaded {len(self.social_events)} social events from cache")

            # Load hotspots
            if self.hotspots_cache_file.exists():
                with open(self.hotspots_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.hotspots_cache = cache_data.get("hotspots", [])
                    cache_time_str = cache_data.get("cache_time")
                    if cache_time_str:
                        self.hotspots_cache_time = datetime.fromisoformat(cache_time_str.replace('Z', '+00:00'))
                logger.info(f"Loaded {len(self.hotspots_cache) if self.hotspots_cache else 0} hotspots from cache")

        except Exception as e:
            logger.warning(f"Could not load cache from disk: {e}")

    async def _save_cache_to_disk(self):
        """Save current cache to disk"""
        try:
            # Save weather events
            with open(self.weather_cache_file, 'w') as f:
                json.dump(list(self.weather_events), f)

            # Save social events
            with open(self.social_cache_file, 'w') as f:
                json.dump(list(self.social_events), f)

            # Save hotspots
            if self.hotspots_cache:
                with open(self.hotspots_cache_file, 'w') as f:
                    json.dump({
                        "hotspots": self.hotspots_cache,
                        "cache_time": self.hotspots_cache_time.isoformat() if self.hotspots_cache_time else None
                    }, f)

            logger.debug("Cache saved to disk")
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")

    async def start(self):
        """Start the consumer and background polling task"""
        try:
            self.consumer = Consumer(CONFLUENT_CONSUMER_CONFIG)
            self.consumer.subscribe([WEATHER_TOPIC, SOCIAL_TOPIC])
            self.running = True

            # Start background polling task
            asyncio.create_task(self._poll_loop())

            # Start periodic cache saving task
            asyncio.create_task(self._cache_save_loop())

            logger.info(f"Kafka consumer started, subscribed to topics: {WEATHER_TOPIC}, {SOCIAL_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self):
        """Stop the consumer"""
        self.running = False

        # Save cache one final time before stopping
        await self._save_cache_to_disk()

        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")

    async def _poll_loop(self):
        """Background task to continuously poll for messages"""
        while self.running:
            try:
                # Poll for messages (non-blocking with timeout)
                msg = self.consumer.poll(timeout=0.1)

                if msg is None:
                    await asyncio.sleep(0.1)
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue

                # Process the message
                self._process_message(msg)

            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                await asyncio.sleep(1)

    async def _cache_save_loop(self):
        """Periodically save cache to disk"""
        while self.running:
            try:
                # Save cache every 30 seconds
                await asyncio.sleep(30)
                await self._save_cache_to_disk()
                self.last_cache_save = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error in cache save loop: {e}")

    def _process_message(self, msg):
        """Process a Kafka message and add to appropriate cache"""
        try:
            # Track processing start time
            start_time = datetime.utcnow()

            topic = msg.topic()
            value = json.loads(msg.value().decode('utf-8'))

            if topic == WEATHER_TOPIC:
                self.weather_events.append(value)
                logger.debug(f"Cached weather event: {value.get('location', {}).get('name')} - Risk: {value.get('risk_level')}")

            elif topic == SOCIAL_TOPIC:
                self.social_events.append(value)
                logger.debug(f"Cached social event: {value.get('data', {}).get('category')} - Urgency: {value.get('data', {}).get('urgency')}")

            # Track processing metrics
            try:
                from stream_analytics import stream_analytics
                from prediction_engine import prediction_engine

                # Record event processing
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                stream_analytics.record_event(processing_time)

                # Add to prediction engine for analysis
                prediction_engine.add_event(value)
            except ImportError:
                pass  # Stream analytics not yet available

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def get_latest_events(self, limit: int = 50) -> Dict[str, List]:
        """Get latest events from cache"""
        return {
            "weather": list(self.weather_events)[-limit:],
            "social": list(self.social_events)[-limit:],
            "last_updated": datetime.utcnow().isoformat()
        }

    def clear_cache(self, keep_percentage: float = 0.2) -> Dict:
        """
        Clear the event cache, optionally keeping a percentage of recent events
        to maintain some continuity
        """
        try:
            # Calculate how many events to keep
            weather_keep = int(len(self.weather_events) * keep_percentage)
            social_keep = int(len(self.social_events) * keep_percentage)

            # Keep only the most recent events
            if weather_keep > 0:
                recent_weather = list(self.weather_events)[-weather_keep:]
                self.weather_events.clear()
                for event in recent_weather:
                    self.weather_events.append(event)
            else:
                self.weather_events.clear()

            if social_keep > 0:
                recent_social = list(self.social_events)[-social_keep:]
                self.social_events.clear()
                for event in recent_social:
                    self.social_events.append(event)
            else:
                self.social_events.clear()

            # Clear hotspot cache to force recalculation
            self.hotspots_cache = None
            self.hotspots_cache_time = None

            # Save the cleared cache to disk
            asyncio.create_task(self._save_cache_to_disk())

            logger.info(f"Cache cleared. Kept {weather_keep} weather and {social_keep} social events")

            return {
                "status": "success",
                "weather_events_kept": weather_keep,
                "social_events_kept": social_keep,
                "message": f"Cache cycled, kept {int(keep_percentage * 100)}% of recent events"
            }
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_stats(self) -> Dict:
        """Get statistics about cached events"""
        # Count events by risk level
        risk_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
        for event in self.weather_events:
            risk_level = event.get("risk_level", "low")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

        # Count social events by urgency
        urgency_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {}
        for event in self.social_events:
            urgency = event.get("data", {}).get("urgency", "low")
            if urgency in urgency_counts:
                urgency_counts[urgency] += 1

            category = event.get("data", {}).get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "weather": {
                "total": len(self.weather_events),
                "by_risk": risk_counts
            },
            "social": {
                "total": len(self.social_events),
                "by_urgency": urgency_counts,
                "by_category": category_counts
            },
            "cache_time": datetime.utcnow().isoformat()
        }

    async def get_hotspots(self) -> List[Dict]:
        """
        Get aggregated hotspots
        In a real implementation, this would query ksqlDB
        For now, we'll create synthetic hotspots from cached events
        """
        # Check cache
        if self.hotspots_cache and self.hotspots_cache_time:
            if datetime.utcnow() - self.hotspots_cache_time < timedelta(seconds=60):
                return self.hotspots_cache

        # Create synthetic hotspots from cached events
        hotspots = []
        grid_data = {}

        # Aggregate weather events by grid
        for event in self.weather_events:
            lat = event.get("location", {}).get("lat", 0)
            lon = event.get("location", {}).get("lon", 0)

            # Round to 0.5 degree grid
            grid_lat = round(lat * 2) / 2
            grid_lon = round(lon * 2) / 2
            grid_key = f"{grid_lat},{grid_lon}"

            if grid_key not in grid_data:
                grid_data[grid_key] = {
                    "grid_lat": grid_lat,
                    "grid_lon": grid_lon,
                    "weather_count": 0,
                    "social_count": 0,
                    "fire_indices": [],
                    "flood_indices": [],
                    "max_risk": "low"
                }

            grid_data[grid_key]["weather_count"] += 1
            grid_data[grid_key]["fire_indices"].append(
                event.get("data", {}).get("fire_index", 0)
            )
            grid_data[grid_key]["flood_indices"].append(
                event.get("data", {}).get("flood_index", 0)
            )

            # Update max risk
            risk = event.get("risk_level", "low")
            if risk == "critical" or grid_data[grid_key]["max_risk"] != "critical":
                grid_data[grid_key]["max_risk"] = risk

        # Aggregate social events by grid
        for event in self.social_events:
            lat = event.get("location", {}).get("lat", 0)
            lon = event.get("location", {}).get("lon", 0)

            grid_lat = round(lat * 2) / 2
            grid_lon = round(lon * 2) / 2
            grid_key = f"{grid_lat},{grid_lon}"

            if grid_key in grid_data:
                grid_data[grid_key]["social_count"] += 1

        # Convert to hotspot list
        for grid_key, data in grid_data.items():
            avg_fire = sum(data["fire_indices"]) / len(data["fire_indices"]) if data["fire_indices"] else 0
            avg_flood = sum(data["flood_indices"]) / len(data["flood_indices"]) if data["flood_indices"] else 0

            hotspot = {
                "grid_lat": data["grid_lat"],
                "grid_lon": data["grid_lon"],
                "event_count": data["weather_count"] + data["social_count"],
                "avg_fire_index": round(avg_fire, 1),
                "avg_flood_index": round(avg_flood, 1),
                "social_count": data["social_count"],
                "risk_level": data["max_risk"],
                "window_start": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "window_end": datetime.utcnow().isoformat()
            }
            hotspots.append(hotspot)

        # Sort by risk level and event count
        risk_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
        hotspots.sort(key=lambda x: (risk_order.get(x["risk_level"], 3), -x["event_count"]))

        # Cache the results
        self.hotspots_cache = hotspots
        self.hotspots_cache_time = datetime.utcnow()

        return hotspots

# Global consumer instance
consumer = KafkaEventConsumer()