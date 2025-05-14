variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
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

# AppConfig variables
variable "appconfig_application_name" {
  description = "Name of the AppConfig application"
  type        = string
  default     = "service-order-application"
}

variable "appconfig_environment_name" {
  description = "Name of the AppConfig environment"
  type        = string
  default     = "default"
}

variable "appconfig_configuration_profile_name" {
  description = "Name of the AppConfig configuration profile"
  type        = string
  default     = "service-order-config"
}

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
}

variable "lambda_timeout" {
  description = "Timeout for the Lambda function in seconds"
  type        = number
  default     = 30
}

variable "lambda_log_retention_days" {
  description = "Number of days to retain Lambda function logs"
  type        = number
  default     = 14
}

# S3 variables
variable "lambda_deployment_bucket_name" {
  description = "Name of the S3 bucket to store Lambda deployment packages"
  type        = string
  default     = null
}