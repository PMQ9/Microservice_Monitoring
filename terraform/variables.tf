# Variables for Terraform configuration
# These can be overridden via terraform.tfvars or command-line flags

variable "kubeconfig_path" {
  description = "Path to Kubernetes config file"
  type        = string
  default     = "~/.kube/config"
}

variable "kubeconfig_context" {
  description = "Kubernetes context to use"
  type        = string
  default     = "minikube"
}

variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring stack"
  type        = string
  default     = "monitoring"
}

variable "helm_ca_cert" {
  description = "CA certificate for Helm repositories (optional)"
  type        = string
  default     = null
}

variable "prometheus_replica_count" {
  description = "Number of Prometheus replicas for high availability"
  type        = number
  default     = 1
  validation {
    condition     = var.prometheus_replica_count >= 1
    error_message = "Prometheus replica count must be at least 1."
  }
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = "admin"
}

variable "enable_ha" {
  description = "Enable high availability configurations"
  type        = bool
  default     = false
}

variable "enable_tls" {
  description = "Enable TLS for ingress"
  type        = bool
  default     = false
}

variable "backend_replicas" {
  description = "Number of backend service replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.backend_replicas >= 1
    error_message = "Backend replicas must be at least 1."
  }
}

variable "frontend_replicas" {
  description = "Number of frontend service replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.frontend_replicas >= 1
    error_message = "Frontend replicas must be at least 1."
  }
}

variable "resource_limits" {
  description = "Resource limits for services"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "500m"
    memory = "512Mi"
  }
}

variable "resource_requests" {
  description = "Resource requests for services"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "100m"
    memory = "128Mi"
  }
}

variable "enable_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "autoscaling_min_replicas" {
  description = "Minimum replicas for autoscaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_replicas" {
  description = "Maximum replicas for autoscaling"
  type        = number
  default     = 5
}

variable "autoscaling_target_cpu" {
  description = "Target CPU percentage for autoscaling"
  type        = number
  default     = 80
}
