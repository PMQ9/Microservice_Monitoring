#!/bin/bash
set -e

# Purpose: Clean up Minikube and resources for Microservice Monitoring project
# Usage: Run in WSL2 Ubuntu terminal

echo "Deleting microservices..."
kubectl delete -f app/frontend/frontend-deployment.yaml -n default
kubectl delete -f app/frontend/frontend-service.yaml -n default
kubectl delete -f app/backend/backend-deployment.yaml -n default
kubectl delete -f app/backend/backend-service.yaml -n default

echo "Deleting monitoring stack..."
helm uninstall prometheus -n monitoring
helm uninstall loki -n monitoring
helm uninstall grafana -n monitoring
kubectl delete -f observability/jaeger/jaeger-deployment.yaml -n monitoring
kubectl delete -f observability/prometheus/service-monitor.yaml -n monitoring
kubectl delete namespace monitoring

echo "Deleting ArgoCD..."
kubectl delete -f gitops/argocd-install/argocd-install.yaml
kubectl delete namespace argocd

echo "Stopping Minikube..."
minikube stop
minikube delete

echo "Cleanup complete!"