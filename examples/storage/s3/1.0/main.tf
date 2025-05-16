terraform {
  required_version = ">= 1.5.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}

# Local variables for configuration
locals {
  bucket_name = lower("${var.instance.spec.bucket_name_prefix}-${var.environment.unique_name}-${var.instance_name}")

  # Define lifecycle configuration based on storage_type
  lifecycle_rules = {
    short_term = [
      {
        id      = "short-term-lifecycle"
        enabled = true

        transition = [
          {
            days          = 30
            storage_class = "STANDARD_IA"
          },
          {
            days          = 60
            storage_class = "GLACIER"
          }
        ]

        expiration = {
          days = 90
        }
      }
    ],
    long_term = [
      {
        id      = "long-term-lifecycle"
        enabled = true

        transition = [
          {
            days          = 90
            storage_class = "STANDARD_IA"
          },
          {
            days          = 180
            storage_class = "GLACIER"
          },
          {
            days          = 365
            storage_class = "DEEP_ARCHIVE"
          }
        ]

        expiration = {
          days = 2555 # ~7 years
        }
      }
    ],
    compliance = [
      {
        id      = "compliance-lifecycle"
        enabled = true

        transition = [
          {
            days          = 90
            storage_class = "STANDARD_IA"
          },
          {
            days          = 180
            storage_class = "GLACIER"
          },
          {
            days          = 365
            storage_class = "DEEP_ARCHIVE"
          }
        ]

        # No expiration for compliance storage
        noncurrent_version_transition = [
          {
            days          = 30
            storage_class = "STANDARD_IA"
          },
          {
            days          = 60
            storage_class = "GLACIER"
          },
          {
            days          = 180
            storage_class = "DEEP_ARCHIVE"
          }
        ]
      },
      {
        id      = "compliance-delete-markers"
        enabled = true

        expiration = {
          expired_object_delete_marker = true
        }
      }
    ]
  }

  # Select the appropriate lifecycle rules based on storage_type
  selected_lifecycle_rules = local.lifecycle_rules[var.instance.spec.storage_type]

  # Tags based on environment and storage type
  tags = merge(var.environment.cloud_tags, {
    Name        = local.bucket_name
    StorageType = var.instance.spec.storage_type
    CreatedBy   = "Facets"
  })

  # Create a logging bucket if compliance storage is selected
  create_logging_bucket = var.instance.spec.storage_type == "compliance"
  logging_bucket_name   = "${local.bucket_name}-logs"
}

# Create S3 logging bucket if compliance storage is selected
resource "aws_s3_bucket" "logging_bucket" {
  count  = local.create_logging_bucket ? 1 : 0
  bucket = local.logging_bucket_name
  tags   = merge(local.tags, { Purpose = "AccessLogs" })
}

resource "aws_s3_bucket_ownership_controls" "logging_bucket_ownership" {
  count  = local.create_logging_bucket ? 1 : 0
  bucket = aws_s3_bucket.logging_bucket[0].id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "logging_bucket_acl" {
  count      = local.create_logging_bucket ? 1 : 0
  depends_on = [aws_s3_bucket_ownership_controls.logging_bucket_ownership]

  bucket = aws_s3_bucket.logging_bucket[0].id
  acl    = "log-delivery-write"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logging_bucket_encryption" {
  count  = local.create_logging_bucket ? 1 : 0
  bucket = aws_s3_bucket.logging_bucket[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logging_bucket_public_access" {
  count  = local.create_logging_bucket ? 1 : 0
  bucket = aws_s3_bucket.logging_bucket[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create main S3 bucket
resource "aws_s3_bucket" "this" {
  bucket = local.bucket_name
  tags   = local.tags
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.instance.spec.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = local.selected_lifecycle_rules

    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "transition" {
        for_each = lookup(rule.value, "transition", [])

        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = lookup(rule.value, "expiration", null) != null ? [rule.value.expiration] : []

        content {
          days                         = lookup(expiration.value, "days", null)
          expired_object_delete_marker = lookup(expiration.value, "expired_object_delete_marker", null)
        }
      }

      dynamic "noncurrent_version_transition" {
        for_each = lookup(rule.value, "noncurrent_version_transition", [])

        content {
          noncurrent_days = noncurrent_version_transition.value.days
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure bucket logging
resource "aws_s3_bucket_logging" "this" {
  count  = local.create_logging_bucket ? 1 : 0
  bucket = aws_s3_bucket.this.id

  target_bucket = aws_s3_bucket.logging_bucket[0].id
  target_prefix = "log/"
}

# Configure bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}