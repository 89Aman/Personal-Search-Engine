# 🚀 Knowledge Vault: GCP Deployment Guide

Follow these steps in your terminal to deploy your private semantic search engine to Google Cloud.

## 0. Prerequisites
- **GCP Project**: Create a project in the [GCP Console](https://console.cloud.google.com/).
- **API Key**: Have your `GEMINI_API_KEY` ready.
- **gcloud CLI**: Ensure you have the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed.

---

## 1. Initial Setup
Run these once to prepare your environment:
```powershell
# Login to GCP
gcloud auth login

# Set your project ID
gcloud config set project [YOUR_PROJECT_ID]

# Enable required APIs
gcloud services enable run.googleapis.com `
                       storage.googleapis.com `
                       artifactregistry.googleapis.com `
                       cloudbuild.googleapis.com
```

---

## 2. Storage Persistence (FUSE)
Create the bucket that will store your PDFs and the ChromaDB index:
```powershell
# Create bucket (Replace [REGION] with e.g., us-central1)
gcloud storage buckets create gs://gen-lang-client-0055040611-vault-storage --location=asia-south1
```

---

## 3. Backend Deployment
Navigate to the `Backend` folder and deploy:
```powershell
cd Backend

gcloud run deploy vault-backend --source . `
  --region=asia-south1 `
  --allow-unauthenticated `
  --memory=1GiB `
  --cpu=1 `
  --add-volume="name=vault-data,type=cloud-storage,bucket=gen-lang-client-0055040611-vault-storage" `
  --add-volume-mount="volume=vault-data,mount-path=/app/chroma_db" `
  --set-env-vars="GEMINI_API_KEY=AIzaSyDO2BCDEEIP-6QR5YTvRKyLTp1BBhR906w,ENV=production"
```
*Note: Copy the **Service URL** output at the end of this command.*

---

## 4. Frontend Deployment
Navigate to any folder and deploy the `Frontend`:
```powershell
cd ../Frontend

gcloud run deploy vault-frontend --source . `
  --region=[REGION] `
  --allow-unauthenticated `
  --set-build-env-vars="VITE_API_BASE_URL=[YOUR_BACKEND_URL]"
```

---

## 5. Final Connection
Once both are deployed, update the Backend `FRONTEND_URL` to allow CORS:
```powershell
gcloud run services update vault-backend `
  --region=[REGION] `
  --set-env-vars="FRONTEND_URL=[YOUR_FRONTEND_URL]"
```

---
**Done!** Your Personal Search Engine is now live and persistent.
