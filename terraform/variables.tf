variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (e.g. dev, test, prod)"
  type        = string
  default     = "dev"
}

variable "service_name" {
  description = "Name of the service, used for resource naming"
  type        = string
  default     = "service-order"
}

# AppConfig variables have been removed
# The Lambda function now uses environment variables directly instead of AppConfig


# DynamoDB variables
variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for service orders"
  type        = string
  default     = null
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.dynamodb_billing_mode)
    error_message = "Billing mode must be either PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (only used with PROVISIONED billing mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (only used with PROVISIONED billing mode)"
  type        = number
  default     = 5
}

# Lambda variables
variable "lambda_runtime" {
  description = "Runtime for the Lambda function"
  type        = string
  default     = "python3.13"
}

variable "lambda_memory_size" {
  description = "Memory size for the Lambda function in MB"
  type        = number
  default     = 256
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 MB and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Timeout for the Lambda function in seconds"
  type        = number
  default     = 30
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_log_retention_days" {
  description = "Number of days to retain Lambda function logs"
  type        = number
  default     = 14
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.lambda_log_retention_days)
    error_message = "Lambda log retention days must be one of: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653."
  }
}

# API Gateway variables
variable "api_gateway_throttling_rate_limit" {
  description = "API Gateway rate limit (requests per second)"
  type        = number
  default     = 50
  validation {
    condition     = var.api_gateway_throttling_rate_limit > 0
    error_message = "API Gateway throttling rate limit must be greater than 0."
  }
}

variable "api_gateway_throttling_burst_limit" {
  description = "API Gateway burst limit (concurrent requests)"
  type        = number
  default     = 100
  validation {
    condition     = var.api_gateway_throttling_burst_limit > 0
    error_message = "API Gateway throttling burst limit must be greater than 0."
  }
}

# S3 bucket variables for Lambda deployment
variable "lambda_deployment_bucket_name" {
  description = "Name of the S3 bucket for Lambda deployment packages (optional, will be generated if not provided)"
  type        = string
  default     = null
}

variable "lambda_s3_key_prefix" {
  description = "Prefix for Lambda deployment package S3 keys"
  type        = string
  default     = "lambda/service-order-lambda"
}