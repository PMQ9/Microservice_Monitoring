.PHONY: help start stop restart build deploy clean status logs test demo install

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Microservice Monitoring - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make start          # Start everything"
	@echo "  make status         # Check service status"
	@echo "  make logs           # View backend logs"
	@echo "  make test           # Run load tests"
	@echo "  make stop           # Stop Minikube"
	@echo ""

install: ## Install required tools (kubectl, helm, minikube, docker)
	@echo "$(GREEN)Installing required tools...$(NC)"
	@chmod +x utils/setup/setup-tools-bash.sh
	@./utils/setup/setup-tools-bash.sh

start: ## Start local server (Minikube + all services)
	@echo "$(GREEN)Starting local server...$(NC)"
	@chmod +x start-local.sh
	@./start-local.sh

start-manual: ## Start local server without Terraform
	@echo "$(GREEN)Starting local server (manual deployment)...$(NC)"
	@chmod +x start-local.sh
	@./start-local.sh --no-terraform

stop: ## Stop Minikube cluster
	@echo "$(YELLOW)Stopping Minikube...$(NC)"
	@minikube stop
	@echo "$(GREEN)Minikube stopped$(NC)"

restart: stop start ## Restart local server

build: ## Build Docker images only
	@echo "$(GREEN)Building Docker images...$(NC)"
	@eval $$(minikube docker-env) && \
		cd app/backend && docker build -t backend-service:latest . && \
		cd ../frontend && docker build -t frontend-service:latest .
	@echo "$(GREEN)Images built successfully$(NC)"

deploy: ## Deploy services (assumes images are built)
	@echo "$(GREEN)Deploying services...$(NC)"
	@chmod +x start-local.sh
	@SKIP_BUILD=true ./start-local.sh

clean: ## Clean up all resources and delete Minikube
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@chmod +x utils/cleanup.sh
	@./utils/cleanup.sh || true
	@echo "$(GREEN)Cleanup complete$(NC)"

status: ## Show status of all services
	@echo "$(BLUE)Minikube Status:$(NC)"
	@minikube status || echo "Minikube is not running"
	@echo ""
	@echo "$(BLUE)Application Pods:$(NC)"
	@kubectl get pods -n default || echo "No application pods found"
	@echo ""
	@echo "$(BLUE)Application Services:$(NC)"
	@kubectl get svc -n default || echo "No application services found"
	@echo ""
	@echo "$(BLUE)Monitoring Pods:$(NC)"
	@kubectl get pods -n monitoring || echo "No monitoring pods found"
	@echo ""
	@echo "$(BLUE)All Pods:$(NC)"
	@kubectl get pods -A || echo "Cannot connect to cluster"

logs: ## View backend service logs
	@echo "$(BLUE)Backend logs (Ctrl+C to exit):$(NC)"
	@kubectl logs -f deployment/backend-deployment -n default

logs-frontend: ## View frontend service logs
	@echo "$(BLUE)Frontend logs (Ctrl+C to exit):$(NC)"
	@kubectl logs -f deployment/frontend-deployment -n default

logs-all: ## View all application logs
	@echo "$(BLUE)All application logs:$(NC)"
	@kubectl logs -l app=backend -n default --tail=50
	@kubectl logs -l app=frontend -n default --tail=50

test: ## Run load test against frontend
	@echo "$(GREEN)Running load test...$(NC)"
	@chmod +x utils/test.sh
	@./utils/test.sh

demo: ## Open all UIs (Grafana, Jaeger, Frontend, etc.)
	@echo "$(GREEN)Opening demo UIs...$(NC)"
	@chmod +x utils/demo.sh
	@./utils/demo.sh

open-frontend: ## Open frontend service in browser
	@echo "$(BLUE)Opening frontend...$(NC)"
	@minikube service frontend-service -n default

open-grafana: ## Open Grafana dashboard
	@echo "$(BLUE)Opening Grafana...$(NC)"
	@echo "Default credentials: admin / prom-operator"
	@kubectl port-forward -n monitoring svc/grafana 3000:80

open-prometheus: ## Open Prometheus UI
	@echo "$(BLUE)Opening Prometheus...$(NC)"
	@kubectl port-forward -n monitoring svc/prometheus-operator-kube-p-prometheus 9090:9090

open-jaeger: ## Open Jaeger tracing UI
	@echo "$(BLUE)Opening Jaeger...$(NC)"
	@kubectl port-forward -n monitoring svc/jaeger 16686:16686

shell-backend: ## Open shell in backend pod
	@kubectl exec -it deployment/backend-deployment -n default -- /bin/sh

shell-frontend: ## Open shell in frontend pod
	@kubectl exec -it deployment/frontend-deployment -n default -- /bin/sh

describe-backend: ## Describe backend deployment
	@kubectl describe deployment backend-deployment -n default

describe-frontend: ## Describe frontend deployment
	@kubectl describe deployment frontend-deployment -n default

terraform-init: ## Initialize Terraform
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	@cd terraform && terraform init

terraform-plan: ## Show Terraform plan
	@echo "$(BLUE)Terraform plan:$(NC)"
	@cd terraform && terraform plan

terraform-apply: ## Apply Terraform configuration
	@echo "$(GREEN)Applying Terraform...$(NC)"
	@cd terraform && terraform apply

terraform-destroy: ## Destroy Terraform resources
	@echo "$(YELLOW)Destroying Terraform resources...$(NC)"
	@cd terraform && terraform destroy

port-forward-all: ## Port forward all services to localhost
	@echo "$(GREEN)Port forwarding all services...$(NC)"
	@echo "Starting port forwards in background..."
	@kubectl port-forward -n monitoring svc/grafana 3000:80 &
	@kubectl port-forward -n monitoring svc/prometheus-operator-kube-p-prometheus 9090:9090 &
	@kubectl port-forward -n monitoring svc/jaeger 16686:16686 &
	@kubectl port-forward -n default svc/frontend-service 5000:5000 &
	@echo "$(GREEN)Services available at:$(NC)"
	@echo "  Frontend:   http://localhost:5000"
	@echo "  Grafana:    http://localhost:3000 (admin/prom-operator)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Jaeger:     http://localhost:16686"
	@echo ""
	@echo "$(YELLOW)To stop port forwards: killall kubectl$(NC)"

check: ## Check if all prerequisites are installed
	@echo "$(BLUE)Checking prerequisites...$(NC)"
	@command -v minikube >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) minikube" || echo "$(YELLOW)✗$(NC) minikube"
	@command -v kubectl >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) kubectl" || echo "$(YELLOW)✗$(NC) kubectl"
	@command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) docker" || echo "$(YELLOW)✗$(NC) docker"
	@command -v helm >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) helm" || echo "$(YELLOW)✗$(NC) helm"
	@command -v terraform >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) terraform" || echo "$(YELLOW)✗$(NC) terraform"
	@command -v node >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) node" || echo "$(YELLOW)✗$(NC) node (optional, for load tests)"
