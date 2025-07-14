locals {
  # Generate bucket name if not provided
  bucket_name = var.instance.spec.bucket_name != null ? var.instance.spec.bucket_name : "${var.instance_name}-${var.environment.unique_name}"

  # Merge environment tags with user-defined tags
  bucket_tags = merge(
    var.environment.cloud_tags,
    var.instance.spec.tags,
    {
      Name        = local.bucket_name
      Environment = var.environment.name
      ManagedBy   = "facets"
    }
  )

  # KMS key configuration
  kms_key_id = var.instance.spec.encryption.kms_key_id != null ? var.instance.spec.encryption.kms_key_id : "alias/aws/s3"
}

# S3 Bucket
resource "aws_s3_bucket" "main" {
  bucket = local.bucket_name
  tags   = local.bucket_tags
}

# Bucket versioning configuration
resource "aws_s3_bucket_versioning" "main" {
  count  = var.instance.spec.versioning.enabled ? 1 : 0
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status     = "Enabled"
    mfa_delete = var.instance.spec.versioning.mfa_delete ? "Enabled" : "Disabled"
  }
}

# Bucket encryption configuration
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  count  = var.instance.spec.encryption.enabled ? 1 : 0
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = local.kms_key_id
      sse_algorithm     = var.instance.spec.encryption.kms_key_id != null ? "aws:kms" : "AES256"
    }
    bucket_key_enabled = var.instance.spec.encryption.kms_key_id != null ? true : false
  }
}

# Public access block configuration
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = var.instance.spec.public_access_block.block_public_acls
  block_public_policy     = var.instance.spec.public_access_block.block_public_policy
  ignore_public_acls      = var.instance.spec.public_access_block.ignore_public_acls
  restrict_public_buckets = var.instance.spec.public_access_block.restrict_public_buckets
}

# Lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count  = var.instance.spec.lifecycle_configuration.enabled ? 1 : 0
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "lifecycle_rule"
    status = "Enabled"

    # Transition to Infrequent Access
    dynamic "transition" {
      for_each = var.instance.spec.lifecycle_configuration.transition_to_ia_days > 0 ? [1] : []
      content {
        days          = var.instance.spec.lifecycle_configuration.transition_to_ia_days
        storage_class = "STANDARD_IA"
      }
    }

    # Transition to Glacier
    dynamic "transition" {
      for_each = var.instance.spec.lifecycle_configuration.transition_to_glacier_days > 0 ? [1] : []
      content {
        days          = var.instance.spec.lifecycle_configuration.transition_to_glacier_days
        storage_class = "GLACIER"
      }
    }

    # Expiration
    dynamic "expiration" {
      for_each = var.instance.spec.lifecycle_configuration.expiration_days > 0 ? [1] : []
      content {
        days = var.instance.spec.lifecycle_configuration.expiration_days
      }
    }
  }
}