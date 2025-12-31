#!/bin/bash

# CrisisFlow Deployment Script for Google Cloud Run
# Usage: ./deploy.sh [project-id]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if project ID is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide your GCP project ID${NC}"
    echo "Usage: ./deploy.sh your-project-id"
    exit 1
fi

PROJECT_ID=$1
REGION="us-central1"
BACKEND_SERVICE="crisisflow-backend"
FRONTEND_SERVICE="crisisflow-frontend"

echo -e "${GREEN}🚀 Starting CrisisFlow deployment to Google Cloud Run${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com

# Build and deploy backend
echo -e "${GREEN}Building and deploying backend...${NC}"
cd backend

# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE

# Deploy to Cloud Run
gcloud run deploy $BACKEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 1 \
    --port 8080 \
    --set-env-vars="PORT=8080"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo -e "${GREEN}Backend deployed at: $BACKEND_URL${NC}"

# Build and deploy frontend
echo -e "${GREEN}Building and deploying frontend...${NC}"
cd ../frontend

# Update frontend to use backend URL
echo "VITE_API_URL=$BACKEND_URL/api" > .env.production

# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --port 8080

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "🌐 Frontend: $FRONTEND_URL"
echo "🔧 Backend API: $BACKEND_URL"
echo ""
echo -e "${YELLOW}⚠️  Important: Set environment variables in Cloud Console:${NC}"
echo "  - GOOGLE_API_KEY"
echo "  - TOMORROW_API_KEY"
echo "  - CONFLUENT_BOOTSTRAP_SERVERS"
echo "  - CONFLUENT_API_KEY"
echo "  - CONFLUENT_API_SECRET"
echo ""
echo "Visit: https://console.cloud.google.com/run/detail/$REGION/$BACKEND_SERVICE/revisions?project=$PROJECT_ID"