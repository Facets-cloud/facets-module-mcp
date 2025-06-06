variable "instance" {
  description = "Production-ready Kong API Gateway deployment with secure defaults, SSL termination, rate limiting, and authentication"
  type = object({
    kind    = string
    flavor  = string
    version = string
    spec = object({
      namespace = string

      deployment = object({
        replicas = number
        resources = object({
          requests = object({
            cpu    = string
            memory = string
          })
          limits = object({
            cpu    = string
            memory = string
          })
        })
      })

      ingress = object({
        enabled              = bool
        hostname             = optional(string)
        tls_enabled          = bool
        cert_manager_enabled = bool
      })

      database = object({
        mode = string
        postgres = optional(object({
          host     = optional(string)
          port     = optional(number, 5432)
          database = optional(string, "kong")
          username = optional(string, "kong")
        }))
      })

      plugins = object({
        rate_limiting = object({
          enabled             = bool
          requests_per_minute = optional(number, 1000)
        })
        cors = object({
          enabled = bool
          origins = optional(string, "*")
        })
        authentication = object({
          jwt_enabled      = optional(bool, false)
          oauth2_enabled   = optional(bool, false)
          key_auth_enabled = bool
        })
        security = object({
          ip_restriction_enabled        = optional(bool, false)
          bot_detection_enabled         = bool
          request_size_limiting_enabled = bool
          max_request_size              = optional(number, 10)
        })
      })

      monitoring = object({
        prometheus_enabled = bool
        logging = object({
          level              = string
          access_log_enabled = optional(bool, true)
        })
        health_checks = object({
          enabled              = bool
          liveness_probe_path  = optional(string, "/status")
          readiness_probe_path = optional(string, "/status/ready")
        })
      })
    })
  })

  validation {
    condition     = contains(["postgres", "dbless"], var.instance.spec.database.mode)
    error_message = "Database mode must be either 'postgres' or 'dbless'."
  }

  validation {
    condition     = var.instance.spec.deployment.replicas >= 1 && var.instance.spec.deployment.replicas <= 10
    error_message = "Number of replicas must be between 1 and 10."
  }

  validation {
    condition     = contains(["debug", "info", "notice", "warn", "error", "crit", "alert", "emerg"], var.instance.spec.monitoring.logging.level)
    error_message = "Log level must be one of: debug, info, notice, warn, error, crit, alert, emerg."
  }

  validation {
    condition     = try(var.instance.spec.plugins.security.max_request_size, 10) >= 1 && try(var.instance.spec.plugins.security.max_request_size, 10) <= 100
    error_message = "Maximum request size must be between 1 and 100 MB."
  }

  validation {
    condition     = try(var.instance.spec.plugins.rate_limiting.requests_per_minute, 1000) >= 1
    error_message = "Requests per minute must be at least 1."
  }

  validation {
    condition     = var.instance.spec.ingress.hostname == null || can(regex("^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?)*$", var.instance.spec.ingress.hostname))
    error_message = "Hostname must be a valid domain name format."
  }
}

variable "instance_name" {
  description = "The architectural name for the resource as added in the Facets blueprint designer."
  type        = string
}

variable "environment" {
  description = "An object containing details about the environment."
  type = object({
    name        = string
    unique_name = string
    cloud_tags  = optional(map(string), {})
  })
}

variable "inputs" {
  description = "A map of inputs requested by the module developer."
  type = object({
    kubernetes_cluster = optional(object({
      cluster_name           = string
      cluster_endpoint       = string
      cluster_ca_certificate = optional(string)
      namespace              = optional(string)
    }))
  })

  default = {
    kubernetes_cluster = null
  }
}