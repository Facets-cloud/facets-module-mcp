locals {
  output_attributes = {
    bucket_name                 = aws_s3_bucket.main.bucket
    bucket_id                   = aws_s3_bucket.main.id
    bucket_arn                  = aws_s3_bucket.main.arn
    bucket_domain_name          = aws_s3_bucket.main.bucket_domain_name
    bucket_regional_domain_name = aws_s3_bucket.main.bucket_regional_domain_name
    bucket_hosted_zone_id       = aws_s3_bucket.main.hosted_zone_id
    bucket_region               = aws_s3_bucket.main.region
    tags                        = aws_s3_bucket.main.tags_all
    access_logs_bucket_name     = "null"
    access_logs_bucket_arn      = "null"
    versioning_enabled          = var.instance.spec.versioning.enabled
    encryption_enabled          = var.instance.spec.encryption.enabled
    kms_key_id                  = var.instance.spec.encryption.kms_key_id
    lifecycle_enabled           = var.instance.spec.lifecycle_configuration.enabled
  }
  output_interfaces = {
  }
}