# AWS S3 Bucket Module

![Terraform](https://img.shields.io/badge/terraform-v1.5.7-blue) ![AWS](https://img.shields.io/badge/provider-aws-orange)

## Overview

This module creates and configures an AWS S3 bucket with comprehensive security and lifecycle management capabilities. It provides developer-friendly configuration options while maintaining security best practices through sensible defaults.

## Environment as Dimension

The module is environment-aware and will automatically incorporate environment-specific naming and tagging:

- **Bucket naming**: If no custom bucket name is provided, the module generates a unique name using `instance_name` and `environment.unique_name`
- **Tagging**: Environment-specific cloud tags are automatically applied alongside user-defined tags
- **Configuration consistency**: All settings remain consistent across environments unless explicitly overridden

## Resources Created

- **S3 Bucket**: Primary storage bucket with configurable naming
- **Versioning Configuration**: Optional object versioning with MFA delete protection
- **Server-Side Encryption**: Configurable encryption using AWS managed keys or customer-managed KMS keys
- **Public Access Block**: Security controls to prevent accidental public exposure
- **Lifecycle Configuration**: Optional automated object lifecycle management with transitions to IA and Glacier storage classes

## Security Considerations

This module implements security best practices by default:

- **Public access blocking**: All public access controls are enabled by default to prevent accidental exposure
- **Encryption**: Server-side encryption is enabled by default using AWS managed S3 keys
- **Versioning**: Available for data protection and compliance requirements
- **MFA delete**: Optional multi-factor authentication requirement for permanent deletions
- **Lifecycle management**: Helps optimize storage costs and manage data retention

The module follows the principle of secure by default, requiring explicit configuration to reduce security controls. All public access settings default to maximum restriction, and encryption is automatically enabled.

## Configuration Options

### Bucket Naming
Configure custom bucket names with automatic validation for AWS naming requirements, or allow automatic generation based on instance and environment context.

### Versioning Management
Enable object versioning for data protection and compliance. Optional MFA delete provides additional protection against accidental or malicious deletions.

### Encryption Settings
Choose between AWS managed S3 encryption or customer-managed KMS keys. Encryption is enabled by default for data protection.

### Lifecycle Policies
Configure automated transitions to reduce storage costs:
- Standard to Infrequent Access storage
- Infrequent Access to Glacier storage  
- Automatic expiration for data retention compliance

### Access Controls
Comprehensive public access blocking ensures buckets remain private by default. All four public access controls can be individually configured but default to maximum security.