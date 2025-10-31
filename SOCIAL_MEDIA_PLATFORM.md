# Social Media Platform - Microservices Monitoring Demo

A comprehensive social media-like platform demonstrating microservices architecture with full observability using OpenTelemetry, Prometheus, Jaeger, and Grafana.

## Architecture Overview

This platform consists of three core microservices that simulate a social media environment:

### 1. Content Creator Service (Port 5001)
Manages content creators and content creation.

**Features:**
- Register new content creators
- Create content (videos, images, articles, audio, stories)
- Track content creation metrics
- Monitor creator statistics

**Metrics Exposed:**
- `content.created` - Total content items created (by type)
- `creators.active` - Number of active creators
- `content.creation.duration` - Content creation time
- `creator.requests.total` - Request count by endpoint

### 2. User Service (Port 5002)
Manages users and their interactions with content.

**Features:**
- Register new users
- View content
- Like content
- Browse random content
- Track user engagement

**Metrics Exposed:**
- `users.active` - Number of active users
- `content.views` - Total content views (by type)
- `content.likes` - Total likes (by type)
- `content.access.duration` - Content access time
- `user.requests.total` - Request count by endpoint

### 3. Content Service (Port 5003)
Traffic generator and platform orchestration service.

**Features:**
- Automated random traffic generation
- Platform-wide statistics aggregation
- Simulation control (start/stop)
- Distributed tracing across services

**Metrics Exposed:**
- `traffic.generated` - Traffic generation events (by action type)
- `simulation.active` - Simulation status

## Key Features

### Random Traffic Generation
The Content Service includes an intelligent traffic generator that:
- Creates content creators at random intervals
- Generates users randomly
- Creates content with random types
- Simulates users viewing content
- Simulates users liking content (30% probability)
- Maintains realistic activity patterns with random delays

### Full Observability Stack

**Metrics (Prometheus)**
- All services export Prometheus metrics on port 8000
- ServiceMonitors automatically scrape metrics
- Custom business metrics (content created, views, likes)
- Performance metrics (request duration, response times)

**Distributed Tracing (Jaeger)**
- Full request tracing across all services
- Trace user viewing content from User Service → Content Creator Service
- Performance bottleneck identification
- Service dependency mapping

**Dashboards (Grafana)**
Two pre-configured dashboards:

1. **Content Creators Dashboard**
   - Total creators count
   - Total content created
   - Content creation rate
   - Content by type distribution
   - Content creation duration (p95)
   - Request rates
   - Top creators by content count

2. **Users Performance Dashboard**
   - Active users count
   - Total views and likes
   - Engagement rate (likes/views %)
   - View and like rates over time
   - Content access duration
   - Views by content type
   - Most active users

## Deployment

### Quick Start

```bash
# Deploy everything
./utils/deploy-social-media.sh
```

This script will:
1. Check Minikube status
2. Build all Docker images
3. Deploy monitoring stack (if not present)
4. Deploy ServiceMonitors
5. Deploy all three microservices
6. Wait for pods to be ready

### Manual Deployment

```bash
# Build images (ensure Docker is pointed to Minikube)
eval $(minikube docker-env)

docker build -t content-creator-service:latest app/content-creator/
docker build -t user-service:latest app/user-service/
docker build -t content-service:latest app/content-service/

# Deploy services
kubectl apply -f app/content-creator/content-creator-deployment.yaml
kubectl apply -f app/content-creator/content-creator-service.yaml

kubectl apply -f app/user-service/user-service-deployment.yaml
kubectl apply -f app/user-service/user-service-service.yaml

kubectl apply -f app/content-service/content-service-deployment.yaml
kubectl apply -f app/content-service/content-service-service.yaml

# Deploy ServiceMonitors
kubectl apply -f observability/prometheus/service-monitor.yaml
```

## Usage

### Start Traffic Simulation

```bash
# Port forward to content service
kubectl port-forward -n default svc/content-service 5003:5003

# Start simulation
curl -X POST http://localhost:5003/api/simulation/start
```

### Check Platform Statistics

```bash
curl http://localhost:5003/api/platform/stats | python3 -m json.tool
```

```

### Stop Simulation

```bash
curl -X POST http://localhost:5003/api/simulation/stop
```

### Check Simulation Status

```bash
curl http://localhost:5003/api/simulation/status
```

## API Endpoints

### Content Creator Service

```bash
# Create a creator
curl -X POST http://content-creator-service:5001/api/creators \
  -H "Content-Type: application/json" \
  -d '{"name": "Creator Name"}'

# List all creators
curl http://content-creator-service:5001/api/creators

# Get specific creator
curl http://content-creator-service:5001/api/creators/{creator_id}

# Create content
curl -X POST http://content-creator-service:5001/api/content \
  -H "Content-Type: application/json" \
  -d '{"creator_id": "creator_1", "type": "video", "title": "My Video"}'

# List all content
curl http://content-creator-service:5001/api/content

# Get statistics
curl http://content-creator-service:5001/api/stats
```

### User Service

```bash
# Create a user
curl -X POST http://user-service:5002/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "User Name"}'

# List all users
curl http://user-service:5002/api/users

# Get specific user
curl http://user-service:5002/api/users/{user_id}

