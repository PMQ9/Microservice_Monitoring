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
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
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

# Deploy Prometheus using Helm
resource "helm_release" "prometheus" {
  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "prometheus"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 600

  values = [
    file("${path.module}/../observability/prometheus/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Jaeger using kubectl
resource "null_resource" "jaeger" {
  provisioner "local-exec" {
    command = "kubectl apply -f ${path.module}/../observability/jaeger/jaeger-deployment.yaml"
  }

  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Loki using Helm
resource "helm_release" "loki" {
  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 600

  values = [
    file("${path.module}/../observability/loki/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Grafana using Helm
resource "helm_release" "grafana" {
  name             = "grafana"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "grafana"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 600

  values = [
    file("${path.module}/../observability/grafana/values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# Deploy Prometheus Operator for ServiceMonitor support
resource "helm_release" "kube_prometheus_stack" {
  name             = "prometheus-operator"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 900

  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  depends_on = [kubernetes_namespace.monitoring]
}

# Apply ServiceMonitor for OTel metrics using kubectl
resource "null_resource" "service_monitor" {
  provisioner "local-exec" {
    command = "kubectl apply -f ${path.module}/../observability/prometheus/service-monitor.yaml"
  }

  depends_on = [helm_release.kube_prometheus_stack]
}

# Deploy backend service (default namespace already exists)
resource "kubernetes_manifest" "backend_deployment" {
  manifest = yamldecode(file("${path.module}/../app/backend/backend-deployment.yaml"))
}

resource "kubernetes_manifest" "backend_service" {
  manifest = yamldecode(file("${path.module}/../app/backend/backend-service.yaml"))
}

# Deploy frontend service
resource "kubernetes_manifest" "frontend_deployment" {
  manifest = yamldecode(file("${path.module}/../app/frontend/frontend-deployment.yaml"))
}

resource "kubernetes_manifest" "frontend_service" {
  manifest = yamldecode(file("${path.module}/../app/frontend/frontend-service.yaml"))
}

# Deploy ConfigMap
resource "kubernetes_manifest" "configmap" {
  manifest = yamldecode(file("${path.module}/../app/configmap.yaml"))
}
