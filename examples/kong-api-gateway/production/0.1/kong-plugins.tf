# Kong Plugin Configuration via ConfigMaps
# Simple approach without complex CRDs or init containers

# Kong Plugin Environment Variables ConfigMap
resource "kubernetes_config_map" "kong_plugins_env" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-plugins-env", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "plugin-config"
      }
    )
  }

  data = {
    # Basic plugin configuration flags
    "KONG_PLUGINS_RATE_LIMITING_ENABLED"      = var.instance.spec.plugins.rate_limiting.enabled ? "true" : "false"
    "KONG_PLUGINS_CORS_ENABLED"               = var.instance.spec.plugins.cors.enabled ? "true" : "false"
    "KONG_PLUGINS_KEY_AUTH_ENABLED"           = var.instance.spec.plugins.authentication.key_auth_enabled ? "true" : "false"
    "KONG_PLUGINS_REQUEST_SIZE_LIMIT_ENABLED" = var.instance.spec.plugins.security.request_size_limiting_enabled ? "true" : "false"
    "KONG_PLUGINS_BOT_DETECTION_ENABLED"      = var.instance.spec.plugins.security.bot_detection_enabled ? "true" : "false"
    "KONG_PLUGINS_PROMETHEUS_ENABLED"         = var.instance.spec.monitoring.prometheus_enabled ? "true" : "false"
  }
}

# Documentation ConfigMap for plugin setup
resource "kubernetes_config_map" "kong_plugin_setup_docs" {
  metadata {
    name      = trimsuffix(substr("${var.instance_name}-plugin-docs", 0, 63), "-")
    namespace = kubernetes_namespace.kong.metadata[0].name
    labels = merge(
      var.environment.cloud_tags,
      {
        "app.kubernetes.io/name"      = "kong"
        "app.kubernetes.io/instance"  = var.instance_name
        "app.kubernetes.io/component" = "documentation"
      }
    )
  }

  data = {
    "README.md" = <<-EOF
      # Kong API Gateway - ${var.instance_name}
      
      ## Access Information
      
      **Admin API (Internal)**:
      - URL: http://${trimsuffix(substr("${var.instance_name}-admin", 0, 63), "-")}.${kubernetes_namespace.kong.metadata[0].name}.svc.cluster.local:8001
      - Port-forward: kubectl port-forward -n ${kubernetes_namespace.kong.metadata[0].name} svc/${trimsuffix(substr("${var.instance_name}-admin", 0, 63), "-")} 8001:8001
      
      **Gateway Proxy**:
      ${var.instance.spec.ingress.enabled ? "- External URL: ${local.gateway_url}" : "- NodePort access available"}
      
      ## Plugin Configuration Status
      
      - Rate Limiting: ${var.instance.spec.plugins.rate_limiting.enabled ? "Enabled" : "Disabled"}
      - CORS: ${var.instance.spec.plugins.cors.enabled ? "Enabled" : "Disabled"}
      - Key Authentication: ${var.instance.spec.plugins.authentication.key_auth_enabled ? "Enabled" : "Disabled"}
      - Request Size Limiting: ${var.instance.spec.plugins.security.request_size_limiting_enabled ? "Enabled" : "Disabled"}
      - Bot Detection: ${var.instance.spec.plugins.security.bot_detection_enabled ? "Enabled" : "Disabled"}
      - Prometheus Metrics: ${var.instance.spec.monitoring.prometheus_enabled ? "Enabled" : "Disabled"}
      
      ## Manual Plugin Configuration
      
      To configure plugins via Kong Admin API:
      
      1. Port-forward to admin API:
         ```bash
         kubectl port-forward -n ${kubernetes_namespace.kong.metadata[0].name} svc/${trimsuffix(substr("${var.instance_name}-admin", 0, 63), "-")} 8001:8001
         ```
      
      2. Check Kong status:
         ```bash
         curl http://localhost:8001/status
         ```
      
      3. Add a service:
         ```bash
         curl -X POST http://localhost:8001/services \
           --data name=example-service \
           --data url=http://httpbin.org
         ```
      
      4. Add a route:
         ```bash
         curl -X POST http://localhost:8001/services/example-service/routes \
           --data paths[]=/example
         ```
      
      5. Configure rate limiting plugin:
         ```bash
         curl -X POST http://localhost:8001/plugins \
           --data name=rate-limiting \
           --data config.minute=${try(var.instance.spec.plugins.rate_limiting.requests_per_minute, 1000)} \
           --data config.policy=local
         ```
    EOF
  }
}
