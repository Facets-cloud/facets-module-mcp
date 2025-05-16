variable "instance" {
  description = "Provisions an AWS S3 bucket with secure defaults and configurable lifecycle policies for banking industry compliance."
  type = object({
    kind    = string
    flavor  = string
    version = string
    spec = object({
      bucket_name_prefix = string
      storage_type       = string
      enable_versioning  = bool
    })
  })
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
    aws_provider = any
  })
}