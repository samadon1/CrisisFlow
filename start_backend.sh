#!/bin/bash

# Start Backend Server
echo "Starting CrisisFlow Backend Server..."

cd backend
source venv/bin/activate
python main.py