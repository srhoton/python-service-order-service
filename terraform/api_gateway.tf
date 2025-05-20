# API Gateway for Service Order Lambda
resource "aws_apigatewayv2_api" "service_order_api" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
  description   = "HTTP API for Service Order Lambda"

  cors_configuration {
    allow_origins = ["*"]
    allow_headers = ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    max_age       = 300
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-api"
    }
  )
}

# Default stage for the API Gateway
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.service_order_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      requestTime        = "$context.requestTime"
      httpMethod         = "$context.httpMethod"
      routeKey           = "$context.routeKey"
      status             = "$context.status"
      protocol           = "$context.protocol"
      responseLength     = "$context.responseLength"
      userAgent          = "$context.identity.userAgent"
      integrationLatency = "$context.integrationLatency"
      latency            = "$context.responseLatency"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.api_gateway_throttling_burst_limit
    throttling_rate_limit  = var.api_gateway_throttling_rate_limit
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-default-stage"
    }
  )
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${local.name_prefix}-api"
  retention_in_days = var.lambda_log_retention_days
  tags              = local.common_tags
}

# Lambda integration
resource "aws_apigatewayv2_integration" "service_order_lambda" {
  api_id                 = aws_apigatewayv2_api.service_order_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.service_order.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

# Routes for CRUD operations
# POST - Create a service order
resource "aws_apigatewayv2_route" "create_service_order" {
  api_id    = aws_apigatewayv2_api.service_order_api.id
  route_key = "POST /customers/{customerId}/service-orders"
  target    = "integrations/${aws_apigatewayv2_integration.service_order_lambda.id}"
}

# GET - List all service orders for a customer
resource "aws_apigatewayv2_route" "list_service_orders" {
  api_id    = aws_apigatewayv2_api.service_order_api.id
  route_key = "GET /customers/{customerId}/service-orders"
  target    = "integrations/${aws_apigatewayv2_integration.service_order_lambda.id}"
}

# GET - Get a specific service order
resource "aws_apigatewayv2_route" "get_service_order" {
  api_id    = aws_apigatewayv2_api.service_order_api.id
  route_key = "GET /customers/{customerId}/service-orders/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.service_order_lambda.id}"
}

# PUT - Update a service order
resource "aws_apigatewayv2_route" "update_service_order" {
  api_id    = aws_apigatewayv2_api.service_order_api.id
  route_key = "PUT /customers/{customerId}/service-orders/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.service_order_lambda.id}"
}

# DELETE - Delete a service order
resource "aws_apigatewayv2_route" "delete_service_order" {
  api_id    = aws_apigatewayv2_api.service_order_api.id
  route_key = "DELETE /customers/{customerId}/service-orders/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.service_order_lambda.id}"
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.service_order.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.service_order_api.execution_arn}/*/*"
}

