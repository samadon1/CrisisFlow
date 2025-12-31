"""
Configuration for CrisisFlow Backend
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

logger = logging.getLogger('CrisisFlow-API')
logger.addHandler(handler)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

# API Configuration
API_TITLE = "CrisisFlow API"
API_DESCRIPTION = "Real-time disaster intelligence platform"
API_VERSION = "1.0.0"

# Confluent Configuration for Consumer
CONFLUENT_CONSUMER_CONFIG = {
    'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
    'sasl.mechanisms': 'PLAIN',
    'security.protocol': 'SASL_SSL',
    'sasl.username': os.getenv('CONFLUENT_API_KEY'),
    'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
    'group.id': 'crisisflow-backend',
    'auto.offset.reset': 'latest',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'max.poll.interval.ms': 300000
}

# Topics
WEATHER_TOPIC = 'weather_risks'
SOCIAL_TOPIC = 'social_signals'

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Tomorrow.io Weather API Configuration
TOMORROW_IO_API_KEY = os.getenv('TOMORROW_IO_API_KEY') or os.getenv('TOMORROW_API_KEY')

# Cache Configuration
EVENT_CACHE_SIZE = 500  # Number of events to keep in memory (increased for better predictions)
HOTSPOT_CACHE_TTL = 60  # Cache hotspots for 60 seconds

# Locations
try:
    LOCATIONS = json.loads(os.getenv('LOCATIONS', '[]'))
except json.JSONDecodeError:
    LOCATIONS = [
        # United States - Major Cities
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
        {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
        {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
        {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
        {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
        {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
        {"name": "San Jose", "lat": 37.3382, "lon": -121.8863},
        {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
        {"name": "Jacksonville", "lat": 30.3322, "lon": -81.6557},
        {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
        {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
        {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880},
        {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715},
        {"name": "Las Vegas", "lat": 36.1699, "lon": -115.1398},
        {"name": "Portland", "lat": 45.5152, "lon": -122.6784},

        # International - Major Cities
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
        {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
        {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
        {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
        {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694},

        # High-Risk Areas (Hurricanes, Earthquakes, Wildfires)
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},  # Earthquake
        {"name": "Manila", "lat": 14.5995, "lon": 120.9842},  # Typhoons
        {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456},  # Flooding
        {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784},  # Earthquake
        {"name": "Athens", "lat": 37.9838, "lon": 23.7275},  # Wildfires
        {"name": "Brisbane", "lat": -27.4698, "lon": 153.0251},  # Floods/Cyclones
        {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207},  # Earthquake risk
        {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},  # Landslides/Floods
        {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},  # Earthquakes/Typhoons
        {"name": "Cairo", "lat": 30.0444, "lon": 31.2357}  # Heat/Sandstorms
    ]

# CORS Origins (for frontend)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://*.vercel.app",
    "https://*.netlify.app"
]

# Validate configuration
def validate_config():
    """Validate that all required configuration is present"""
    errors = []

    if not os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'):
        errors.append("CONFLUENT_BOOTSTRAP_SERVERS is not set")

    if not os.getenv('CONFLUENT_API_KEY'):
        errors.append("CONFLUENT_API_KEY is not set")

    if not os.getenv('CONFLUENT_API_SECRET'):
        errors.append("CONFLUENT_API_SECRET is not set")

    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY is not set")

    if errors:
        for error in errors:
            logger.error(error)
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    logger.info("Backend configuration validated successfully")