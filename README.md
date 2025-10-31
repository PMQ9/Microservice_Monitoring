# Microservice Monitoring

Enterprise-grade monitoring platform for Kubernetes microservices with complete observability, infrastructure automation, and security hardening.

![alt text](doc/live-metric-grafana-dashboard-prometheus.png)

## Overview

Production-ready monitoring solution demonstrating enterprise architecture:

- Applications: Flask-based frontend and backend microservices
- Observability: Prometheus metrics, Jaeger tracing, Loki logs, Grafana dashboards
- Infrastructure: Kubernetes orchestration with Minikube for local development
- Automation: Terraform IaC, Helm package management, GitHub Actions CI/CD
- Security: RBAC, network policies, secrets management, security scanning
- Reliability: Auto-scaling (HPA), disruption budgets (PDB), resource management
- GitOps: ArgoCD declarative deployments

## Architecture Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | Kubernetes | Container and microservice management |
| Metrics | Prometheus | Time-series metrics collection and querying |
| Tracing | Jaeger | Distributed request tracing |
| Logs | Loki | Log aggregation and analysis |
| Visualization | Grafana | Unified dashboard for metrics, logs, traces |
| Instrumentation | OpenTelemetry | Automatic metrics and trace collection |
| IaC | Terraform | Complete infrastructure automation |
| CI/CD | GitHub Actions | Automated testing, building, deployment |
| GitOps | ArgoCD | Declarative version-controlled deployments |

## Quick Start

### One-Command Setup

```bash
# Install prerequisites (first time only)
make install

# Start everything (Minikube + all services)
make start
```

Script will:
- Start Minikube
- Build Docker images
- Deploy all services with Terraform
- Set up monitoring stack (Prometheus, Grafana, Jaeger, Loki)
- Show all UIs

### Alternative Methods

Manual script execution:
```bash
./start-local.sh
```

Traditional Terraform deployment:
```bash
minikube start --driver=docker --force
eval $(minikube docker-env)

cd terraform
terraform init
terraform apply
```

Manual Kubernetes deployment:
```bash
kubectl apply -f k8s-security/
kubectl apply -f k8s-reliability/
kubectl apply -f app/

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -n monitoring
helm install grafana grafana/grafana -n monitoring
helm install loki grafana/loki -n monitoring
helm install jaeger bitnami/jaeger -n monitoring
```

GitOps deployment with ArgoCD:
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f gitops/argocd-install/
kubectl apply -f gitops/applications/
```

## Key Features

Infrastructure Automation: Terraform IaC with parameterized configuration

Enterprise Security: RBAC, zero-trust network policies, secrets management, container scanning

High Availability: HPA auto-scaling, PDB disruption protection, resource quotas

CI/CD Pipeline: Automated testing, building, security scanning, deployment via GitHub Actions

Production Manifests: Enhanced deployments with health probes, resource limits, pod affinity

Complete Documentation: Enterprise deployment guide, DevOps handbook, security procedures

## Project Structure

```
terraform/                    Infrastructure-as-Code automation
.github/workflows/            CI/CD pipelines (build-and-deploy, security)
k8s-security/                 RBAC, network policies, secrets templates
k8s-reliability/              HPA, PDB, resource quotas
k8s-enhanced/                 Production deployment manifests
app/                          Frontend and backend services
observability/                Prometheus, Jaeger, Loki, Grafana configs
gitops/                       ArgoCD installation and applications
docs/                         Enterprise deployment and operations guides
```

## Essential Commands

### Simplified Commands (using Makefile)

```bash
make start              # Start everything
make status             # Check service status
make logs               # View backend logs
make test               # Run load tests
make demo               # Open all UIs
make stop               # Stop Minikube
make clean              # Complete cleanup
make help               # Show all available commands
```

### Port Forwarding to Localhost

```bash
make port-forward-all   # Forward all services to localhost

# Or individually:
make open-grafana       # http://localhost:3000 (admin/prom-operator)
make open-prometheus    # http://localhost:9090
make open-jaeger        # http://localhost:16686
make open-frontend      # Frontend service
```

### Traditional Kubernetes Commands

Local development:
```bash
minikube start --driver=docker --force
eval $(minikube docker-env)
cd app/backend && docker build -t backend-service:latest . && cd ../..
cd app/frontend && docker build -t frontend-service:latest . && cd ../..
kubectl apply -f app/backend/backend-deployment.yaml app/backend/backend-service.yaml
kubectl apply -f app/frontend/frontend-deployment.yaml app/frontend/frontend-service.yaml
kubectl get pods -n default
```

Kubernetes operations:
```bash
kubectl get pods -A
kubectl get svc -A
kubectl top nodes
kubectl logs -f deployment/backend -n default
```

## Technology Stack

Kubernetes 1.28+, Docker, Minikube

Monitoring: Prometheus, Jaeger, Loki, Grafana, OpenTelemetry

Infrastructure: Terraform, Helm, ArgoCD

CI/CD: GitHub Actions, Trivy, Bandit, TruffleHog

Security: RBAC, Network Policies, Kubernetes Secrets

Application: Python 3.9 Flask

## Environment Requirements

OS: Linux, macOS, Windows WSL2
Kubernetes: 1.28+ (Minikube 1.33+ for local)
Container Runtime: Docker 20+
Tools: kubectl, helm 3+, terraform 1.0+, git
Resources: 4GB+ RAM minimum (8GB+ recommended)

## Security

RBAC enforces least-privilege access. Network policies implement zero-trust networking. Kubernetes secrets with encryption at rest. Container images scanned for vulnerabilities. Dependencies checked for known issues. Pre-commit hooks prevent credential commits.

## Documentation


## Support

