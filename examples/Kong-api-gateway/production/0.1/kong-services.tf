# Kong Proxy Service - Pure Kubernetes, no AWS dependencies
resource "kubernetes_service" "kong_proxy" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-proxy", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "proxy"
      }
    )
    # Pure Kubernetes annotations only
    annotations = {
      "service.kubernetes.io/topology-aware-hints" = "auto"
    }
  }

  spec {
    # Always use ClusterIP to avoid any cloud provider LoadBalancer creation
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name"     = "kong"
      "app.kubernetes.io/instance" = var.instance_name
    }

    port {
      name        = "proxy"
      port        = 80
      target_port = 8000
      protocol    = "TCP"
    }

    port {
      name        = "proxy-ssl"
      port        = 443
      target_port = 8000
      protocol    = "TCP"
    }
  }
}

# Kong Admin Service (ClusterIP only for security)
resource "kubernetes_service" "kong_admin" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-admin", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "admin"
      }
    )
  }

  spec {
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name"     = "kong"
      "app.kubernetes.io/instance" = var.instance_name
    }

    port {
      name        = "admin"
      port        = 8001
      target_port = 8001
      protocol    = "TCP"
    }
  }
}

# Kong Status Service (for health checks and metrics)
resource "kubernetes_service" "kong_status" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-status", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "status"
      }
    )
    annotations = var.instance.spec.monitoring.prometheus_enabled ? {
      "prometheus.io/scrape" = "true"
      "prometheus.io/port"   = "8100"
      "prometheus.io/path"   = "/metrics"
    } : {}
  }

  spec {
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name"     = "kong"
      "app.kubernetes.io/instance" = var.instance_name
    }

    port {
      name        = "status"
      port        = 8100
      target_port = 8100
      protocol    = "TCP"
    }
  }
}

# Kong Ingress - Standard Kubernetes ingress (no cloud-specific features)
resource "kubernetes_ingress_v1" "kong_proxy" {
  count = var.instance.spec.ingress.enabled ? 1 : 0

  metadata {
    name      = trimsuffix(substr("${var.instance_name}-ingress", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "ingress"
      }
    )
    # Standard Kubernetes ingress annotations only (no AWS ALB)
    annotations = merge(
      {
        "nginx.ingress.kubernetes.io/proxy-body-size"    = "${try(var.instance.spec.plugins.security.max_request_size, 10)}m"
        "nginx.ingress.kubernetes.io/proxy-read-timeout" = "300"
        "nginx.ingress.kubernetes.io/proxy-send-timeout" = "300"
        "nginx.ingress.kubernetes.io/ssl-redirect"       = var.instance.spec.ingress.tls_enabled ? "true" : "false"
      },
      try(var.instance.spec.ingress.cert_manager_enabled, false) && var.instance.spec.ingress.tls_enabled ? {
        "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
      } : {}
    )
  }

  spec {
    ingress_class_name = "nginx"

    dynamic "tls" {
      for_each = var.instance.spec.ingress.tls_enabled && try(var.instance.spec.ingress.hostname, null) != null ? [1] : []
      content {
        hosts       = [try(var.instance.spec.ingress.hostname, "kong-gateway.local")]
        secret_name = trimsuffix(substr("${var.instance_name}-tls", 0, 63), "-")
      }
    }

    rule {
      host = try(var.instance.spec.ingress.hostname, "kong-gateway.local")
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.kong_proxy.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}

# NodePort Service for external access when ingress is disabled
resource "kubernetes_service" "kong_nodeport" {
  count = var.instance.spec.ingress.enabled ? 0 : 1

  metadata {
    name      = trimsuffix(substr("${var.instance_name}-nodeport", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "nodeport"
      }
    )
  }

  spec {
    type = "NodePort"

    selector = {
      "app.kubernetes.io/name"     = "kong"
      "app.kubernetes.io/instance" = var.instance_name
    }

    port {
      name        = "proxy"
      port        = 80
      target_port = 8000
      protocol    = "TCP"
    }

    port {
      name        = "proxy-ssl"
      port        = 443
      target_port = 8000
      protocol    = "TCP"
    }
  }
}