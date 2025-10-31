#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USE_TERRAFORM=${USE_TERRAFORM:-true}
SKIP_BUILD=${SKIP_BUILD:-false}
MONITORING_NAMESPACE="monitoring"
DEFAULT_NAMESPACE="default"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-flight checks
preflight_checks() {
    print_header "Running Pre-flight Checks"

    local missing_tools=()

    # Check required tools
    for tool in minikube kubectl docker helm terraform; do
        if ! command_exists "$tool"; then
            missing_tools+=("$tool")
            print_error "$tool is not installed"
        else
            print_success "$tool is installed"
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Run: ./utils/setup/setup-tools-bash.sh to install missing tools"
        exit 1
    fi

    # Check if running as root (for WSL2)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Minikube will use --force flag"
        MINIKUBE_FORCE="--force"
    else
        MINIKUBE_FORCE=""
    fi
}

# Start Minikube
start_minikube() {
    print_header "Starting Minikube Cluster"

    # Check if Minikube is already running
    if minikube status &>/dev/null; then
        print_info "Minikube is already running"
        minikube status
    else
        print_info "Starting Minikube with Docker driver..."
        minikube start --driver=docker $MINIKUBE_FORCE --memory=4096 --cpus=2
        print_success "Minikube started successfully"
    fi

    # Point Docker to Minikube's Docker daemon
    print_info "Configuring Docker environment..."
    eval $(minikube docker-env)
    print_success "Docker environment configured"
}

# Build Docker images
build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        print_warning "Skipping Docker image builds (SKIP_BUILD=true)"
        return
    fi

    print_header "Building Docker Images"

    # Ensure we're using Minikube's Docker daemon
    eval $(minikube docker-env)

    print_info "Building backend service..."
    cd "$SCRIPT_DIR/app/backend"
    docker build -t backend-service:latest . -q
    print_success "Backend image built"

    print_info "Building frontend service..."
    cd "$SCRIPT_DIR/app/frontend"
    docker build -t frontend-service:latest . -q
    print_success "Frontend image built"

    cd "$SCRIPT_DIR"
}

# Deploy using Terraform (recommended)
deploy_with_terraform() {
    print_header "Deploying with Terraform"

    cd "$SCRIPT_DIR/terraform"

    # Initialize Terraform if needed
    if [ ! -d ".terraform" ]; then
        print_info "Initializing Terraform..."
        terraform init
    fi

    # Apply Terraform configuration
    print_info "Applying Terraform configuration..."
    terraform apply -auto-approve

    print_success "Terraform deployment completed"

    cd "$SCRIPT_DIR"
}

# Deploy manually (alternative method)
deploy_manually() {
    print_header "Deploying Manually"

    # Create namespaces
    print_info "Creating namespaces..."
    kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

    # Deploy applications
    print_info "Deploying backend service..."
    kubectl apply -f "$SCRIPT_DIR/app/backend/backend-deployment.yaml"
    kubectl apply -f "$SCRIPT_DIR/app/backend/backend-service.yaml"

    print_info "Deploying frontend service..."
    kubectl apply -f "$SCRIPT_DIR/app/frontend/frontend-deployment.yaml"
    kubectl apply -f "$SCRIPT_DIR/app/frontend/frontend-service.yaml"

    # Add Helm repositories
    print_info "Adding Helm repositories..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
    helm repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
    helm repo update

    # Install monitoring stack
    print_info "Installing Prometheus..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace $MONITORING_NAMESPACE \
        --create-namespace \
        --wait \
        --timeout 5m

    print_info "Installing Loki..."
    helm upgrade --install loki grafana/loki \
        --namespace $MONITORING_NAMESPACE \
        --wait \
        --timeout 5m

    print_info "Installing Jaeger..."
    kubectl apply -f "$SCRIPT_DIR/observability/jaeger/jaeger-deployment.yaml"

    print_success "Manual deployment completed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    print_header "Waiting for Deployments"

    print_info "Waiting for application pods..."
    kubectl wait --for=condition=ready pod -l app=backend -n $DEFAULT_NAMESPACE --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=frontend -n $DEFAULT_NAMESPACE --timeout=300s || true

    print_info "Waiting for monitoring pods..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n $MONITORING_NAMESPACE --timeout=300s || true

    print_success "All deployments are ready"
}

# Display access information
show_access_info() {
    print_header "Service Access Information"

    print_info "Getting service URLs..."
    echo ""

    # Frontend
    echo -e "${BLUE}Frontend Application:${NC}"
    echo "  minikube service frontend-service --url -n $DEFAULT_NAMESPACE"
    echo ""

    # Grafana
    echo -e "${BLUE}Grafana Dashboard:${NC}"
    echo "  kubectl port-forward -n $MONITORING_NAMESPACE svc/grafana 3000:80"
    echo "  Then visit: http://localhost:3000"
    echo "  Credentials: admin / prom-operator"
    echo ""

    # Prometheus
    echo -e "${BLUE}Prometheus:${NC}"
    echo "  kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-operator-kube-p-prometheus 9090:9090"
    echo "  Then visit: http://localhost:9090"
    echo ""

    # Jaeger
    echo -e "${BLUE}Jaeger Tracing:${NC}"
    echo "  kubectl port-forward -n $MONITORING_NAMESPACE svc/jaeger 16686:16686"
    echo "  Then visit: http://localhost:16686"
    echo ""

    # Quick commands
    echo -e "${BLUE}Quick Commands:${NC}"
    echo "  Open all services:  ./utils/demo.sh"
    echo "  Run load test:      node utils/load-test.js \$(minikube service frontend-service --url -n $DEFAULT_NAMESPACE)"
    echo "  View logs:          kubectl logs -f deployment/backend-deployment -n $DEFAULT_NAMESPACE"
    echo "  Check status:       kubectl get pods -A"
    echo ""
}

# Main deployment logic
main() {
    print_header "Microservice Monitoring - Local Server Startup"

    # Run pre-flight checks
    preflight_checks

    # Start Minikube
    start_minikube

    # Build images
    build_images

    # Deploy services
    if [ "$USE_TERRAFORM" = true ]; then
        deploy_with_terraform
    else
        deploy_manually
    fi

    # Wait for everything to be ready
    wait_for_deployments

    # Show access information
    show_access_info

    print_success "Local server is ready!"
    print_info "To stop: minikube stop"
    print_info "To clean up: ./utils/cleanup.sh"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-terraform)
            USE_TERRAFORM=false
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-terraform    Use manual Kubernetes deployment instead of Terraform"
            echo "  --skip-build      Skip Docker image builds (use existing images)"
            echo "  --help            Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  USE_TERRAFORM     Set to 'false' to disable Terraform (default: true)"
            echo "  SKIP_BUILD        Set to 'true' to skip Docker builds (default: false)"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
