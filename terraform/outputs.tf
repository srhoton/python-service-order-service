# Service Order Lambda - Terraform Outputs

output "aws_region" {
  description = "The AWS region resources are deployed to"
  value       = var.aws_region
}

output "environment" {
  description = "The environment resources are deployed to"
  value       = var.environment
}

# DynamoDB outputs
output "service_order_table" {
  description = "Information about the DynamoDB service order table"
  value = {
    name = aws_dynamodb_table.service_order.name
    arn  = aws_dynamodb_table.service_order.arn
    id   = aws_dynamodb_table.service_order.id
  }
}

# Lambda outputs
output "lambda_function" {
  description = "Information about the Service Order Lambda function"
  value = {
    name          = aws_lambda_function.service_order.function_name
    arn           = aws_lambda_function.service_order.arn
    invoke_arn    = aws_lambda_function.service_order.invoke_arn
    version       = aws_lambda_function.service_order.version
    last_modified = aws_lambda_function.service_order.last_modified
  }
}

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

# API Gateway outputs
output "api_gateway" {
  description = "Information about the API Gateway endpoints"
  value = {
    endpoint      = aws_apigatewayv2_api.service_order_api.api_endpoint
    id            = aws_apigatewayv2_api.service_order_api.id
    stage_name    = aws_apigatewayv2_stage.default.name
    execution_arn = aws_apigatewayv2_api.service_order_api.execution_arn
  }
}

# AppConfig outputs removed - using environment variables instead

# S3 Bucket outputs
output "lambda_deployment_bucket" {
  description = "Name of the S3 bucket used for Lambda deployment packages"
  value       = aws_s3_bucket.lambda_deployment.bucket
}

output "lambda_deployment_bucket_arn" {
  description = "ARN of the S3 bucket used for Lambda deployment packages"
  value       = aws_s3_bucket.lambda_deployment.arn
}

# Deployment outputs completed
