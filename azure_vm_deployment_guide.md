# ☁️ Azure VM Deployment Guide

This guide details how to deploy your Personal Search Engine to an Azure Virtual Machine (Ubuntu) using Docker Compose.

## 0. Prerequisites
1.  **Azure VM**: An Ubuntu 20.04 or 22.04 LTS VM running on Azure.
2.  **SSH Access**: You must be able to SSH into your VM.
3.  **Open Ports**: Ensure your VM's "Networking" settings (Network Security Group) allow **Inbound** traffic on:
    *   Port `80` (HTTP)
    *   Port `8080` (Backend API)
    *   Port `22` (SSH)

## 1. Connect to your VM
Open your terminal (PowerShell or Bash) and SSH into your VM:
```bash
ssh -i <path_to_your_key.pem> azureuser@<VM_PUBLIC_IP>
```

## 2. Install Docker & Docker Compose
Run the following commands on your VM to install Docker:
```bash
# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo apt-get install -y docker-compose

# Add your user to the docker group (to run without sudo)
sudo usermod -aG docker $USER
# You might need to logout and log back in for this to take effect, 
# or run: newgrp docker
```

## 3. Transfer Your Code
You can transfer your code to the VM using `scp` (from your local machine) or `git`.

### Option A: Using Git (Recommended)
If your code is on GitHub:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### Option B: Using SCP (Copy from Local)
Run this from your **local machine** (not inside the VM):
```powershell
# Make sure you are in the project root folder
scp -r -i <path_to_key.pem> . azureuser@<VM_PUBLIC_IP>:~/app
```

## 4. Configuration
Create a `.env` file in the project root on the VM:
```bash
nano .env
```

Paste the following configuration (Right-click to paste in SSH):
```ini
# --- AI Configuration ---
GEMINI_API_KEY=your_actual_gemini_api_key_here

# --- Network Configuration ---
# Your VM's Public IP
VITE_API_BASE_URL=http://172.206.114.250:8080

FRONTEND_URL=http://172.206.114.250
```
*Press `Ctrl+X`, then `Y`, then `Enter` to save and exit.*

## 5. Build and Run
Now, build the Docker images and start the services:

```bash
# Build and start in detached mode (background)
docker-compose up --build -d
```

## 6. Verify Deployment
1.  **Frontend**: Open your browser and visit `http://<VM_PUBLIC_IP>`. You should see the search interface.
2.  **Backend**: Visit `http://<VM_PUBLIC_IP>:8080/health` or `http://<VM_PUBLIC_IP>:8080/docs` to check the API.

## 7. Troubleshooting
- **Permission Denied**: If you get Docker permission errors, run `sudo docker-compose up ...` or ensure you ran the `usermod` command in Step 2.
- **Site Unreachable**: Double-check your Azure **Network Security Group (NSG)** rules. Ports 80 and 8080 MUST be allowed.
- **Build Fails**: Ensure you have enough RAM on the VM (at least 2GB is recommended for building). If the build crashes, you might need to enable a swap file.
