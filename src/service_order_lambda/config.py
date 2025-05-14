"""Configuration module for the Service Order Lambda.

This module handles configuration loading and management,
including retrieving values from AWS AppConfig.
"""

import json
import logging
import os
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class Config:
    """Configuration manager for the service order Lambda.

    Handles retrieving configuration values from AWS AppConfig
    and environment variables.
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._app_config_client = boto3.client("appconfig")
        self._table_name: Optional[str] = None
        
        # Get required environment variables
        self.application_id = os.environ.get("APPCONFIG_APPLICATION_ID")
        self.environment_id = os.environ.get("APPCONFIG_ENVIRONMENT_ID")
        self.configuration_profile_id = os.environ.get("APPCONFIG_CONFIGURATION_PROFILE_ID")
        
        if not all([self.application_id, self.environment_id, self.configuration_profile_id]):
            logger.warning("Missing required AppConfig environment variables")
    
    @property
    def service_order_table_name(self) -> str:
        """Get the service order DynamoDB table name from AppConfig.
        
        Returns:
            The DynamoDB table name
            
        Raises:
            RuntimeError: If the table name cannot be retrieved
        """
        if self._table_name is None:
            try:
                response = self._app_config_client.get_configuration(
                    Application=self.application_id,
                    Environment=self.environment_id,
                    Configuration=self.configuration_profile_id,
                    ClientId="service-order-lambda"
                )
                
                config_data = json.loads(response["Content"].read())
                self._table_name = config_data.get("serviceOrderTableName")
                
                if not self._table_name:
                    raise ValueError("serviceOrderTableName not found in AppConfig")
                
                logger.info(f"Retrieved table name from AppConfig: {self._table_name}")
            except (ClientError, ValueError) as e:
                logger.error(f"Failed to retrieve table name from AppConfig: {str(e)}")
                raise RuntimeError(f"Configuration error: {str(e)}") from e
        
        return self._table_name
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from AppConfig.
        
        Args:
            key: The configuration key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        try:
            response = self._app_config_client.get_configuration(
                Application=self.application_id,
                Environment=self.environment_id,
                Configuration=self.configuration_profile_id,
                ClientId="service-order-lambda"
            )
            
            config_data = json.loads(response["Content"].read())
            return config_data.get(key, default)
        except Exception as e:
            logger.warning(f"Failed to retrieve config value {key}: {str(e)}")
            return default


# Singleton instance
config = Config()