# View content
curl -X POST http://user-service:5002/api/users/{user_id}/view/{content_id}

# Like content
curl -X POST http://user-service:5002/api/users/{user_id}/like/{content_id}

# Get statistics
curl http://user-service:5002/api/stats
```

## Accessing Dashboards

### Grafana

```bash
# Get Grafana URL
minikube service grafana -n monitoring --url

# Get admin password
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Login credentials
Username: admin
Password: [from command above]
```

Import the dashboards:
1. Go to Dashboards → Import
2. Upload JSON files:
   - `observability/grafana/dashboards/content-creators-dashboard.json`
   - `observability/grafana/dashboards/users-dashboard.json`

### Jaeger (Distributed Tracing)

```bash
minikube service jaeger -n monitoring --url
```

### Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Access at: http://localhost:9090

Example queries:
```promql
# Content creation rate
rate(content_created_total[5m])

# Active users
users_active_total

# Content views by type
sum by (content_type) (content_views_total)

# Engagement rate
(sum(content_likes_total) / sum(content_views_total)) * 100
```

## Monitoring Metrics

### Business Metrics

**Content Metrics:**
- Total content created
- Content creation rate
- Content by type (video, image, article, audio, story)
- Content creation duration

**User Metrics:**
- Active users
- Total views and likes
- Engagement rate (likes/views)
- Average views per user
- Average likes per user

**Creator Metrics:**
- Active creators
- Content per creator
- Creator activity rate

### Technical Metrics

**Performance:**
- Request duration (p50, p95, p99)
- Request rate
- Error rate
- Service availability

**System:**
- Pod CPU and memory usage
- Network I/O
- Kubernetes metrics

## Architecture Benefits

### Scalability
- Each service can scale independently
- Kubernetes manages pod replicas
- LoadBalancer services distribute traffic

### Observability
- Full distributed tracing
- Custom business metrics
- Real-time dashboards
- Log aggregation (Loki)

### Resilience
- Health checks (liveness/readiness probes)
- Service discovery via Kubernetes DNS
- Automatic pod restarts
- Resource limits prevent resource exhaustion

## Traffic Simulation Details

The simulation generates realistic social media traffic patterns:

**Action Weights:**
- View content: 50% (most common action)
- Create content: 15%
- Like content: 20%
- Create user: 10%
- Create creator: 5%

**Timing:**
- Random delays between actions: 0.5-2 seconds
- Content creation time: 0.1-0.5 seconds
- Content viewing time: 0.5-3 seconds (simulated)

**Random Elements:**
- Content type selection
- User and content pairing
- Like probability (30%)

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n default
kubectl logs -n default -l app=content-creator
kubectl logs -n default -l app=user-service
kubectl logs -n default -l app=content-service
```

### Check Services
```bash
kubectl get svc -n default
kubectl describe svc content-creator-service -n default
```

### Check Metrics Endpoints
```bash
# Port forward metrics port
kubectl port-forward -n default deployment/content-creator 8000:8000

# Check metrics
curl http://localhost:8000/metrics
```

### Verify ServiceMonitors
```bash
kubectl get servicemonitor -n monitoring
kubectl describe servicemonitor content-creator-monitor -n monitoring
```

### Check Prometheus Targets
```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090/targets
# Verify all social media services are "UP"
```

## Service Dependencies

```
Content Service (Traffic Generator)
    ↓ creates creators
Content Creator Service
    ↑ fetch content list
    ↓ create content
    ↑
User Service
    ↑ view/like content

All Services → Jaeger (traces)
All Services → Prometheus (metrics)
```

## Cleanup

```bash
# Delete social media services
kubectl delete deployment content-creator user-service content-service -n default
kubectl delete svc content-creator-service user-service content-service -n default

# Delete ServiceMonitors
kubectl delete servicemonitor content-creator-monitor user-service-monitor content-service-monitor -n monitoring

# Or delete everything including monitoring
minikube delete
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │          Default Namespace                    │  │
│  │                                               │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  │  │
│  │  │ Content Creator │  │  User Service    │  │  │
│  │  │   Service       │  │                  │  │  │
│  │  │  Port: 5001     │  │  Port: 5002      │  │  │
│  │  │  Metrics: 8000  │  │  Metrics: 8000   │  │  │
│  │  └────────┬────────┘  └────────┬─────────┘  │  │
│  │           │                     │            │  │
│  │           └──────────┬──────────┘            │  │
│  │                      │                       │  │
│  │            ┌─────────▼──────────┐            │  │
│  │            │  Content Service   │            │  │
│  │            │ (Traffic Generator)│            │  │
│  │            │    Port: 5003      │            │  │
│  │            │    Metrics: 8000   │            │  │
│  │            └────────────────────┘            │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │        Monitoring Namespace                   │  │
│  │                                               │  │
│  │  ┌──────────┐  ┌─────────┐  ┌──────────┐    │  │
│  │  │Prometheus│  │ Jaeger  │  │ Grafana  │    │  │
│  │  │  :9090   │  │  :16686 │  │   :3000  │    │  │
│  │  └────┬─────┘  └────┬────┘  └─────┬────┘    │  │
│  │       │             │             │          │  │
│  │       └─────────────┴─────────────┘          │  │
│  │              (scrapes metrics)               │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```
