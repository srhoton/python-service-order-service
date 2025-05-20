# S3 bucket for Lambda deployment packages

# Generate a random suffix for globally unique bucket name
resource "random_id" "lambda_bucket_suffix" {
  byte_length = 8
}

# Define the S3 bucket for Lambda deployment
resource "aws_s3_bucket" "lambda_deployment" {
  # Create a unique bucket name with environment and random suffix
  bucket = var.lambda_deployment_bucket_name != null ? var.lambda_deployment_bucket_name : "lambda-deployment-${var.service_name}-${var.environment}-${random_id.lambda_bucket_suffix.hex}"

  # Force destroy allows the bucket to be deleted even if it contains objects
  force_destroy = true

  tags = merge(
    local.common_tags,
    {
      Name = "Lambda Deployment Bucket"
    }
  )
}

# Enable versioning on the S3 bucket
resource "aws_s3_bucket_versioning" "lambda_deployment_versioning" {
  bucket = aws_s3_bucket.lambda_deployment.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for the S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_deployment_encryption" {
  bucket = aws_s3_bucket.lambda_deployment.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Set up public access block for the S3 bucket
resource "aws_s3_bucket_public_access_block" "lambda_deployment_public_access_block" {
  bucket = aws_s3_bucket.lambda_deployment.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure lifecycle rules to expire old Lambda deployment versions
resource "aws_s3_bucket_lifecycle_configuration" "lambda_deployment_lifecycle" {
  bucket = aws_s3_bucket.lambda_deployment.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    
    filter {
      prefix = ""  # Apply to all objects
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    expiration {
      expired_object_delete_marker = true
    }
  }
}