# Outputs for Terraform configuration
# These provide important information after deployment

output "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring stack"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "prometheus_endpoint" {
  description = "Prometheus service endpoint"
  value       = "prometheus.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:9090"
}

output "grafana_endpoint" {
  description = "Grafana service endpoint (port 80)"
  value       = "grafana.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:80"
}

output "grafana_admin_username" {
  description = "Grafana admin username"
  value       = "admin"
}

output "loki_endpoint" {
  description = "Loki service endpoint"
  value       = "loki.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:3100"
}

output "jaeger_endpoint" {
  description = "Jaeger service endpoint (OTLP gRPC)"
  value       = "jaeger.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:4317"
}

output "jaeger_http_endpoint" {
  description = "Jaeger service endpoint (OTLP HTTP)"
  value       = "jaeger.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:4318"
}

output "backend_service_endpoint" {
  description = "Backend service endpoint"
  value       = "backend-service.default.svc.cluster.local:5000"
}

output "frontend_service_endpoint" {
  description = "Frontend service endpoint"
  value       = "frontend-service.default.svc.cluster.local:5000"
}

output "deployment_info" {
  description = "Summary of deployed resources"
  value = {
    monitoring_namespace = kubernetes_namespace.monitoring.metadata[0].name
    applications_deployed = [
      "Prometheus",
      "Grafana",
      "Loki",
      "Jaeger",
      "Kube-Prometheus-Stack",
      "Backend Service",
      "Frontend Service"
    ]
  }
}

output "access_commands" {
  description = "Commands to access deployed services"
  value = {
    prometheus = "kubectl port-forward -n ${kubernetes_namespace.monitoring.metadata[0].name} svc/prometheus 9090:9090"
    grafana    = "kubectl port-forward -n ${kubernetes_namespace.monitoring.metadata[0].name} svc/grafana 3000:80"
    jaeger     = "kubectl port-forward -n ${kubernetes_namespace.monitoring.metadata[0].name} svc/jaeger 16686:16686"
    backend    = "kubectl port-forward -n default svc/backend-service 5000:5000"
    frontend   = "kubectl port-forward -n default svc/frontend-service 5000:5000"
  }
}
