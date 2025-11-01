# Social Media Platform - Quick Start Guide

## Functionalities

A fully functional social media platform with:
- **4 Content Creators** creating content
- **13 Active Users** viewing and liking content
- **12 Pieces of Content** (articles, videos, audio, images, stories)
- **34 Total Views** across all content
- **20 Total Likes** from users
- **58.8% Engagement Rate** (likes/views)


## Quick Commands

### View Real-Time Statistics
```bash
# Port forward (if not already running)
kubectl port-forward -n default svc/content-service 5003:5003 &

# Check platform stats
curl -s http://localhost:5003/api/platform/stats | python3 -m json.tool
```

### Control Traffic Simulation
```bash
# Stop simulation
curl -X POST http://localhost:5003/api/simulation/stop

# Start simulation
curl -X POST http://localhost:5003/api/simulation/start

# Check status
curl http://localhost:5003/api/simulation/status
```

### Access Dashboards

**Grafana (Metrics Visualization):**
```bash
minikube service grafana -n monitoring --url

# Get password
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Login: admin / [password from above]
```

**Jaeger (Distributed Tracing):**
```bash
minikube service jaeger -n monitoring --url
```

**Prometheus (Raw Metrics):**
```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090
```

## What's Happening

The system is continuously:
1. Creating new content creators randomly
2. Generating users randomly
3. Creating content (videos, articles, audio, images, stories)
4. Simulating users viewing content
5. Simulating users liking content (30% probability)
6. Tracking all metrics in Prometheus
7. Sending distributed traces to Jaeger

## View Logs

```bash
# Content Creator Service
kubectl logs -f -l app=content-creator -n default

# User Service
kubectl logs -f -l app=user-service -n default

# Traffic Generator
kubectl logs -f -l app=content-service -n default
```

## Check Metrics

All services expose Prometheus metrics on port 8000:

```bash
# Content Creator metrics
kubectl port-forward -n default svc/content-creator-service 8000:8000
curl http://localhost:8000/metrics | grep content_created

# User metrics
kubectl port-forward -n default svc/user-service 8001:8000
curl http://localhost:8001/metrics | grep content_views
```

## Sample Prometheus Queries

Open Prometheus (see above) and try these queries:

```promql
# Total content created
sum(content_created_total)

# Content creation rate (per second)
rate(content_created_total[1m])

# Active users
users_active_total

# Total views by content type
sum by (content_type) (content_views_total)

# Engagement rate (%)
(sum(content_likes_total) / sum(content_views_total)) * 100

# p95 content access duration
histogram_quantile(0.95, rate(content_access_duration_bucket[5m]))
```

## Import Grafana Dashboards

Two pre-built dashboards are available:

1. **Content Creators Dashboard**
   - File: `observability/grafana/dashboards/content-creators-dashboard.json`
   - Shows: creator count, content created, creation rates, content types

2. **Users Performance Dashboard**
   - File: `observability/grafana/dashboards/users-dashboard.json`
   - Shows: user count, views, likes, engagement rate, most active users

## Architecture

```
Content-Service (Traffic Generator)
    ↓
    Creates creators → Content-Creator-Service
    Creates users    → User-Service
    Generates views  → User-Service → Content-Creator-Service
    Generates likes  → User-Service
```

All services send:
- **Metrics** → Prometheus (port 8000)
- **Traces** → Jaeger (http://jaeger.monitoring:4318)


## Scaling the Platform

```bash
# Scale content creators
kubectl scale deployment content-creator --replicas=3 -n default

# Scale users
kubectl scale deployment user-service --replicas=3 -n default

# Increase traffic (edit content-service/app.py delays)
```

## Stop/Cleanup

```bash
# Stop simulation (keep services running)
curl -X POST http://localhost:5003/api/simulation/stop

# Delete all social media services
kubectl delete deployment content-creator user-service content-service -n default
kubectl delete svc content-creator-service user-service content-service -n default

# Or delete entire cluster
minikube delete
```
