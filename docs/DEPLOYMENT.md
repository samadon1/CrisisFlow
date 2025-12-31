# 🚀 CrisisFlow Deployment Guide

This guide walks you through deploying CrisisFlow to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Create one at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install from [here](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install from [docker.com](https://www.docker.com/get-started)
4. **API Keys**:
   - Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Tomorrow.io API key from [Tomorrow.io](https://www.tomorrow.io/weather-api/)
   - Confluent Cloud credentials from [Confluent](https://confluent.cloud)

## Quick Deploy

### 1. Clone and Prepare

```bash
git clone <your-repo>
cd CrisisFlow
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Deploy to Cloud Run

```bash
# Login to Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Run the deployment script
./scripts/deploy.sh YOUR_PROJECT_ID
```

## Manual Deployment Steps

### Backend Deployment

1. **Build the Docker image**:
```bash
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/crisisflow-backend .
```

2. **Push to Google Container Registry**:
```bash
docker push gcr.io/YOUR_PROJECT_ID/crisisflow-backend
```

3. **Deploy to Cloud Run**:
```bash
gcloud run deploy crisisflow-backend \
  --image gcr.io/YOUR_PROJECT_ID/crisisflow-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="GOOGLE_API_KEY=your_key" \
  --set-env-vars="TOMORROW_API_KEY=your_key" \
  --set-env-vars="CONFLUENT_BOOTSTRAP_SERVERS=your_servers" \
  --set-env-vars="CONFLUENT_API_KEY=your_key" \
  --set-env-vars="CONFLUENT_API_SECRET=your_secret"
```

### Frontend Deployment

1. **Update API endpoint**:
```bash
cd frontend
echo "VITE_API_URL=https://crisisflow-backend-xxxxx-uc.a.run.app/api" > .env.production
```

2. **Build and deploy**:
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/crisisflow-frontend .
docker push gcr.io/YOUR_PROJECT_ID/crisisflow-frontend

gcloud run deploy crisisflow-frontend \
  --image gcr.io/YOUR_PROJECT_ID/crisisflow-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## Environment Variables

### Backend (set in Cloud Run):
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `TOMORROW_API_KEY`: Your Tomorrow.io weather API key
- `CONFLUENT_BOOTSTRAP_SERVERS`: Kafka bootstrap servers
- `CONFLUENT_API_KEY`: Confluent API key
- `CONFLUENT_API_SECRET`: Confluent API secret
- `PORT`: 8080 (default for Cloud Run)

### Frontend (build-time):
- `VITE_API_URL`: Backend API URL (https://your-backend.a.run.app/api)

## Post-Deployment

1. **Test the deployment**:
   - Visit your frontend URL
   - Check backend health: `https://your-backend.a.run.app/api/health`
   - Monitor logs in Cloud Console

2. **Set up monitoring**:
   ```bash
   gcloud alpha monitoring dashboards create --config-from-file=monitoring.json
   ```

3. **Configure custom domain** (optional):
   ```bash
   gcloud run domain-mappings create \
     --service crisisflow-frontend \
     --domain your-domain.com \
     --region us-central1
   ```

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="user:your-email@gmail.com" \
     --role="roles/run.admin"
   ```

2. **Container fails to start**:
   - Check logs: `gcloud run services logs read crisisflow-backend`
   - Verify environment variables are set correctly

3. **Frontend can't reach backend**:
   - Ensure CORS is configured in backend
   - Check that backend URL in frontend is correct
   - Verify both services are deployed in same region

## Cost Optimization

- **Minimum instances**: Set to 0 for development, 1 for production
- **Maximum instances**: Limit based on expected traffic
- **Memory**: Start with 512Mi for frontend, 1Gi for backend
- **CPU**: 1 CPU is usually sufficient for both services

## CI/CD with Cloud Build

For automated deployments on git push:

1. Connect your GitHub repo to Cloud Build
2. Create a trigger using the provided `cloudbuild.yaml`
3. Set substitution variables for API keys
4. Push to main branch to trigger deployment

## Security Best Practices

1. **Never commit API keys** - Use Secret Manager instead:
   ```bash
   echo -n "your-api-key" | gcloud secrets create google-api-key --data-file=-
   ```

2. **Enable authentication** for production:
   ```bash
   gcloud run services update crisisflow-backend --no-allow-unauthenticated
   ```

3. **Set up VPC connector** for database access:
   ```bash
   gcloud compute networks vpc-access connectors create crisisflow-connector \
     --region us-central1 \
     --subnet your-subnet
   ```

## Support

For issues or questions:
- Check the [Cloud Run documentation](https://cloud.google.com/run/docs)
- Review application logs in Cloud Console
- Open an issue in the GitHub repository

## Estimated Costs

With Cloud Run's pay-per-use model:
- **Development**: ~$5-10/month
- **Production** (1000 users/day): ~$30-50/month
- **High traffic** (10k+ users/day): ~$100-200/month

Free tier includes:
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds of compute time