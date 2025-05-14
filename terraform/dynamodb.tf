resource "aws_dynamodb_table" "service_order" {
  name         = local.dynamodb_table_name
  billing_mode = var.dynamodb_billing_mode

  # Only set capacity if using PROVISIONED billing mode
  read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
  write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null

  # Primary key structure: PK = service order ID (UUID), SK = customer ID
  hash_key  = "PK"
  range_key = "SK"

  # Attribute definitions
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # Global Secondary Index for querying by customer ID
  global_secondary_index {
    name            = "CustomerIndex"
    hash_key        = "SK"
    projection_type = "ALL"
    
    # Only set capacity if using PROVISIONED billing mode
    read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
    write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
  }

  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  # TTL specification - not enabled by default
  ttl {
    enabled        = false
    attribute_name = "TTL"
  }

  # Stream specification - enable for integrations if needed
  stream_enabled   = false
  stream_view_type = null

  # Apply tags for better resource management
  tags = merge(
    local.common_tags,
    {
      Name = "ServiceOrderTable"
    }
  )
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for service orders"
  value       = aws_dynamodb_table.service_order.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for service orders"
  value       = aws_dynamodb_table.service_order.arn
}