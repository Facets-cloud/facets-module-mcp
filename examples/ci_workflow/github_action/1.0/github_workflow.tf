resource "local_file" "github_workflow" {
  filename = "${path.module}/github-workflow.yml"
  content  = local.workflow_content
}

locals {
  # Define GitHub Secrets
  github_secrets = {
    sonarqube = var.instance.spec.enable_sonarqube ? {
      SONAR_TOKEN    = var.instance.spec.sonarqube_token
      SONAR_HOST_URL = var.instance.spec.sonarqube_host_url
    } : {}

    docker = var.instance.spec.enable_docker_build ? {
      DOCKER_USERNAME = var.instance.spec.docker_username
      DOCKER_PASSWORD = var.instance.spec.docker_password
    } : {}
  }

  # Combine all secrets
  all_secrets = merge(local.github_secrets.sonarqube, local.github_secrets.docker)

  # Generate list of secrets for documentation
  secrets_list = join("\n", [for key, _ in local.all_secrets : "- ${key}"])

  # Determine image tag format
  image_tag = "$${github.sha}" # Use commit SHA as default

  # Base workflow content
  workflow_content = <<-EOT
name: ${var.instance.spec.workflow_name}

on:
  push:
    branches: [ ${var.instance.spec.branch_name} ]
  pull_request:
    branches: [ ${var.instance.spec.branch_name} ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK ${var.instance.spec.java_version}
      uses: actions/setup-java@v3
      with:
        java-version: '${var.instance.spec.java_version}'
        distribution: 'temurin'
        cache: maven
    
    - name: Build with Maven
      run: mvn -B package --file pom.xml
    
    - name: Test with Maven
      run: mvn test
    ${var.instance.spec.enable_sonarqube ? local.sonarqube_step : ""}
    ${var.instance.spec.enable_docker_build ? local.docker_build_step : ""}
    
    # Store the artifacts of the build
    - name: Archive production artifacts
      uses: actions/upload-artifact@v3
      with:
        name: target
        path: target
        retention-days: 5
EOT

  # SonarQube step
  sonarqube_step = <<-EOT
    
    - name: SonarQube Scan
      uses: sonarsource/sonarqube-scan-action@master
      env:
        SONAR_TOKEN: $${secrets.SONAR_TOKEN}
        SONAR_HOST_URL: $${secrets.SONAR_HOST_URL}
      with:
        args: >
          -Dsonar.projectKey=${var.instance.spec.sonarqube_project_key}
EOT

  # Docker build and push steps
  docker_build_step = <<-EOT
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Registry
      uses: docker/login-action@v2
      with:
        registry: ${var.instance.spec.docker_registry}
        username: $${secrets.DOCKER_USERNAME}
        password: $${secrets.DOCKER_PASSWORD}
    
    - name: Extract metadata (tags, labels) for Docker
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${var.instance.spec.docker_registry}/${var.instance.spec.docker_username}/${var.instance.spec.docker_image_name}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ${var.instance.spec.dockerfile_path}
        push: true
        tags: $${steps.meta.outputs.tags}
        labels: $${steps.meta.outputs.labels}
EOT
}

# Create a file documenting the GitHub secrets needed
resource "local_file" "github_secrets_readme" {
  filename = "${path.module}/github-secrets-README.md"
  content  = <<-EOT
# GitHub Secrets Required

This module requires the following GitHub secrets to be set up in your repository:

${local.secrets_list}

## How to Set Up GitHub Secrets

1. Navigate to your GitHub repository
2. Go to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with its name and value
  EOT
}
