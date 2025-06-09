# Local variables for Kong configuration
locals {
  # Kong version to use
  kong_version = "3.4"

  # Generate safe resource names (Kubernetes resource name length limits)
  base_name = "${var.instance_name}-${var.environment.unique_name}"
  safe_name = length(local.base_name) > 32 ? trimsuffix(substr(local.base_name, 0, 32), "-") : local.base_name

  # Simple enabled plugins list
  enabled_plugins = compact([
    "bundled",
    var.instance.spec.plugins.rate_limiting.enabled ? "rate-limiting" : "",
    var.instance.spec.plugins.cors.enabled ? "cors" : "",
    var.instance.spec.plugins.security.request_size_limiting_enabled ? "request-size-limiting" : "",
    var.instance.spec.plugins.security.bot_detection_enabled ? "bot-detection" : "",
    var.instance.spec.plugins.authentication.key_auth_enabled ? "key-auth" : "",
    var.instance.spec.monitoring.prometheus_enabled ? "prometheus" : ""
  ])

  # Compute gateway endpoint URL - Updated for Kubernetes-only deployment
  gateway_protocol = var.instance.spec.ingress.tls_enabled ? "https" : "http"
  gateway_port     = var.instance.spec.ingress.tls_enabled ? 443 : 80

  # Gateway hostname logic - Handle optional hostname safely
  gateway_hostname = try(var.instance.spec.ingress.hostname, null) != null ? var.instance.spec.ingress.hostname : (
    var.instance.spec.ingress.enabled ? "kong-gateway.local" : "localhost"
  )

  # Gateway URL construction
  gateway_url = var.instance.spec.ingress.enabled ? (
    "${local.gateway_protocol}://${local.gateway_hostname}${local.gateway_port != 80 && local.gateway_port != 443 ? ":${local.gateway_port}" : ""}"
    ) : (
    # When ingress is disabled, use NodePort
    "http://${local.gateway_hostname}:30080"
  )

  # Compute admin endpoint URL (internal only) - Always internal cluster access
  admin_hostname = "${trimsuffix(substr("${var.instance_name}-admin", 0, 63), "-")}.${kubernetes_namespace.kong.metadata[0].name}.svc.cluster.local"
  admin_url      = "http://${local.admin_hostname}:8001"

  # Common labels for resources
  common_labels = merge(
    var.environment.cloud_tags,
    {
      "app.kubernetes.io/name"       = "kong"
      "app.kubernetes.io/instance"   = var.instance_name
      "app.kubernetes.io/version"    = local.kong_version
      "app.kubernetes.io/managed-by" = "facets"
      "facets/environment"           = var.environment.name
      "facets/instance-name"         = var.instance_name
    }
  )
}

# Simple Pod Disruption Budget for high availability
resource "kubernetes_pod_disruption_budget_v1" "kong" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-pdb", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels    = local.common_labels
  }

  spec {
    min_available = max(1, floor(var.instance.spec.deployment.replicas * 0.5))

    selector {
      match_labels = {
        "app.kubernetes.io/name"     = "kong"
        "app.kubernetes.io/instance" = var.instance_name
      }
    }
  }
}

# Basic RBAC for Kong
resource "kubernetes_cluster_role" "kong" {
  metadata {
    name   = trimsuffix(substr("${var.instance_name}-${var.environment.unique_name}-cr", 0, 63), "-")
    labels = local.common_labels
  }

  rule {
    api_groups = [""]
    resources  = ["services", "endpoints"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["networking.k8s.io"]
    resources  = ["ingresses"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_cluster_role_binding" "kong" {
  metadata {
    name   = trimsuffix(substr("${var.instance_name}-${var.environment.unique_name}-crb", 0, 63), "-")
    labels = local.common_labels
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.kong.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.kong.metadata[0].name
    namespace = kubernetes_namespace.kong.metadata[0].name
  }
}