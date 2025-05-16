locals {
  output_interfaces = {}
  output_attributes = {
    bucket_name   = aws_s3_bucket.this.id
    bucket_arn    = aws_s3_bucket.this.arn
    bucket_region = aws_s3_bucket.this.region
  }
}