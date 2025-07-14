# Secure S3 Bucket Module for Banking

## Chat Link
https://claude.ai/share/9d08f644-10c8-4080-b159-98f5320aa99e

This module provisions an AWS S3 bucket with secure defaults and configurable lifecycle policies for banking industry compliance.

## Features

- Secure by default: Server-side encryption, public access blocking, proper bucket ownership
- Simplified lifecycle policies through predefined storage types
- Compliant with banking industry security standards
- Developer-friendly interface with minimal configuration options

## Usage

```yaml
kind: storage
flavor: s3
version: "1.0"
spec:
  bucket_name_prefix: "bank"       # Prefix for bucket name
  storage_type: "compliance"       # Options: short_term, long_term, compliance
  enable_versioning: true          # Toggle bucket versioning
```

## Required Inputs

- `aws_provider`: An AWS provider from another module (typically a cloud_account module)

## Storage Types

The module supports three predefined storage configurations:

### short_term (90-day retention)
- Transitions to Standard-IA after 30 days
- Transitions to Glacier after 60 days
- Deletes objects after 90 days
- Good for: Temporary data, processing outputs, logs

### long_term (7-year retention)
- Transitions to Standard-IA after 90 days
- Transitions to Glacier after 180 days
- Transitions to Deep Archive after 365 days
- Deletes objects after 7 years (2555 days)
- Good for: Financial records, transaction data

### compliance (Indefinite retention)
- Full versioning with appropriate transitions
- Automatically creates and configures a logging bucket
- Never expires objects
- Advanced security controls
- Good for: Compliance data, audit evidence, legal documentation

## Security Controls

The module automatically implements these security features:

- Server-side encryption with AES256
- Complete public access blocking
- Object ownership controls
- Access logging (for compliance storage)
- Secure bucket naming

## Outputs

- `bucket_name`: The name of the created S3 bucket
- `bucket_arn`: The ARN of the created S3 bucket
- `bucket_region`: The region where the bucket is created

## Examples

### Basic Usage

```yaml
kind: storage
flavor: s3
version: "1.0"
spec:
  bucket_name_prefix: "bank"
  storage_type: "compliance"
  enable_versioning: true
```

### Short-term Storage Without Versioning

```yaml
kind: storage
flavor: s3
version: "1.0"
spec:
  bucket_name_prefix: "temp"
  storage_type: "short_term"
  enable_versioning: false
```

## Terraform Resources Created

- AWS S3 Bucket with secure configuration
- Access logging bucket (for compliance storage)
- Lifecycle rules based on storage type
- Resource policies for security
