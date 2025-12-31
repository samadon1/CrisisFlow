#!/bin/bash

# CrisisFlow Deployment Script with Environment Variables
# Usage: ./deploy-with-env.sh [project-id]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if project ID is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide your GCP project ID${NC}"
    echo "Usage: ./deploy-with-env.sh your-project-id"
    exit 1
fi

PROJECT_ID=$1
REGION="us-central1"
BACKEND_SERVICE="crisisflow-backend"
FRONTEND_SERVICE="crisisflow-frontend"

# Your actual API keys (from .env.production)
GOOGLE_API_KEY="AIzaSyAldHaInfwzi9LnNnkp442MOt62ZiSCfDM"
TOMORROW_API_KEY="YSP59hBPuA0CMyqj5g8NQ1Dr4FiFApww"
CONFLUENT_BOOTSTRAP_SERVERS="pkc-619z3.us-east1.gcp.confluent.cloud:9092"
CONFLUENT_API_KEY="3YWHXAOZLWCA7DLC"
CONFLUENT_API_SECRET="cflt9GCILwSuuLFw2xqeSwsIGJ9IwgSu6Ohz5GSRUE2y+oeus6JhVAFqI8mEGbIQ"

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
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo -e "${YELLOW}Setting up Artifact Registry...${NC}"
gcloud artifacts repositories create crisisflow \
    --repository-format=docker \
    --location=$REGION \
    --description="CrisisFlow Docker images" 2>/dev/null || true

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and deploy backend
echo -e "${GREEN}Building and deploying backend...${NC}"
cd backend

# Build container with Artifact Registry
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/crisisflow/${BACKEND_SERVICE}:latest"
docker build -t $IMAGE_URL .

# Push to Artifact Registry
docker push $IMAGE_URL

# Deploy to Cloud Run with environment variables
gcloud run deploy $BACKEND_SERVICE \
    --image=$IMAGE_URL \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --max-instances=10 \
    --min-instances=0 \
    --port=8080 \
    --set-env-vars="PORT=8080" \
    --set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
    --set-env-vars="TOMORROW_API_KEY=${TOMORROW_API_KEY}" \
    --set-env-vars="CONFLUENT_BOOTSTRAP_SERVERS=${CONFLUENT_BOOTSTRAP_SERVERS}" \
    --set-env-vars="CONFLUENT_API_KEY=${CONFLUENT_API_KEY}" \
    --set-env-vars="CONFLUENT_API_SECRET=${CONFLUENT_API_SECRET}" \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="LOG_LEVEL=INFO"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --platform=managed \
    --region=$REGION \
    --format='value(status.url)')

echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}"

# Build and deploy frontend
echo -e "${GREEN}Building and deploying frontend...${NC}"
cd ../frontend

# Update frontend to use backend URL
echo "VITE_API_URL=${BACKEND_URL}/api" > .env.production

# Build container with Artifact Registry
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/crisisflow/${FRONTEND_SERVICE}:latest"

# Create a temporary nginx config with backend URL
cat > nginx.conf << EOF
server {
    listen 8080;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass ${BACKEND_URL};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Build with the backend URL baked in
docker build \
    --build-arg VITE_API_URL="${BACKEND_URL}/api" \
    -t $FRONTEND_IMAGE .

# Clean up temp nginx config
rm nginx.conf

# Push to Artifact Registry
docker push $FRONTEND_IMAGE

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE \
    --image=$FRONTEND_IMAGE \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=10 \
    --min-instances=0 \
    --port=8080

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
    --platform=managed \
    --region=$REGION \
    --format='value(status.url)')

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "======================================"
echo "🌐 Frontend URL: ${FRONTEND_URL}"
echo "🔧 Backend API: ${BACKEND_URL}"
echo "======================================"
echo ""
echo "📊 Monitor your services:"
echo "https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo ""
echo "📝 View logs:"
echo "gcloud run services logs read ${BACKEND_SERVICE} --region=${REGION}"
echo "gcloud run services logs read ${FRONTEND_SERVICE} --region=${REGION}"
echo ""
echo -e "${YELLOW}⚠️  Note: It may take a few minutes for the services to be fully ready.${NC}"
echo -e "${GREEN}✨ Your CrisisFlow platform is now live in the cloud!${NC}"