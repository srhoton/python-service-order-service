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

# AppConfig outputs
output "appconfig" {
  description = "Information about the AppConfig configuration"
  value = {
    application_id    = aws_appconfig_application.service_order.id
    environment_id    = aws_appconfig_environment.service_order.environment_id
    config_profile_id = aws_appconfig_configuration_profile.service_order.configuration_profile_id
  }
}

# S3 outputs
output "lambda_deployment_bucket" {
  description = "Information about the Lambda deployment S3 bucket"
  value = {
    name = aws_s3_bucket.lambda_deployment.id
    arn  = aws_s3_bucket.lambda_deployment.arn
  }
}
