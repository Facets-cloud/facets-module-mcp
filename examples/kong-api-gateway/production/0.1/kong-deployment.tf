# Kong Namespace
resource "kubernetes_namespace" "kong" {
  metadata {
    name = "${var.instance.spec.namespace}-${var.instance_name}"
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"       = "kong"
        "app.kubernetes.io/instance"   = var.instance_name
        "app.kubernetes.io/component"  = "api-gateway"
        "app.kubernetes.io/managed-by" = "terraform"
        "facets.cloud/managed-by"      = "facets"
        "facets.cloud/environment"     = var.environment.name
      }
    )
  }
}

# Kong ConfigMap for configuration
resource "kubernetes_config_map" "kong" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-config", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "configuration"
      }
    )
  }

  data = {
    # Simple Kong configuration for DB-less mode
    KONG_DATABASE         = "off"
    KONG_PROXY_ACCESS_LOG = "/dev/stdout"
    KONG_ADMIN_ACCESS_LOG = "/dev/stdout"
    KONG_PROXY_ERROR_LOG  = "/dev/stderr"
    KONG_ADMIN_ERROR_LOG  = "/dev/stderr"
    KONG_LOG_LEVEL        = var.instance.spec.monitoring.logging.level
    KONG_ADMIN_LISTEN     = "0.0.0.0:8001"
    KONG_PROXY_LISTEN     = "0.0.0.0:8000"
    KONG_STATUS_LISTEN    = "0.0.0.0:8100"
    KONG_PLUGINS          = "bundled"
  }
}

# Kong Deployment
resource "kubernetes_deployment" "kong" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-kong", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "api-gateway"
        "app.kubernetes.io/version"   = local.kong_version
      }
    )
  }

  spec {
    replicas = var.instance.spec.deployment.replicas

    selector {
      match_labels = {
        "app.kubernetes.io/name"     = "kong"
        "app.kubernetes.io/instance" = var.instance_name
      }
    }

    template {
      metadata {
        labels = merge(
          var.environment.cloud_tags,
          {
            "app.kubernetes.io/name"      = "kong"
            "app.kubernetes.io/instance"  = var.instance_name
            "app.kubernetes.io/component" = "api-gateway"
            "app.kubernetes.io/version"   = local.kong_version
          }
        )
        annotations = {
          "prometheus.io/scrape" = var.instance.spec.monitoring.prometheus_enabled ? "true" : "false"
          "prometheus.io/port"   = "8100"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.kong.metadata[0].name

        container {
          name  = "kong"
          image = "kong:${local.kong_version}"

          # Environment variables from ConfigMap
          env_from {
            config_map_ref {
              name = kubernetes_config_map.kong.metadata[0].name
            }
          }

          # Generous resource limits for better startup
          resources {
            requests = {
              cpu    = "100m"  # Very minimal for startup
              memory = "256Mi" # Minimal memory
            }
            limits = {
              cpu    = var.instance.spec.deployment.resources.limits.cpu
              memory = var.instance.spec.deployment.resources.limits.memory
            }
          }

          # Ports
          port {
            name           = "proxy"
            container_port = 8000
            protocol       = "TCP"
          }

          port {
            name           = "admin"
            container_port = 8001
            protocol       = "TCP"
          }

          port {
            name           = "status"
            container_port = 8100
            protocol       = "TCP"
          }

          # Very patient health checks
          liveness_probe {
            http_get {
              path = "/status"
              port = 8100
            }
            initial_delay_seconds = 120 # Very long delay for startup
            period_seconds        = 30
            timeout_seconds       = 10
            failure_threshold     = 10
          }

          readiness_probe {
            http_get {
              path = "/status"
              port = 8100
            }
            initial_delay_seconds = 60 # Long delay for startup
            period_seconds        = 15
            timeout_seconds       = 5
            failure_threshold     = 5
          }
        }

        restart_policy = "Always"
      }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "50%" # More aggressive rolling update
        max_surge       = "50%"
      }
    }
  }

  depends_on = [
    kubernetes_config_map.kong
  ]
}

# Kong Service Account
resource "kubernetes_service_account" "kong" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-sa", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "service-account"
      }
    )
  }
}