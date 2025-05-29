# Microservice_Monitoring
Full-stack monitoring platform to surveil microservices, alerts and debug issues, auto-scales and deploy via GitOps/ArgoCD

**What this does**

Tracks, visualizes, and alerts on the health of microservices running in Kubernetes
- Is my app working?
- Why is my app so slow? CPU/memory bottleneck?
- Who broke the production by push --force to ProdDB?

**Key Features**

- Metric Collection (Prometheus) 
- Distributed Tracing (Jaeger)
- Log Aggregation (Loki + Grafana)
