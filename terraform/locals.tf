locals {
  # Resource naming
  name_prefix     = "${var.service_name}-${var.environment}"
  function_name   = "service-order-lambda-${var.environment}"
  
  # Default names for resources
  dynamodb_table_name = var.dynamodb_table_name != null ? var.dynamodb_table_name : "${local.name_prefix}-table"
  lambda_deployment_bucket_name = var.lambda_deployment_bucket_name != null ? var.lambda_deployment_bucket_name : "${local.name_prefix}-deployment-${random_string.suffix.result}"
  
  # Common tags
  common_tags = {
    Service     = var.service_name
    Environment = var.environment
  }
  
  # AppConfig values
  appconfig_content = jsonencode({
    serviceOrderTableName = local.dynamodb_table_name
  })
  
  # Lambda deployment
  lambda_src_path      = "${path.module}/../src"
  lambda_function_handler = "service_order_lambda.app.lambda_handler"
  
  # Lambda environment variables
  lambda_environment_variables = {
    APPCONFIG_APPLICATION_ID          = aws_appconfig_application.service_order.id
    APPCONFIG_ENVIRONMENT_ID          = aws_appconfig_environment.service_order.id
    APPCONFIG_CONFIGURATION_PROFILE_ID = aws_appconfig_configuration_profile.service_order.id
    LOG_LEVEL                         = "INFO"
  }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}