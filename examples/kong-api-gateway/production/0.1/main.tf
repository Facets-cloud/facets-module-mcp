# Kong API Gateway - Production Ready Kubernetes Deployment
# This module deploys Kong API Gateway as a pure Kubernetes deployment

# Kong Namespace - Main entry point for the module
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

# Kong ConfigMap for DB-less configuration
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
    KONG_DATABASE         = var.instance.spec.database.mode == "dbless" ? "off" : "postgres"
    KONG_PROXY_ACCESS_LOG = "/dev/stdout"
    KONG_ADMIN_ACCESS_LOG = "/dev/stdout"
    KONG_PROXY_ERROR_LOG  = "/dev/stderr"
    KONG_ADMIN_ERROR_LOG  = "/dev/stderr"
    KONG_LOG_LEVEL        = var.instance.spec.monitoring.logging.level
    KONG_ADMIN_LISTEN     = "0.0.0.0:8001"
    KONG_PROXY_LISTEN     = "0.0.0.0:8000"
    KONG_STATUS_LISTEN    = "0.0.0.0:8100"
    KONG_PLUGINS          = join(",", local.enabled_plugins)
    
    # Database configuration (only if postgres mode)
    KONG_PG_HOST     = var.instance.spec.database.mode == "postgres" ? try(var.instance.spec.database.postgres.host, "") : ""
    KONG_PG_PORT     = var.instance.spec.database.mode == "postgres" ? tostring(try(var.instance.spec.database.postgres.port, 5432)) : ""
    KONG_PG_DATABASE = var.instance.spec.database.mode == "postgres" ? try(var.instance.spec.database.postgres.database, "kong") : ""
    KONG_PG_USER     = var.instance.spec.database.mode == "postgres" ? try(var.instance.spec.database.postgres.username, "kong") : ""
  }
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

# Kong Deployment - Core application
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

          env_from {
            config_map_ref {
              name = kubernetes_config_map.kong.metadata[0].name
            }
          }

          resources {
            requests = {
              cpu    = var.instance.spec.deployment.resources.requests.cpu
              memory = var.instance.spec.deployment.resources.requests.memory
            }
            limits = {
              cpu    = var.instance.spec.deployment.resources.limits.cpu
              memory = var.instance.spec.deployment.resources.limits.memory
            }
          }

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

          # Health checks
          liveness_probe {
            http_get {
              path = var.instance.spec.monitoring.health_checks.liveness_probe_path
              port = 8100
            }
            initial_delay_seconds = 60
            period_seconds        = 30
            timeout_seconds       = 10
            failure_threshold     = 5
          }

          readiness_probe {
            http_get {
              path = var.instance.spec.monitoring.health_checks.readiness_probe_path
              port = 8100
            }
            initial_delay_seconds = 30
            period_seconds        = 15
            timeout_seconds       = 5
            failure_threshold     = 3
          }
        }

        restart_policy = "Always"
      }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "25%"
        max_surge       = "25%"
      }
    }
  }

  depends_on = [
    kubernetes_config_map.kong,
    kubernetes_service_account.kong
  ]
}

# Kong Proxy Service - Main gateway service
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
  }

  spec {
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

# Kong Admin Service - Admin API access
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