#!/bin/bash
set -e

# Purpose: Demo script for Microservice Monitoring project
# Usage: Run in WSL2 Ubuntu terminal

echo "Starting Minikube..."
minikube start --driver=docker

echo "Verifying microservices..."
kubectl get pods -n default
kubectl get svc -n default
echo "Opening frontend in browser..."
minikube service frontend-service --url -n default &

echo "Verifying monitoring stack..."
kubectl get pods -n monitoring
echo "Opening Grafana in browser..."
minikube service grafana -n monitoring --url &
echo "Opening Jaeger in browser..."
minikube service jaeger -n monitoring --url &

echo "Verifying ArgoCD..."
kubectl get pods -n argocd
echo "Opening ArgoCD UI..."
minikube service argocd-server -n argocd --url &
echo "ArgoCD password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

echo "Opening Kubernetes dashboard..."
minikube dashboard &

echo "Demo ready! Check your Windows browser for UIs."
echo "Generate traffic: curl \$(minikube service frontend-service --url -n default)"
echo "Check Grafana (admin/admin) and Jaeger for metrics/logs/traces."