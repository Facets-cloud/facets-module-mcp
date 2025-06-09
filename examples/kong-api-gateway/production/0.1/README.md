# Kong API Gateway - Production Module

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](./facets.yaml)
[![Kubernetes](https://img.shields.io/badge/kubernetes-compatible-green.svg)](./facets.yaml)

## Reference

**Chat Link**
https://claude.ai/share/a1794ff0-3890-4159-970d-3a072a99b78c

This module creates a production-ready Kong API Gateway deployment for Kubernetes environments with secure defaults, SSL termination, rate limiting, and authentication capabilities.

## Overview

This module deploys Kong API Gateway 3.4 as a scalable, secure, and production-ready solution on Kubernetes. It provides comprehensive API management capabilities including authentication, rate limiting, CORS handling, and monitoring integration without any cloud provider dependencies or Kong Custom Resource Definitions (CRDs).

The module uses Kong's Admin API for plugin configuration, making it compatible with any Kubernetes cluster without requiring Kong Ingress Controller or Kong CRDs. Key features include:
- **Pure Kubernetes** - No cloud provider specific features
- **Database flexible** - Supports both PostgreSQL and DB-less modes

## Environment as Dimension

This module is environment-aware and adapts its configuration based on the target environment:

- **Namespace isolation**: Each environment deploys Kong in its own namespace
- **Resource scaling**: Production environments typically use higher replica counts and resource limits
- **Monitoring levels**: Different log levels and monitoring configurations per environment
- **Security policies**: Environment-specific security configurations and access controls
- **TLS/SSL settings**: Cert-manager integration varies by environment setup

The module uses `var.environment` to:
- Apply environment-specific cloud tags and labels
- Generate unique resource names using `environment.unique_name`
- Configure environment-appropriate defaults for monitoring and logging

## Resources Created

The module creates and manages the following Kubernetes resources:

- **Namespace** - Dedicated Kong namespace with proper labeling
- **Deployment** - Kong gateway pods with security contexts and resource limits
- **Services** - ClusterIP services for proxy, admin, and status endpoints
- **Ingress** - Standard Kubernetes ingress for external access (optional)
- **NodePort Service** - Alternative external access when ingress is disabled
- **ConfigMaps** - Kong configuration and plugin setup scripts
- **Secret** - PostgreSQL credentials (when database mode is postgres)
- **ServiceAccount** - Pod identity with minimal required permissions
- **ClusterRole/ClusterRoleBinding** - RBAC for Kong operations
- **PodDisruptionBudget** - High availability during cluster operations
- **HorizontalPodAutoscaler** - Automatic scaling based on CPU/memory metrics
- **ServiceMonitor** - Prometheus metrics collection (when monitoring enabled)

## Plugin Configuration

This module configures Kong plugins through the Admin API without requiring Kong CRDs:

- **Rate Limiting** - Configurable requests per minute limits
- **CORS** - Cross-origin resource sharing with customizable origins
- **Request Size Limiting** - Maximum request payload size control
- **Bot Detection** - Automated bot detection and blocking
- **Prometheus** - Metrics collection for monitoring
- **Authentication** - Key-auth, JWT, and OAuth2 support (service-level configuration)

## Security Considerations

This module implements several security best practices:

- **Non-root containers** - Kong runs as non-root user (1000) with dropped capabilities
- **Read-only root filesystem** - Prevents runtime modifications to container filesystem
- **Security contexts** - Proper pod and container security contexts applied
- **Resource limits** - CPU and memory limits prevent resource exhaustion
- **Network policies** - ClusterIP services by default for internal communication
- **Secret management** - Database credentials managed via Kubernetes secrets
- **Plugin security** - Bot detection, request size limiting, and IP restriction available
- **RBAC** - Minimal required permissions for Kong service account
- **TLS support** - SSL/TLS termination with cert-manager integration
- **No CRD dependency** - Uses Admin API for configuration, reducing attack surface

## Compatibility

- **Kubernetes 1.20+** - Compatible with modern Kubernetes clusters
- **No Kong CRDs required** - Works without Kong Ingress Controller
- **Pure Kubernetes** - No cloud provider specific features
- **Database flexible** - Supports both PostgreSQL and DB-less modes
