# 🚀 Google Cloud Platform (Cloud Run) Deployment Guide

This guide details how to deploy your Personal Search Engine to **Google Cloud Run**.

## Prerequisites
1.  **Google Cloud Project**: You should have an active GCP project.
2.  **gcloud CLI**: Installed and authenticated (`gcloud auth login`).
3.  **APIs Enabled**: Cloud Run, Cloud Build, Artifact Registry.

## 1. Setup & Configuration

Set your project ID variable for easier commands:
```powershell
# Replace with your actual Project ID (e.g., ims-backend-486812)
$PROJECT_ID="your-project-id-here"
gcloud config set project $PROJECT_ID
```

Enable necessary services:
```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## 2. Deploy Backend (Step 1)

We deploy the backend first to get its URL.

```powershell
cd Backend

# Submit build to Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/pse-backend .

# Deploy to Cloud Run
# Note: REPLACE [YOUR_GEMINI_KEY]
gcloud run deploy pse-backend `
  --image gcr.io/$PROJECT_ID/pse-backend `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars "GEMINI_API_KEY=[YOUR_GEMINI_KEY],ENV=production,FRONTEND_URL=*"
```

**Copy the Backend URL** from the output (e.g., `https://pse-backend-xyz.a.run.app`).

## 3. Deploy Frontend

Now we build the frontend, "baking in" the Backend URL.

```powershell
cd ../Frontend

# Replace [BACKEND_URL] with the URL you just copied
$BACKEND_URL="https://pse-backend-xyz.a.run.app"

# Submit build (passing the backend URL as a build argument)
gcloud builds submit --tag gcr.io/$PROJECT_ID/pse-frontend `
  --substitutions=_VITE_API_BASE_URL=$BACKEND_URL .

# Note: If the above command fails with substitution errors, create a cloudbuild.yaml or use Docker to build and push manually.
# Alternative (using Docker):
# docker build -t gcr.io/$PROJECT_ID/pse-frontend --build-arg VITE_API_BASE_URL=$BACKEND_URL .
# docker push gcr.io/$PROJECT_ID/pse-frontend

# Deploy Frontend
gcloud run deploy pse-frontend `
  --image gcr.io/$PROJECT_ID/pse-frontend `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated
```

**Copy the Frontend URL** from the output (e.g., `https://pse-frontend-xyz.a.run.app`).

## 4. Secure Backend (Step 2)

Update the backend to only allow requests from your frontend.

```powershell
# Replace [FRONTEND_URL] with your actual frontend URL (no trailing slash)
gcloud run services update pse-backend `
  --region us-central1 `
  --set-env-vars "FRONTEND_URL=https://pse-frontend-xyz.a.run.app"
```

## 5. Verification
1.  Open your **Frontend URL**.
2.  Try a search.
3.  If you see "Network Error", check the console logs and ensure the Backend URL is correct.

## Troubleshooting
-   **Build Failures**: Ensure `cloudbuild.googleapis.com` is enabled.
-   **503 Errors**: Check `gcloud run services logs read pse-backend`.
