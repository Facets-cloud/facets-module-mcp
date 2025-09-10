# Facets Actions Tekton.tf Writing Guide

## Overview
This guide provides instructions for generating `tekton.tf` files that configure Facets Actions workflows within Terraform modules. The MCP automatically handles environment variable management for sensitive values.

## Module Schema

```hcl
module "workflow_name" {
  source = "github.com/Facets-cloud/facets-utility-modules//facets-workflows/kubernetes?ref=workflows"
  name   = "workflow-name"

  instance_name    = var.instance_name
  environment      = var.environment
  instance         = var.instance
  auth_secret_name = module.legacy_eks.legacy_attributes.k8s_details.workflows_auth_secret_name
  providers = {
    helm = "helm.release-pod"
  }

  description = "Description of what this workflow does"
  params = [
    # Array of params objects like `{ name = "revision", description = "Revision number to rollback to" }`
  ] 
  steps = [
    # Array of step objects
  ]
}
```

## Required Fields

- **source**: Always `github.com/Facets-cloud/facets-utility-modules//facets-workflows/kubernetes?ref=workflows`
- **name**: Kebab-case workflow name
- **instance_name**: `var.instance_name`
- **environment**: `var.environment`
- **instance**: `var.instance`
- **auth_secret_name**: `module.legacy_eks.legacy_attributes.k8s_details.workflows_auth_secret_name`
- **providers**: `{ helm = "helm.release-pod" }`
- **description**: String describing the workflow purpose
- **steps**: Array of step objects

## Step Object Schema

```hcl
{
  name      = "step-name"           # String: kebab-case step name
  image     = "container:tag"      # String: container image to run
  resources = {}                   # Object: resource constraints (can be empty)
  env = []                        # Array: environment variables (can be empty)
  script = <<-EOT                 # String: bash script content
    #!/bin/bash
    # Script content here
  EOT
}
```

## Parameter Schema

```hcl
{
  name        = "parameter_name"    # String: parameter name
  type        = "string"           # String: parameter type (string, array, etc.)
  description = "Parameter desc"   # String: parameter description
  default     = "default_value"    # Optional: default value
}
```

## Environment Variable Handling

The MCP automatically determines environment variable usage:

### Automatic Environment Variables
- **Sensitive values** (containing `.secret`, `.token`, `.password`, `.key`, `_secret`, etc.) are automatically wrapped in env variables
- **Non-sensitive values** can be referenced directly in scripts using Terraform interpolation

### Environment Variable Patterns
```hcl
env = [
  {
    name  = "SECRET_VALUE"
    value = var.secret_variable      # Secret values detected automatically
  },
  {
    name  = "RESOURCE_TYPE"
    value = local.resource_type      # Non-secret values for script clarity
  }
]
```

### Script Access Patterns
- **Parameter access**: Use `$(params.parameter_name)` syntax within scripts
- **Environment variables**: Use `$ENV_VAR_NAME` syntax in bash scripts
- **Direct references**: Non-sensitive terraform values can use `${var.name}` or `${module.name.output}`

## Examples

### Simple Workflow
```hcl
module "restart_task" {
  source = "github.com/Facets-cloud/facets-utility-modules//facets-workflows/kubernetes?ref=workflows"
  name   = "restart-deployment"
  
  # ... required fields ...
  
  description = "Restarts Kubernetes deployments"
  steps = [
    {
      name      = "restart-pods"
      image     = "bitnami/kubectl:latest"
      resources = {}
      env = [
        {
          name  = "NAMESPACE"
          value = local.namespace
        }
      ]
      script = <<-EOT
        #!/bin/bash
        kubectl rollout restart deployment -n $NAMESPACE
      EOT
    }
  ]
}
```

### Workflow with Parameters
```hcl
module "parameterized_task" {
  # ... module config ...
  
  params = [
    {
      name        = "action"
      type        = "string"
      description = "Action to perform: restart, stop, start"
      default     = "restart"
    }
  ]
  steps = [
    {
      name   = "perform-action"
      image  = "bitnami/kubectl:latest"
      script = <<-EOT
        #!/bin/bash
        ACTION="$(params.action)"
        echo "Performing action: $ACTION"
      EOT
    }
  ]
}
```

## Code Generation Guidelines

1. **Module Naming**: Convert kebab-case workflow names to snake_case for Terraform module names
2. **Parameter Validation**: Ensure all required parameters are present
3. **Environment Variables**: Automatically detect and wrap sensitive values
4. **Script Formatting**: Use heredoc format with proper indentation
5. **Error Handling**: Include proper bash error handling (`set -e`) in scripts
6. **Security**: Never expose secrets directly in script content