# Quick Start Guide

## First Time Setup (5 minutes)

### 1. Install Prerequisites
```bash
make install
```

This installs: kubectl, helm, minikube, docker

### 2. Start Everything
```bash
make start
```

This automatically:
- Starts Minikube cluster
- Builds Docker images (backend + frontend)
- Deploys applications
- Installs monitoring stack (Prometheus, Grafana, Jaeger, Loki)
- Waits for all services to be ready
- Shows you access URLs

---

## Access Services

### Option 1: Port Forwarding (Recommended for WSL2)
```bash
make port-forward-all
```

Then open in browser:
- **Frontend App**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/prom-operator)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

Note: Port forwards run in background. To stop: `killall kubectl`

### Option 2: Minikube Service URLs
```bash
make open-frontend      # Opens frontend
make open-grafana       # Opens Grafana
make open-jaeger        # Opens Jaeger
```

---

## Common Commands

```bash
make start              # Start everything
make stop               # Stop Minikube (keeps data)
make restart            # Restart everything
make status             # Check if services are running
make logs               # View backend logs
make test               # Run load test
make clean              # Delete everything and start fresh
make help               # See all commands
```

---

## Generate Test Traffic

```bash
make test
```

Then check:
- **Grafana** for metrics dashboards
- **Jaeger** for distributed traces
- **Prometheus** for raw metrics

---

## Troubleshooting

### Services starting
```bash
make status             # Check pod status
make logs               # Check backend logs
kubectl get pods -A     # See all pods
```

### Rebuild images
```bash
make build              # Rebuild Docker images
make deploy             # Redeploy with new images
```

### Clean
```bash
make clean              # Delete everything
make start              # Start fresh
```

### Check prerequisites
```bash
make check              # Verify all tools are installed
```

---

## Advanced Usage

### Use Manual Deployment (without Terraform)
```bash
./start-local.sh --no-terraform
```

### Skip Image Rebuilds
```bash
./start-local.sh --skip-build
```

### View All Available Options
```bash
./start-local.sh --help
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Minikube Cluster               │
│                                                 │
│  ┌─────────────┐       ┌──────────────┐       │
│  │  Frontend   │──────>│   Backend    │       │
│  │  (Flask)    │       │   (Flask)    │       │
│  └─────────────┘       └──────────────┘       │
│         │                      │               │
│         └──────────┬───────────┘               │
│                    │                           │
│         ┌──────────▼────────────┐             │
│         │  OpenTelemetry         │             │
│         │  (Metrics + Traces)    │             │
│         └────────────────────────┘             │
│                    │                           │
│         ┌──────────┼───────────┐              │
│         │          │           │              │
│    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐         │
│    │Prometheus│ │Jaeger │ │  Loki │          │
│    └────┬───┘ └───┬────┘ └───┬────┘         │
│         │          │           │              │
│         └──────────▼───────────┘              │
│                    │                           │
│              ┌─────▼─────┐                    │
│              │  Grafana  │                    │
│              └───────────┘                    │
└─────────────────────────────────────────────────┘
```

**Services**:
- Frontend: User-facing Flask app
- Backend: API service called by frontend
- Prometheus: Metrics collection
- Grafana: Visualization dashboards
- Jaeger: Distributed tracing
- Loki: Log aggregation

**Observability**:
- All services emit OpenTelemetry metrics and traces
- Prometheus scrapes metrics every 15s
- Jaeger collects distributed traces
- Grafana provides unified view

---

## Workflow

### Starting Work
```bash
make start              # Start the cluster
make status             # Verify everything is running
```

### During Development
```bash
# Make code changes to app/backend/app.py or app/frontend/app.py
make build              # Rebuild images
make deploy             # Deploy changes
make logs               # Check logs
```

### End of Day
```bash
make stop               # Stop cluster (saves resources)
# Or
make clean              # Complete cleanup
```

---

## Getting Help

```bash
make help               # See all commands
./start-local.sh --help # Script options
kubectl get pods -A     # Check cluster status
```
