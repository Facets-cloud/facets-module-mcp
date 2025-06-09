locals {
  output_attributes = {
    replicas           = var.instance.spec.deployment.replicas
    admin_url          = local.admin_url
    namespace          = kubernetes_namespace.kong.metadata[0].name
    admin_port         = "\"8001\""
    proxy_port         = "\"80\""
    gateway_url        = local.gateway_url
    tls_enabled        = var.instance.spec.ingress.tls_enabled
    kong_version       = local.kong_version
    service_name       = kubernetes_service.kong_proxy.metadata[0].name
    database_mode      = var.instance.spec.database.mode
    plugins_enabled    = local.enabled_plugins
    ingress_hostname   = try(var.instance.spec.ingress.hostname, "kong-gateway.local")
    admin_service_name = kubernetes_service.kong_admin.metadata[0].name
    prometheus_enabled = var.instance.spec.monitoring.prometheus_enabled
    ingress_enabled    = var.instance.spec.ingress.enabled
    nodeport_service   = var.instance.spec.ingress.enabled ? null : kubernetes_service.kong_nodeport[0].metadata[0].name
  }
  output_interfaces = {
    admin_endpoint = {
      url          = local.admin_url
      port         = "\"8001\""
      hostname     = local.admin_hostname
      protocol     = "\"http\""
      service_name = kubernetes_service.kong_admin.metadata[0].name
    }
    gateway_endpoint = {
      url         = local.gateway_url
      port        = var.instance.spec.ingress.enabled ? local.gateway_port : 30080
      hostname    = local.gateway_hostname
      protocol    = var.instance.spec.ingress.enabled ? local.gateway_protocol : "http"
      tls_enabled = var.instance.spec.ingress.tls_enabled
    }
  }
}