# Terraform configuration for Microservice Monitoring Stack
# This demonstrates Infrastructure-as-Code best practices and complete automation

terraform {
  required_version = ">= 1.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
  config_context = var.kubeconfig_context
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
    config_context = var.kubeconfig_context
  }
}

# Create monitoring namespace
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.monitoring_namespace
    labels = {
      "name" = var.monitoring_namespace
    }
  }

  depends_on = []
}

# Add Prometheus Helm repository
resource "helm_repository" "prometheus" {
  name           = "prometheus-community"
  url            = "https://prometheus-community.github.io/helm-charts"
  repository_ca_certificate = var.helm_ca_cert
}

# Add Grafana Helm repository
resource "helm_repository" "grafana" {
  name           = "grafana"
  url            = "https://grafana.github.io/helm-charts"
  repository_ca_certificate = var.helm_ca_cert
}

# Deploy Prometheus using Helm
resource "helm_release" "prometheus" {
  name            = "prometheus"
  repository      = helm_repository.prometheus.name
  chart           = "prometheus"
  namespace       = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait            = true
  timeout         = 600

  values = [
    file("${path.module}/../observability/prometheus/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring, helm_repository.prometheus]
}

# Deploy Jaeger
resource "kubernetes_manifest" "jaeger" {
  manifest = yamldecode(file("${path.module}/../observability/jaeger/jaeger-deployment.yaml"))

  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Loki using Helm
resource "helm_release" "loki" {
  name            = "loki"
  repository      = helm_repository.grafana.name
  chart           = "loki"
  namespace       = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait            = true
  timeout         = 600

  values = [
    file("${path.module}/../observability/loki/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring, helm_repository.grafana]
}

# Deploy Grafana using Helm
resource "helm_release" "grafana" {
  name            = "grafana"
  repository      = helm_repository.grafana.name
  chart           = "grafana"
  namespace       = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait            = true
  timeout         = 600

  values = [
    file("${path.module}/../observability/grafana/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring, helm_repository.grafana]
}

# Deploy Prometheus Operator for ServiceMonitor support
resource "helm_release" "kube_prometheus_stack" {
  name            = "prometheus-operator"
  repository      = helm_repository.prometheus.name
  chart           = "kube-prometheus-stack"
  namespace       = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait            = true
  timeout         = 900

  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  depends_on = [kubernetes_namespace.monitoring, helm_repository.prometheus]
}

# Apply ServiceMonitor for OTel metrics
resource "kubernetes_manifest" "service_monitor" {
  manifest = yamldecode(file("${path.module}/../observability/prometheus/service-monitor.yaml"))

  depends_on = [helm_release.kube_prometheus_stack]
}

# Create default namespace resources (applications)
resource "kubernetes_namespace" "default" {
  metadata {
    name = "default"
    labels = {
      "name" = "default"
    }
  }
}

# Deploy backend service
resource "kubernetes_manifest" "backend_deployment" {
  manifest = yamldecode(file("${path.module}/../app/backend/backend-deployment.yaml"))

  depends_on = [kubernetes_namespace.default]
}

resource "kubernetes_manifest" "backend_service" {
  manifest = yamldecode(file("${path.module}/../app/backend/backend-service.yaml"))

  depends_on = [kubernetes_namespace.default]
}

# Deploy frontend service
resource "kubernetes_manifest" "frontend_deployment" {
  manifest = yamldecode(file("${path.module}/../app/frontend/frontend-deployment.yaml"))

  depends_on = [kubernetes_namespace.default]
}

resource "kubernetes_manifest" "frontend_service" {
  manifest = yamldecode(file("${path.module}/../app/frontend/frontend-service.yaml"))

  depends_on = [kubernetes_namespace.default]
}

# Deploy ConfigMap
resource "kubernetes_manifest" "configmap" {
  manifest = yamldecode(file("${path.module}/../app/configmap.yaml"))

  depends_on = [kubernetes_namespace.default]
}
