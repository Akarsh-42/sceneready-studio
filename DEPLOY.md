# Reproduce or update the Cloud Run deployment

SceneReady is currently deployed as the Cloud Run service `sceneready-studio` in
`us-central1`. These instructions reproduce or update that deployment. The production
artifact is the repository's FastAPI browser application—not the ADK development web UI.

## 1. Project and runtime identity

In Cloud Shell:

```bash
export GOOGLE_CLOUD_PROJECT=project-3164c7d4-a464-41b4-ae9
export STUDIO_RUNTIME_SA="sceneready-runtime@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"

gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --project="$GOOGLE_CLOUD_PROJECT"

gcloud iam service-accounts create sceneready-runtime --display-name="SceneReady runtime" --project="$GOOGLE_CLOUD_PROJECT"

gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" --member="serviceAccount:$STUDIO_RUNTIME_SA" --role=roles/aiplatform.user

gcloud secrets add-iam-policy-binding parallel-api-key --project="$GOOGLE_CLOUD_PROJECT" --member="serviceAccount:$STUDIO_RUNTIME_SA" --role=roles/secretmanager.secretAccessor
```

If the account already exists, reuse it; do not create duplicate accounts. If an IAM
command fails, inspect the specific permission error rather than granting Owner.

## 2. Protect paid requests

Create a new Secret Manager secret named `sceneready-access-token` with a unique,
private access code of at least 24 characters. This is separate from the Parallel key.
The dashboard requests this code before making paid API requests. Do not commit it,
include it in the demo video, or put it in a public README. Arrange private judge access
through an organizer-approved channel and verify that judging access works.

```bash
gcloud secrets add-iam-policy-binding sceneready-access-token --project="$GOOGLE_CLOUD_PROJECT" --member="serviceAccount:$STUDIO_RUNTIME_SA" --role=roles/secretmanager.secretAccessor
```

In Secret Manager, note the enabled version NUMBER of the working Parallel secret and
the access-code secret. Set these variables to those numbers (not to secret values):

```bash
export PARALLEL_SECRET_VERSION=1
export ACCESS_SECRET_VERSION=1
```

Use `1` only if that is the correct enabled version. Secret values are injected by
Cloud Run, not passed on a command line. Pinning versions makes deployment repeatable.

## 3. Deploy or update

```bash
cd ~/sceneready-studio
git pull --ff-only
bash scripts/deploy.sh
```

This explicitly publishes the dashboard URL; the paid run endpoint remains protected
by the access code. It builds a Docker image with Cloud Build and uses a dedicated
runtime service account. Source deployment can require additional permissions for
the deployer and the BUILD service account, separate from the runtime account. Follow
the actual Cloud Build error and the official source-deployment docs if those are missing.

Configured limits: one instance, four HTTP requests per instance, at most two active
workflows per process, 480-second request timeout, zero minimum instances. These are
operational limits, not a billing cap. Configure billing alerts separately.

On a newly reconnected Cloud Shell, export the four variables again before invoking the
script. Secret *values* remain in Secret Manager; only their enabled version numbers are
used here.

## 4. Verify the hosted app

- Open the URL, provide the studio access code, and complete a live example.
- Verify exact citations and research failures in the dashboard.
- Review/assign a task and download both exports.
- Confirm changing the input creates a fresh, unreviewed plan.
- Verify an incorrect access code cannot start research.
- Import an original PDF under 8 MiB, review the extracted text, and complete a plan.
- Verify an incorrect access code cannot import a PDF.
- Confirm there are no credentials or confidential content in the public repository.
- Check both desktop and mobile-width layouts with a hard refresh after each deployment.
- Record the demo only once the deployed path works as described.

Official references:
https://docs.cloud.google.com/run/docs/configuring/services/secrets
https://docs.cloud.google.com/run/docs/configuring/services/build-service-account
