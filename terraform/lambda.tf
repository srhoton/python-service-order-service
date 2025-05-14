resource "aws_lambda_function" "service_order" {
  function_name = local.function_name
  description   = "Service Order Lambda function"
  
  s3_bucket = aws_s3_bucket.lambda_deployment.id
  s3_key    = aws_s3_object.lambda_package.key
  
  runtime     = var.lambda_runtime
  handler     = local.lambda_function_handler
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  
  role = aws_iam_role.lambda_execution.arn
  
  environment {
    variables = local.lambda_environment_variables
  }
  
  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]
  
  tags = merge(
    local.common_tags,
    {
      Name = local.function_name
    }
  )
}

# Lambda deployment package
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = local.lambda_src_path
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_s3_object" "lambda_package" {
  bucket = aws_s3_bucket.lambda_deployment.id
  key    = "lambda/${local.function_name}/${filesha256(data.archive_file.lambda_package.output_path)}.zip"
  source = data.archive_file.lambda_package.output_path
  
  etag = filemd5(data.archive_file.lambda_package.output_path)
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
          "appconfig:GetConfiguration",
          "appconfig:StartConfigurationSession"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_permissions.arn
}

# Outputs
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.service_order.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.service_order.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_function.service_order.invoke_arn
}