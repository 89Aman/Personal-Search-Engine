# 💨 Knowledge Vault: Azure Deployment Guide

This guide describes how to deploy your Private Semantic Search Engine to **Azure Container Apps** using **Azure Files** for persistent storage.

## 0. Prerequisites
- **Azure CLI**: [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows) if you haven't already.
- **Azure Subscription**: Ensure you have an active subscription.
- **Gemini API Key**: Your `GEMINI_API_KEY`.

---

## 1. Initial Setup
Run these in your terminal (PowerShell):

```powershell
# Login to Azure
az login

# Create a Resource Group (Done)
# az group create --name education --location eastus2

# Create an Azure Container Registry (ACR) (Done)
# az acr create --resource-group education --name vaultregistryshasari --sku Basic --admin-enabled true
```
*Note: Your ACR name is **vaultregistryshasari**.*

---

## 2. Persistent Storage (Azure Files)
Unlike GCP's FUSE, Azure Container Apps uses Azure Files for persistence.

```powershell
# Create Storage Account (Done)
# az storage account create --name vaultstorageshasari --resource-group education --location eastus2 --sku Standard_LRS

# Create a File Share for ChromaDB (Done)
# az storage share create --name vault-share --account-name vaultstorageshasari
```

---

## 3. Backend Deployment
We will build the container in the cloud using ACR and then deploy to Container Apps.

```powershell
cd Backend

# 1. Build and Push to Registry (In Progress)
az acr build --registry vaultregistryshasari --image vault-backend:latest .

# 2. Create Container App Environment
az containerapp env create --name vault-env --resource-group education --location eastus2

# 3. Create Backend Container App with Volume Mount
az containerapp create --name vault-backend --resource-group education --environment vault-env `
  --image vaultregistryshasari.azurecr.io/vault-backend:latest `
  --target-port 8080 --ingress external `
  --min-replicas 1 --max-replicas 1 `
  --cpu 1.0 --memory 2.0Gi `
  --env-vars GEMINI_API_KEY=[YOUR_GEMINI_KEY] ENV=production `
  --storage-name vault-data `
  --mount-path /app/chroma_db
```
*Note: Volume configuration in Azure often requires a JSON or YAML for complex mounts. We can refine this if the simple CLI command needs more detail.*

---

## 4. Frontend Deployment
```powershell
cd ../Frontend

# 1. Build and Push
az acr build --registry vaultregistryshasari --image vault-frontend:latest .

# 2. Deploy
az containerapp create --name vault-frontend --resource-group education --environment vault-env `
  --image vaultregistryshasari.azurecr.io/vault-frontend:latest `
  --target-port 80 --ingress external `
  --env-vars VITE_API_BASE_URL=[YOUR_BACKEND_URL]
```

---

## 5. Final Connection
Update the Backend's `FRONTEND_URL` for CORS:

```powershell
az containerapp update --name vault-backend --resource-group vault-rg `
  --set-env-vars FRONTEND_URL=[YOUR_FRONTEND_URL]
```

---
**Done!** Your Personal Search Engine is now running on Azure.
