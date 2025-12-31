#!/bin/bash

# CrisisFlow Deployment Script
# Deploys backend to Google Cloud Run and frontend to Vercel

set -e

echo "🚀 CrisisFlow Deployment Script"
echo "================================"

# Check for required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT not set"
    echo "Please run: export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

# Deploy Backend to Google Cloud Run
deploy_backend() {
    echo "📦 Deploying Backend to Google Cloud Run..."

    cd backend

    # Build container
    echo "Building container..."
    gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/crisisflow-api

    # Deploy to Cloud Run
    echo "Deploying to Cloud Run..."
    gcloud run deploy crisisflow-api \
        --image gcr.io/$GOOGLE_CLOUD_PROJECT/crisisflow-api \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --port 8000 \
        --memory 512Mi \
        --max-instances 10 \
        --set-env-vars "ENVIRONMENT=production"

    # Get the service URL
    SERVICE_URL=$(gcloud run services describe crisisflow-api --platform managed --region us-central1 --format 'value(status.url)')
    echo "✅ Backend deployed at: $SERVICE_URL"

    cd ..
    return 0
}

# Deploy Frontend to Vercel
deploy_frontend() {
    echo "📦 Deploying Frontend to Vercel..."

    cd frontend

    # Update API URL in .env.production
    echo "VITE_API_URL=$SERVICE_URL/api" > .env.production

    # Build frontend
    echo "Building frontend..."
    npm install
    npm run build

    # Deploy to Vercel
    echo "Deploying to Vercel..."
    npx vercel --prod

    echo "✅ Frontend deployed!"

    cd ..
    return 0
}

# Deploy Producers (optional - could run on Cloud Run or Compute Engine)
deploy_producers() {
    echo "📦 Deploying Producers..."
    echo "Note: Producers can run locally or on a VM for the hackathon"
    echo "For production, consider:"
    echo "- Google Compute Engine with startup scripts"
    echo "- Cloud Run Jobs (for scheduled execution)"
    echo "- Kubernetes Engine for orchestration"
}

# Main deployment flow
main() {
    echo "Starting deployment..."

    # Deploy backend first to get the URL
    deploy_backend

    # Deploy frontend with backend URL
    deploy_frontend

    echo ""
    echo "🎉 Deployment Complete!"
    echo "========================"
    echo "Backend: $SERVICE_URL"
    echo "Frontend: Check Vercel dashboard for URL"
    echo ""
    echo "Next steps:"
    echo "1. Update Confluent Cloud topics if needed"
    echo "2. Start producers locally or on a VM"
    echo "3. Monitor logs in Google Cloud Console"
}

# Run main function
main