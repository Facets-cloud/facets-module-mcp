# AWS EC2 Module

This module provisions an AWS EC2 instance with comprehensive configuration options for compute, storage, networking, IAM, and security.

## Overview

The AWS EC2 module creates a highly configurable compute instance, along with all necessary supporting resources:

- EC2 instance with customizable instance type and AMI
- Root volume with required size and type specification
- Optional additional EBS volumes with explicit configuration
- IAM role and instance profile (existing or new)
- Custom security groups with flexible ingress and egress rules
- SSH key pair (generated or existing)
- Custom tags with key-value pairs
- Instance tagging and metadata

## Environment as Dimension

This module adapts to different environments by:

- Creating unique resource names using environment identifiers
- Applying environment-specific tags to all resources
- Supporting environment-specific security group rules
- Allowing custom user data scripts that can adapt to environments

## Resources Created

- **AWS EC2 Instance**: The main compute resource
- **Security Group**: Controls network access to the instance
- **SSH Key Pair**: Generated (if not specified) for SSH access
- **EBS Volumes**: Root volume and optional additional volumes
- **Volume Attachments**: For connecting additional volumes
- **IAM Role** (Optional): For instance permissions
- **IAM Policy** (Optional): Custom policy for the instance
- **IAM Instance Profile** (Optional): For attaching role to instance

## Security Considerations

- Root and additional EBS volumes are encrypted by default
- SSH access is always enabled on port 22 by default for security management
- Security group rules are fully customizable (except for SSH on port 22)
- IAM instance profile can be configured with least privilege
- Custom SSH key pair can be specified

## Configurability

This module supports extensive customization, including:

### Compute Configuration
- **Instance Type**: EC2 instance type (t3.micro, m5.large, etc.) - Required
- **AMI ID**: Custom AMI or default Amazon Linux 2
- **Root Volume**:
  - **Size**: Size in GB (8-16384) - Required
  - **Type**: Volume type (gp2, gp3, io1, etc.) - Required
- **Additional EBS Volumes**: Optional data volumes with explicit configuration:
  - **Device Name**: The device path - Required when enabled
  - **Size**: Volume size in GB - Required when enabled
  - **Type**: Volume type - Required when enabled
  - **Encryption**: Enable/disable encryption (default: true)

### IAM Configuration
- **Instance Profile Options**:
  - Use no instance profile
  - Use an existing instance profile by name
  - Create a new instance profile with IAM role and custom policy
- **Policy Document**: JSON policy to attach to the IAM role

### Security Group Configuration
- **SSH Access**: (Always enabled for port 22)
  - Configure source CIDR blocks for SSH (default: 0.0.0.0/0)
  - Specify existing key pair or generate new one
- **Custom Ingress Rules**:
  - Define additional ingress rules with ports, protocols, and CIDR blocks
  - Support for TCP, UDP, ICMP, and all traffic (-1)
  - Note: SSH on port 22 is always configured separately and doesn't need to be included in custom rules
- **Custom Egress Rules**:
  - Restrict default "allow all" egress if needed
  - Define custom egress rules to specific destinations

### Networking and Instance Configuration
- **Public IP Association**: Enable/disable public IP assignment
- **Detailed Monitoring**: Enable/disable enhanced CloudWatch monitoring
- **Custom Hostname**: Set instance hostname
- **User Data Script**: Custom initialization script

### Tagging Configuration
- **Custom Tags**: Define any number of custom tags with key-value pairs
  - Example:
    ```
    tags:
      tag1:
        key: environment
        value: "production"
      tag2:
        key: app
        value: "myapp"
      custom_tag:
        key: owner
        value: "team-name"
    ```

## AWS Architecture Notes

This module follows AWS architectural best practices:

1. **Storage Configuration**:
   - Root volume size and type are required fields to ensure explicit configuration
   - Additional volume parameters are required when enabled
   - All volumes are encrypted by default for security

2. **IAM Role and Instance Profile Relationship**:
   - IAM roles contain permission policies
   - Instance profiles are containers for IAM roles
   - EC2 instances use instance profiles to assume IAM roles
   - When creating a new instance profile, a corresponding IAM role is always created

3. **Security Best Practices**:
   - SSH access is always available for management but can be restricted to specific CIDR blocks
   - Security group rules follow principle of least privilege by default

## Outputs

The module provides comprehensive outputs for integration with other systems:

- **Instance**: ID, public/private IPs, hostname
- **Network**: VPC ID, subnet ID
- **SSH Access**: Connection details including private key (if generated)
- **IAM**: Role name and instance profile (if created)
- **Instance Details**: Type, volume info, security group ID
- **Custom Tags**: All custom tags applied to the instance
