"""
Configuration for CrisisFlow producers
"""
import os
import json
import logging
import colorlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = logging.getLogger('CrisisFlow')
logger.addHandler(handler)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

# Tomorrow.io Configuration
TOMORROW_API_KEY = os.getenv('TOMORROW_API_KEY')
TOMORROW_BASE_URL = "https://api.tomorrow.io/v4"

# Confluent Configuration
CONFLUENT_CONFIG = {
    'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
    'sasl.mechanisms': 'PLAIN',
    'security.protocol': 'SASL_SSL',
    'sasl.username': os.getenv('CONFLUENT_API_KEY'),
    'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
    'client.id': 'crisisflow-producer',
    'acks': 'all',
    'enable.idempotence': 'true',
    'max.in.flight.requests.per.connection': 5,
    'retries': 10,
    'retry.backoff.ms': 100
}

# Topics
WEATHER_TOPIC = 'weather_risks'
SOCIAL_TOPIC = 'social_signals'

# Locations to monitor - Expanded to 40 global cities
try:
    locations_env = os.getenv('LOCATIONS')
    if locations_env:
        LOCATIONS = json.loads(locations_env)
    else:
        raise ValueError("No LOCATIONS env var, using defaults")
except (json.JSONDecodeError, ValueError):
    LOCATIONS = [
        # United States - Major Cities (20)
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
        {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
        {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
        {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
        {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
        {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
        {"name": "Jacksonville", "lat": 30.3322, "lon": -81.6557},
        {"name": "Fort Worth", "lat": 32.7555, "lon": -97.3308},
        {"name": "Columbus", "lat": 39.9612, "lon": -82.9988},
        {"name": "Charlotte", "lat": 35.2271, "lon": -80.8431},
        {"name": "Indianapolis", "lat": 39.7684, "lon": -86.1581},
        {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
        {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
        {"name": "Nashville", "lat": 36.1627, "lon": -86.7816},
        {"name": "Portland", "lat": 45.5152, "lon": -122.6784},

        # International - Major Cities (10)
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
        {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
        {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
        {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694},
        {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332},

        # High-Risk Areas (10)
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},  # Earthquake zone
        {"name": "Miami", "lat": 25.7617, "lon": -80.1918},  # Hurricane zone
        {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715},  # Hurricane/flood zone
        {"name": "Manila", "lat": 14.5995, "lon": 120.9842},  # Typhoon zone
        {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456},  # Flood zone
        {"name": "Dhaka", "lat": 23.8103, "lon": 90.4125},  # Flood zone
        {"name": "Lagos", "lat": 6.5244, "lon": 3.3792},  # Flood zone
        {"name": "Karachi", "lat": 24.8607, "lon": 67.0011},  # Heat/flood zone
        {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},  # Flood/landslide zone
        {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784}  # Earthquake zone
    ]

# Polling interval (15 minutes = 900 seconds to stay under rate limit)
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '900'))

# Social producer configuration
SOCIAL_MIN_INTERVAL = 30  # minimum seconds between social posts
SOCIAL_MAX_INTERVAL = 60  # maximum seconds between social posts

# Risk level thresholds
RISK_THRESHOLDS = {
    'critical': 70,
    'high': 50,
    'moderate': 30,
    'low': 0
}

def calculate_risk_level(fire_index=0, flood_index=0):
    """Calculate risk level based on fire and flood indices"""
    max_index = max(fire_index or 0, flood_index or 0)

    for level, threshold in RISK_THRESHOLDS.items():
        if max_index >= threshold:
            return level

    return 'low'

# Validate configuration
def validate_config():
    """Validate that all required configuration is present"""
    errors = []

    if not TOMORROW_API_KEY:
        errors.append("TOMORROW_API_KEY is not set")

    if not os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'):
        errors.append("CONFLUENT_BOOTSTRAP_SERVERS is not set")

    if not os.getenv('CONFLUENT_API_KEY'):
        errors.append("CONFLUENT_API_KEY is not set")

    if not os.getenv('CONFLUENT_API_SECRET'):
        errors.append("CONFLUENT_API_SECRET is not set")

    if not LOCATIONS:
        errors.append("No locations configured")

    if errors:
        for error in errors:
            logger.error(error)
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    logger.info(f"Configuration validated successfully")
    logger.info(f"Monitoring {len(LOCATIONS)} locations")
    logger.info(f"Poll interval: {POLL_INTERVAL_SECONDS} seconds")
    logger.info(f"Bootstrap servers: {CONFLUENT_CONFIG['bootstrap.servers']}")

if __name__ == '__main__':
    validate_config()
    print("Configuration is valid!")