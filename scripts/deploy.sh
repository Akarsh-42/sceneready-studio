#!/usr/bin/env bash
# Invoke only after the live Cloud Shell run succeeds. See DEPLOY.md first.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT to your project ID}"
: "${STUDIO_RUNTIME_SA:?Set STUDIO_RUNTIME_SA to the runtime service account email}"
: "${PARALLEL_SECRET_VERSION:?Set PARALLEL_SECRET_VERSION to the working secret version number}"
: "${ACCESS_SECRET_VERSION:?Set ACCESS_SECRET_VERSION to the studio access secret version number}"
gcloud run deploy sceneready-studio \
  --project="$GOOGLE_CLOUD_PROJECT" \
  --source=. \
  --region=us-central1 \
  --service-account="$STUDIO_RUNTIME_SA" \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1 \
  --concurrency=4 \
  --timeout=480 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GEMINI_MODEL=gemini-3.8-flash,SCENEREADY_DEMO=0" \
  --set-secrets="PARALLEL_API_KEY=parallel-api-key:$PARALLEL_SECRET_VERSION,STUDIO_ACCESS_TOKEN=sceneready-access-token:$ACCESS_SECRET_VERSION"
