#!/bin/bash

# Social Media Platform Deployment Script
# This script deploys the social media microservices platform with monitoring

set -e

echo "=========================================="
echo "Social Media Platform Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if minikube is running
print_info "Checking Minikube status..."
if ! minikube status &> /dev/null; then
    print_warning "Minikube is not running. Starting Minikube..."
    minikube start --driver=docker --force
else
    print_info "Minikube is already running"
fi

# Point Docker to Minikube's Docker daemon
print_info "Setting Docker environment to use Minikube..."
eval $(minikube docker-env)

# Build Docker images
print_info "Building Docker images..."

print_info "Building Content Creator Service..."
cd app/content-creator
docker build -t content-creator-service:latest .
cd ../..

print_info "Building User Service..."
cd app/user-service
docker build -t user-service:latest .
cd ../..

print_info "Building Content Service..."
cd app/content-service
docker build -t content-service:latest .
cd ../..

print_info "All Docker images built successfully!"

# Create monitoring namespace if it doesn't exist
print_info "Setting up Kubernetes namespaces..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy monitoring stack (if not already deployed)
print_info "Checking monitoring stack..."

if ! helm list -n monitoring | grep -q prometheus; then
    print_info "Installing Prometheus..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
else
    print_info "Prometheus is already installed"
fi

if ! kubectl get deployment jaeger -n monitoring &> /dev/null; then
    print_info "Installing Jaeger..."
    kubectl apply -f observability/jaeger/jaeger-deployment.yaml
else
    print_info "Jaeger is already deployed"
fi

if ! helm list -n monitoring | grep -q loki; then
    print_info "Installing Loki..."
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    helm install loki grafana/loki -n monitoring -f observability/loki/values.yaml
else
    print_info "Loki is already installed"
fi

if ! helm list -n monitoring | grep -q grafana; then
    print_info "Installing Grafana..."
    helm install grafana grafana/grafana -n monitoring -f observability/grafana/values.yaml
else
    print_info "Grafana is already installed"
fi

# Deploy ServiceMonitors
print_info "Deploying ServiceMonitors..."
kubectl apply -f observability/prometheus/service-monitor.yaml

# Deploy social media microservices
print_info "Deploying Social Media Microservices..."

print_info "Deploying Content Creator Service..."
kubectl apply -f app/content-creator/content-creator-deployment.yaml
kubectl apply -f app/content-creator/content-creator-service.yaml

print_info "Deploying User Service..."
kubectl apply -f app/user-service/user-service-deployment.yaml
kubectl apply -f app/user-service/user-service-service.yaml

print_info "Deploying Content Service..."
kubectl apply -f app/content-service/content-service-deployment.yaml
kubectl apply -f app/content-service/content-service-service.yaml

# Wait for deployments to be ready
print_info "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/content-creator -n default
kubectl wait --for=condition=available --timeout=120s deployment/user-service -n default
kubectl wait --for=condition=available --timeout=120s deployment/content-service -n default

print_info "Waiting for monitoring stack to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/prometheus-kube-prometheus-operator -n monitoring || true
kubectl wait --for=condition=available --timeout=120s deployment/jaeger -n monitoring || true

echo ""
print_info "=========================================="
print_info "Deployment Complete!"
print_info "=========================================="
echo ""

# Get service URLs
print_info "Service URLs:"
echo ""

CONTENT_SERVICE_URL=$(minikube service content-service --url -n default)
print_info "Content Service (Traffic Generator): $CONTENT_SERVICE_URL"

print_info "Grafana: Run 'minikube service grafana -n monitoring --url'"
GRAFANA_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
print_info "Grafana admin password: $GRAFANA_PASSWORD"

print_info "Jaeger UI: Run 'minikube service jaeger -n monitoring --url'"

print_info "Prometheus: Run 'kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090'"

echo ""
print_info "=========================================="
print_info "Quick Start Commands"
print_info "=========================================="
echo ""
print_info "1. Start traffic simulation:"
echo "   curl -X POST $CONTENT_SERVICE_URL/api/simulation/start"
echo ""
print_info "2. Check simulation status:"
echo "   curl $CONTENT_SERVICE_URL/api/simulation/status"
echo ""
print_info "3. View platform statistics:"
echo "   curl $CONTENT_SERVICE_URL/api/platform/stats"
echo ""
print_info "4. Stop simulation:"
echo "   curl -X POST $CONTENT_SERVICE_URL/api/simulation/stop"
echo ""
print_info "5. Access Grafana dashboards:"
echo "   minikube service grafana -n monitoring"
echo "   Username: admin"
echo "   Password: $GRAFANA_PASSWORD"
echo ""
print_info "Import the following dashboards in Grafana:"
print_info "  - observability/grafana/dashboards/content-creators-dashboard.json"
print_info "  - observability/grafana/dashboards/users-dashboard.json"
echo ""
print_info "=========================================="

# Check pod status
print_info "Current pod status:"
kubectl get pods -n default
echo ""
kubectl get pods -n monitoring
