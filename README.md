# Microservice_Monitoring

Full-stack monitoring platform to surveil microservices, alerts and debug issues, auto-scales and deploy via GitOps/ArgoCD

## What this does

Deploy a sample microservices application on Minikube
Tracks, visualizes, and alerts on the health of the microservices using Prometheus, OTel, Jaeger, Loki, Grafana

## Environment Setup

This project runs in WSL2 on Windows, with Minikube for Kubernetes and Docker Desktop for containerization.

**Step 1: Step up WSL2**

1. Setup WSL2:
    - Install WSL2: `wsl --install -d Ubuntu`
    - Start WSL2 in PowerShell/Command Prompt
    - Update Ubuntu: `sudo apt update && sudo apt upgrade -y`

***Option 1: Setup with `asdf`***

2. Run the automated setup script to download and the necessary tools in WSL2:
    - `chmod +x utils/setup/setup-tools-asdf.sh`
    - `./utils/setup/setup-tools-asdf.sh`

***Option 2: Setup with Bash Shell script***

2. Run the automated setup script to download and the necessary tools in WSL2:
    - `chmod +x utils/setup/setup-tools-bash.sh`
    - `./utils/setup/setup-tools-bash.sh`

3. Install Docker on Windows manually and enable WSL2 integration
    - Settings > Resources > WSL Integration > Enable your Ubuntu.
    - Verify in Ubuntu 
        - `docker --version`
        - `kubectl version --client`
        - `helm version`
        - `minikube version`
        - `docker --version`
        - `git --version`.

4. Start MiniKube in WSL2
    - `minikube start --driver=docker`

**Step 2: Deploy Microservice Apps**

1. Ensure Minikube is running and point Docker to MiniKube Daemon:
    - `minikube start --driver=docker`
    - `eval $(minikube docker-env)`
2. Build Backend Image
    - `cd ~/Microservice_Monitoring/app/backend`
    - `docker build -t backend-service:latest .`
3. Build Frontend Image
    - `cd ~/Microservice_Monitoring/app/frontend`
    - `docker build -t frontend-service:latest .`
4. Verify Image
    - `docker images | grep -E 'backend-service|frontend-service'`
5. Apply Manifest
    - Deploy Backend:
        - `kubectl apply -f app/backend/backend-deployment.yaml`
        - `kubectl apply -f app/backend/backend-service.yaml`
    - Deploy Frontend:
        - `kubectl apply -f app/backend/frontend-deployment.yaml`
        - `kubectl apply -f app/backend/frontend-service.yaml`
6. Verify Deployment:
    - `kubectl get pods -n default`
7. Access Frontend from Windows:
    - Get Frontend URL: `minikube service frontend-service --url -n default`
        - It should say: `http://192.168.49.2:30001`, access from Windows browser
*Explanation: This is a simple microservices app with a frontend calling a backend API, running in Kubernetes*
8. To view Kubernetes clusters:
    - `kubectl get pods` `kubectl get svc`
    - `minikube dashboard`
    

## Key Features

- Metric Collection (Prometheus) 
- Distributed Tracing (Jaeger)
- Log Aggregation (Loki + Grafana)
