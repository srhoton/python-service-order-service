"""Configuration module for the Service Order Lambda.

This module handles configuration loading and management through environment variables.
"""

import logging
import os
from typing import Final, Optional

# Configure logger
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class Config:
    """Configuration manager for the service order Lambda.

    Handles retrieving configuration values from environment variables.
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._table_name: Optional[str] = None

    @property
    def service_order_table_name(self) -> str:
        """Get the service order DynamoDB table name from environment variable.

        Returns:
            The DynamoDB table name

        Raises:
            RuntimeError: If the table name is not configured
        """
        if self._table_name is None:
            self._table_name = os.environ.get("DYNAMODB_TABLE_NAME")

            if not self._table_name:
                error_msg: str = "DYNAMODB_TABLE_NAME environment variable not set"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info(f"Using table name from environment: {self._table_name}")

        return self._table_name


# Singleton instance
config: Final[Config] = Config()
