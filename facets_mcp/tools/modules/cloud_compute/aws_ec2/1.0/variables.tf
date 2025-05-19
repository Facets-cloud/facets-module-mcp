variable "instance" {
  description = "A detailed AWS EC2 instance module that allows for comprehensive VM configuration including instance type, AMI, storage, networking, security groups, and more."
  type = object({
    kind    = string
    flavor  = string
    version = string
    spec = object({
      instance_type              = string
      ami_id                     = optional(string, "")
      root_volume_size           = number
      root_volume_type           = string
      associate_public_ip        = optional(bool, true)
      enable_detailed_monitoring = optional(bool, false)
      hostname                   = optional(string, "")
      user_data                  = optional(string, "")
      additional_volumes = optional(object({
        enabled = optional(bool, false)
        volumes = optional(object({
          data_volume = optional(object({
            device_name = string
            size        = number
            type        = string
            encrypted   = optional(bool, true)
          }))
        }))
      }))
      iam = optional(object({
        instance_profile_config        = optional(string, "none")
        existing_instance_profile_name = optional(string, "")
        create_instance_profile = optional(object({
          policy_json = optional(string, "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"s3:ListAllMyBuckets\",\"Resource\":\"*\"}]}")
        }), {})
      }), {})
      security_groups = optional(object({
        ssh_access = optional(object({
          source_cidr = optional(string, "0.0.0.0/0")
          key_name    = optional(string, "")
        }), {})
        ingress_rules = optional(object({
          rules = optional(map(object({
            description = string
            from_port   = number
            to_port     = number
            protocol    = string
            cidr_blocks = string
          })), {})
        }), {})
        egress_rules = optional(object({
          restrict_default = optional(bool, false)
          rules = optional(map(object({
            description = string
            from_port   = number
            to_port     = number
            protocol    = string
            cidr_blocks = string
          })), {})
        }), {})
      }), {})
      tags = optional(map(object({
        key   = string
        value = string
      })), {})
    })
  })

  validation {
    condition     = can(regex("^(ami-[a-f0-9]{17})?$", var.instance.spec.ami_id))
    error_message = "AMI ID must be in the format ami-xxxxxxxxxxxxxxxxx or left empty"
  }

  validation {
    condition     = var.instance.spec.root_volume_size >= 8 && var.instance.spec.root_volume_size <= 16384
    error_message = "Root volume size must be between 8 and 16384 GB"
  }

  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2", "sc1", "st1", "standard"], var.instance.spec.root_volume_type)
    error_message = "Root volume type must be one of: gp2, gp3, io1, io2, sc1, st1, standard"
  }

  validation {
    condition     = contains(["none", "existing", "create_new"], try(var.instance.spec.iam.instance_profile_config, "none"))
    error_message = "IAM instance profile configuration must be one of: none, existing, create_new"
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
    cloud_tags  = map(string)
  })
}

variable "inputs" {
  description = "A map of inputs requested by the module developer."
  type = object({
    cloud_account_details = object({})
    network_details = object({
      vpc_id    = string
      subnet_id = string
    })
  })
}