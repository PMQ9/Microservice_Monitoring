#!/bin/bash
set -e

# Purpose: Test Microservice Monitoring project components
# Usage: Run in WSL2 Ubuntu terminal

echo "Testing microservices..."
kubectl get pods -n default
kubectl get svc -n default
FRONTEND_URL=$(minikube service frontend-service --url -n default)
curl -s $FRONTEND_URL | grep "Hello from backend" || { echo "Frontend test failed"; exit 1; }

echo "Testing monitoring stack..."
kubectl get pods -n monitoring
GRAFANA_URL=$(minikube service grafana -n monitoring --url)
JAEGER_URL=$(minikube service jaeger -n monitoring --url)
curl -s $GRAFANA_URL | grep "Grafana" || { echo "Grafana test failed"; exit 1; }
curl -s $JAEGER_URL | grep "Jaeger" || { echo "Jaeger test failed"; exit 1; }

echo "Testing ArgoCD..."
kubectl get applications -n argocd
ARGO_URL=$(minikube service argocd-server -n argocd --url)
curl -s $ARGO_URL | grep "Argo CD" || { echo "ArgoCD test failed"; exit 1; }

echo "All tests passed!"