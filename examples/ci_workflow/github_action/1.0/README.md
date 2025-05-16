# GitHub Actions CI Workflow for Java Maven

## Chat Link
https://claude.ai/share/2ebe981f-48f4-4648-881e-4929ebbf0f59

This module creates a GitHub Actions workflow for building, testing, and optionally analyzing Java Maven applications. It also includes options for Docker container builds and registry publishing.

## Overview

The module generates a GitHub workflow YAML file configured for Java Maven applications with the following capabilities:
- Building and testing Java applications using Maven
- Configurable Java version (8, 11, 17, or 21)
- Optional SonarQube static code analysis integration
- Optional Docker image build and push to container registry
- GitHub Secrets management for sensitive values
- Artifact archiving

## Environment as Dimension

This module maintains consistency across environments through:
- Environment-aware naming conventions
- Consistent workflow configuration regardless of environment
- Environment metadata captured in the workflow

## Resources Created

- **GitHub Actions Workflow**: Creates a YAML workflow file that can be added to a specified branch in a GitHub repository
- **GitHub Secrets Documentation**: Generates a README file with instructions for setting up required secrets
- **CI Pipeline Steps**: Configures build, test, code analysis, and container publishing steps based on provided options

## Security Considerations

- All sensitive information is stored as GitHub Secrets
- SonarQube integration uses repository secrets for secure token storage
- Docker registry credentials are stored as GitHub Secrets
- No sensitive data is stored in the workflow file itself
