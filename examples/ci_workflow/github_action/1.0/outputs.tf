locals {
  output_attributes = {
    branch_name         = var.instance.spec.branch_name
    java_version        = var.instance.spec.java_version
    repository_name     = var.instance.spec.repository_name
    enable_sonarqube    = var.instance.spec.enable_sonarqube
    enable_docker_build = var.instance.spec.enable_docker_build
    workflow_content    = local.workflow_content
    workflow_file_path  = local_file.github_workflow.filename
    required_secrets    = local.all_secrets
    secrets_readme_path = local_file.github_secrets_readme.filename
  }
  output_interfaces = {
  }
}