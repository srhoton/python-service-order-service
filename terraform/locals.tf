locals {
  # Resource naming
  name_prefix   = "${var.service_name}-${var.environment}"
  function_name = "service-order-lambda-${var.environment}"

  # Default names for resources
  dynamodb_table_name = var.dynamodb_table_name != null ? var.dynamodb_table_name : "${local.name_prefix}-table"

  # Common tags
  common_tags = {
    Service     = var.service_name
    Environment = var.environment
  }


  # Lambda deployment
  # Removed unused variable: lambda_src_path = "${path.module}/../src"
  lambda_function_handler = "service_order_lambda.app.lambda_handler"
  lambda_s3_key           = "${var.lambda_s3_key_prefix}/function.zip"

  # Lambda environment variables
  lambda_environment_variables = {
    DYNAMODB_TABLE_NAME = local.dynamodb_table_name
    LOG_LEVEL           = "INFO"
  }
}