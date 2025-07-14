variable "instance_name" {
  description = "Unique architectural name for the resource"
  type        = string
}

variable "environment" {
  description = "Environment-specific metadata"
  type = object({
    name        = string
    unique_name = string
    cloud_tags  = map(string)
  })
}

variable "instance" {
  description = "Instance configuration"
  type = object({
    spec = object({
      bucket_name = optional(string)
      versioning = object({
        enabled    = bool
        mfa_delete = optional(bool, false)
      })
      encryption = object({
        enabled    = bool
        kms_key_id = optional(string)
      })
      public_access_block = object({
        block_public_acls       = bool
        block_public_policy     = bool
        ignore_public_acls      = bool
        restrict_public_buckets = bool
      })
      lifecycle_configuration = object({
        enabled                    = bool
        transition_to_ia_days      = optional(number, 30)
        transition_to_glacier_days = optional(number, 90)
        expiration_days            = optional(number, 0)
      })
      tags = optional(map(string), {})
    })
  })

  validation {
    condition     = var.instance.spec.bucket_name == null || can(regex("^[a-z0-9][a-z0-9\\-]*[a-z0-9]$", var.instance.spec.bucket_name))
    error_message = "Bucket name must be between 3-63 characters, start and end with alphanumeric characters, and contain only lowercase letters, numbers, and hyphens."
  }

  validation {
    condition     = var.instance.spec.bucket_name == null || (length(var.instance.spec.bucket_name) >= 3 && length(var.instance.spec.bucket_name) <= 63)
    error_message = "Bucket name must be between 3 and 63 characters long."
  }

  validation {
    condition     = var.instance.spec.lifecycle_configuration.transition_to_ia_days >= 30
    error_message = "Transition to IA must be at least 30 days."
  }

  validation {
    condition     = var.instance.spec.lifecycle_configuration.transition_to_glacier_days >= 90
    error_message = "Transition to Glacier must be at least 90 days."
  }

  validation {
    condition     = var.instance.spec.lifecycle_configuration.expiration_days >= 0
    error_message = "Expiration days must be 0 or greater (0 means no expiration)."
  }
}

variable "inputs" {
  description = "Inputs from other modules"
  type = object({
    aws_provider = any
  })
}