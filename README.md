# Microservice_Monitoring

Full-stack monitoring platform to surveil microservices, alerts and debug issues, auto-scales and deploy via GitOps/ArgoCD

## What this does

Deploy a sample microservices application on Minikube
Tracks, visualizes, and alerts on the health of the microservices using Prometheus, OTel, Jaeger, Loki, Grafana

## Environment Setup

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

## Key Features

- Metric Collection (Prometheus) 
- Distributed Tracing (Jaeger)
- Log Aggregation (Loki + Grafana)
