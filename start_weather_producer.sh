#!/bin/bash

# Start Weather Producer
echo "Starting CrisisFlow Weather Producer..."

cd producers
source venv/bin/activate
python weather_producer.py