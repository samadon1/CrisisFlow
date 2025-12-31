#!/bin/bash

# Start Social Producer
echo "Starting CrisisFlow Social Producer..."

cd producers
source venv/bin/activate
python social_producer.py