variable "instance" {
  description = "Creates a GitHub Actions workflow to build and test Java Maven applications with optional SonarQube integration"
  type = object({
    kind    = string
    flavor  = string
    version = string
    spec = object({
      repository_name       = string
      branch_name           = string
      enable_sonarqube      = bool
      java_version          = string
      workflow_name         = string
      sonarqube_project_key = string
      sonarqube_token       = string
      sonarqube_host_url    = string
      enable_docker_build   = bool
      docker_registry       = string
      docker_image_name     = string
      docker_username       = string
      docker_password       = string
      dockerfile_path       = string
    })
  })

  validation {
    condition     = can(regex("^[a-zA-Z0-9_.-]+$", var.instance.spec.repository_name))
    error_message = "The repository_name must contain only alphanumeric characters, underscores, periods, and hyphens."
  }

  validation {
    condition     = contains(["8", "11", "17", "21"], var.instance.spec.java_version)
    error_message = "The java_version must be one of: 8, 11, 17, or 21."
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
  })
}