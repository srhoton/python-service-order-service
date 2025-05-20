# Lambda function and related resources

# Create a data source to track Lambda source code changes
data "archive_file" "lambda_source_hash" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/.source_hash.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

# Calculate the Lambda package hash based on source code and dependencies
locals {
  source_hash          = data.archive_file.lambda_source_hash.output_base64sha256
  dependencies_hash    = fileexists("${path.module}/../requirements.txt") ? filebase64sha256("${path.module}/../requirements.txt") : ""
  lambda_hash          = base64sha256("${local.source_hash}-${local.dependencies_hash}")
  lambda_zip_path      = "${path.module}/lambda_function.zip"
  lambda_package_built = fileexists(local.lambda_zip_path)
}

# Create a resource that will trigger the Lambda package build
resource "null_resource" "lambda_builder" {
  # Rebuild when source code or dependencies change
  triggers = {
    source_code_hash  = local.source_hash
    dependencies_hash = local.dependencies_hash
    lambda_hash       = local.lambda_hash
    # Force rebuilds when needed by changing this value
    force_rebuild = "2"
  }

  # Build the Lambda package before trying to upload it
  provisioner "local-exec" {
    command = <<-EOT
      echo "Starting Lambda package build at $(date)"
      
      # Define build directory
      BUILD_DIR="${path.module}/build"
      ZIP_FILE="${path.module}/lambda_function.zip"
      
      # Clean any previous build artifacts
      echo "Cleaning previous build artifacts..."
      rm -rf "$BUILD_DIR"
      rm -f "$ZIP_FILE"
      mkdir -p "$BUILD_DIR"
      
      # Copy source code
      echo "Copying source code..."
      cp -r "${path.module}/../src/"* "$BUILD_DIR/"
      
      # Clean any Python cache files
      echo "Cleaning Python cache files..."
      find "$BUILD_DIR" -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
      find "$BUILD_DIR" -name "*.pyc" -delete 2>/dev/null || true
      
      # Install dependencies with pip
      echo "Installing dependencies..."
      pip install --no-cache-dir -r "${path.module}/../requirements.txt" --target "$BUILD_DIR" --upgrade
      
      # List the build directory contents
      echo "Build directory contents:"
      ls -la "$BUILD_DIR"
      ls -la "$BUILD_DIR/service_order_lambda" || echo "service_order_lambda directory not found!"
      
      # Verify required modules exist
      if [ ! -f "$BUILD_DIR/service_order_lambda/app.py" ]; then
        echo "ERROR: app.py not found in build"
        exit 1
      fi
      
      # Create the zip file
      echo "Creating Lambda zip package..."
      cd "$BUILD_DIR" && zip -r "$ZIP_FILE" .
      
      # Verify the zip file was created
      if [ ! -f "$ZIP_FILE" ]; then
        echo "ERROR: Failed to create zip file"
        exit 1
      fi
      
      # Check zip file contents
      echo "Zip file created: $(du -h "$ZIP_FILE" | cut -f1)"
      
      echo "Lambda package build completed at $(date)"
      
      # Upload to S3 directly to ensure it exists before Terraform tries to reference it
      echo "Uploading Lambda package to S3..."
      aws s3 cp "$ZIP_FILE" "s3://${aws_s3_bucket.lambda_deployment.bucket}/${var.lambda_s3_key_prefix}/function.zip"
    EOT
  }

  depends_on = [
    aws_s3_bucket.lambda_deployment,
    aws_s3_bucket_versioning.lambda_deployment_versioning
  ]
}

# Reference the S3 object for the Lambda package
resource "aws_s3_object" "lambda_package" {
  bucket = aws_s3_bucket.lambda_deployment.bucket
  key    = "${var.lambda_s3_key_prefix}/function.zip"
  source = local.lambda_zip_path
  etag   = fileexists(local.lambda_zip_path) ? filemd5(local.lambda_zip_path) : null

  # Only try to upload the package if it's been built
  count = local.lambda_package_built ? 1 : 0

  depends_on = [
    null_resource.lambda_builder,
    aws_s3_bucket.lambda_deployment
  ]
}

# Lambda function resource
resource "aws_lambda_function" "service_order" {
  function_name = local.function_name
  description   = "Service Order Lambda function"

  # Use S3 for Lambda deployment package
  s3_bucket        = aws_s3_bucket.lambda_deployment.bucket
  s3_key           = "${var.lambda_s3_key_prefix}/function.zip"
  source_code_hash = local.lambda_hash

  runtime     = var.lambda_runtime
  handler     = local.lambda_function_handler
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  role = aws_iam_role.lambda_execution.arn

  environment {
    variables = local.lambda_environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
    null_resource.lambda_builder
  ]

  # Prevent unnecessary updates
  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.function_name
    }
  )
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# IAM Role and Policy for Lambda
resource "aws_iam_role" "lambda_execution" {
  name = "${local.function_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "lambda_permissions" {
  name        = "${local.function_name}-policy"
  description = "Policy for Service Order Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.lambda_logs.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.service_order.arn,
          "${aws_dynamodb_table.service_order.arn}/index/*"
        ]
      },

      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.lambda_deployment.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_permissions.arn
}
