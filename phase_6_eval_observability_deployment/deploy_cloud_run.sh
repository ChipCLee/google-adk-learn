#!/usr/bin/env bash
# Deployment script for deploying Google ADK agent service to Google Cloud Run

set -euo pipefail

# Configuration variables
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="adk-agent-service"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "======================================================="
echo "Deploying Google ADK Agent to Cloud Run"
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Service:  ${SERVICE_NAME}"
echo "======================================================="

# 1. Build container image using Google Cloud Build
echo "==> Step 1: Building container image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_TAG}" .

# 2. Deploy container to Cloud Run
echo "==> Step 2: Deploying to Google Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --platform managed \
    --region "${REGION}" \
    --allow-unauthenticated \
    --set-env-vars "ADK_ENV=production" \
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

echo "==> Step 3: Deployment completed successfully!"
gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format "value(status.url)"
