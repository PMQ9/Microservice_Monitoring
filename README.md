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

Prerequisites: Kubernetes cluster, Docker, Terraform, kubectl, helm, git

Terraform deployment (recommended):
```bash
cd terraform
terraform init
cp terraform.tfvars.example terraform.tfvars
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

Local development:
```bash
minikube start --driver=docker
eval $(minikube docker-env)
docker build -t backend-service:latest app/backend/
docker build -t frontend-service:latest app/frontend/
kubectl apply -f app/
minikube service frontend-service --url -n default
```

Monitoring access:
```bash
kubectl port-forward svc/grafana 3000:80 -n monitoring
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
kubectl port-forward svc/jaeger 16686:16686 -n monitoring
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

