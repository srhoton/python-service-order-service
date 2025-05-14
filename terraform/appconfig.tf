resource "aws_appconfig_application" "service_order" {
  name        = var.appconfig_application_name
  description = "Application configuration for Service Order Lambda"

  tags = merge(
    local.common_tags,
    {
      Name = var.appconfig_application_name
    }
  )
}

resource "aws_appconfig_environment" "service_order" {
  name           = var.appconfig_environment_name
  description    = "Environment for Service Order Lambda configuration"
  application_id = aws_appconfig_application.service_order.id

  tags = merge(
    local.common_tags,
    {
      Name = var.appconfig_environment_name
    }
  )
}

resource "aws_appconfig_configuration_profile" "service_order" {
  name           = var.appconfig_configuration_profile_name
  description    = "Configuration profile for Service Order Lambda"
  application_id = aws_appconfig_application.service_order.id
  location_uri   = "hosted"

  tags = merge(
    local.common_tags,
    {
      Name = var.appconfig_configuration_profile_name
    }
  )
}

resource "aws_appconfig_hosted_configuration_version" "service_order" {
  application_id           = aws_appconfig_application.service_order.id
  configuration_profile_id = aws_appconfig_configuration_profile.service_order.id
  description              = "Initial configuration for Service Order Lambda"
  content_type             = "application/json"

  content = base64encode(local.appconfig_content)
}

resource "aws_appconfig_deployment_strategy" "standard" {
  name                           = "service-order-deployment-strategy"
  description                    = "Standard deployment strategy for service order configuration"
  deployment_duration_in_minutes = 0
  final_bake_time_in_minutes     = 0
  growth_factor                  = 100
  growth_type                    = "LINEAR"
  replicate_to                   = "NONE"
}

resource "aws_appconfig_deployment" "service_order" {
  application_id           = aws_appconfig_application.service_order.id
  environment_id           = aws_appconfig_environment.service_order.environment_id
  configuration_profile_id = aws_appconfig_configuration_profile.service_order.configuration_profile_id
  configuration_version    = aws_appconfig_hosted_configuration_version.service_order.version_number
  deployment_strategy_id   = aws_appconfig_deployment_strategy.standard.id
  description              = "Deployment of service order configuration"

  # Prevent continuous deployments on each apply
  lifecycle {
    ignore_changes = [configuration_version]
  }
}

output "appconfig_application_id" {
  description = "ID of the AppConfig application"
  value       = aws_appconfig_application.service_order.id
}

output "appconfig_environment_id" {
  description = "ID of the AppConfig environment"
  value       = aws_appconfig_environment.service_order.environment_id
}

output "appconfig_configuration_profile_id" {
  description = "ID of the AppConfig configuration profile"
  value       = aws_appconfig_configuration_profile.service_order.configuration_profile_id
}
