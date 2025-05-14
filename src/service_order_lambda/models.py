"""Service order data models.

This module contains the Pydantic models used for validation and serialization
of service order data.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ServiceOrderBase(BaseModel):
    """Base model for service order data.

    This model contains the common fields for service order operations.
    """

    unit_id: uuid.UUID = Field(..., description="Unique identifier for the unit being serviced")
    action_id: uuid.UUID = Field(
        ..., description="Unique identifier for the service action to be performed"
    )
    service_date: Optional[str] = Field(
        None, description="The date of service in ISO 8601 format (YYYY-MM-DD)"
    )
    service_time: Optional[str] = Field(
        None, description="The time of service in ISO 8601 format (HH:MM:SS)"
    )
    service_duration: Optional[int] = Field(None, description="Duration of service in minutes")
    service_status: Optional[str] = Field(None, description="Current status of the service order")
    employee_id: Optional[uuid.UUID] = Field(
        None, description="Unique identifier for the employee assigned to the service"
    )
    service_notes: Optional[str] = Field(
        None, description="Additional notes related to the service"
    )

    @field_validator("service_date", mode="before")
    def validate_date_format(self, value: Optional[str]) -> Optional[str]:
        """Validate date strings are in ISO 8601 format.

        Args:
            value: The date string to validate

        Returns:
            The validated date string

        Raises:
            ValueError: If the value is not in ISO 8601 format
        """
        if value is None:
            return None
        try:
            # Validate date format
            datetime.fromisoformat(str(value))
            return value
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format: {value}") from e

    @field_validator("service_time", mode="before")
    def validate_time_format(self, value: Optional[str]) -> Optional[str]:
        """Validate time strings are in ISO 8601 format.

        Args:
            value: The time string to validate

        Returns:
            The validated time string

        Raises:
            ValueError: If the value is not in ISO 8601 format
        """
        if value is None:
            return None

        # Simple time validation
        import re

        if re.match(r"^\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})?$", str(value)):
            return value

        try:
            # Try more complex formats through datetime
            datetime.fromisoformat(str(value))
            return value
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 time format: {value}") from e


class ServiceOrderCreate(ServiceOrderBase):
    """Model for creating a new service order.

    This model extends the base model with location_id which is required
    for creation but not stored directly in the main service order attributes.
    """

    location_id: str = Field(..., description="Location identifier for the service")


class ServiceOrderUpdate(ServiceOrderBase):
    """Model for updating an existing service order.

    This model extends the base model without additional fields.
    """

    pass


class ServiceOrderResponse(ServiceOrderBase):
    """Model for service order responses.

    This model extends the base model with tracking fields like
    created_at, updated_at, and other metadata.
    """

    id: uuid.UUID = Field(..., description="Unique identifier for the service order")
    customer_id: str = Field(..., description="Customer identifier")
    location_id: Optional[str] = Field(None, description="Location identifier for the service")
    created_at: str = Field(..., description="Timestamp of creation in ISO 8601 format")
    updated_at: Optional[str] = Field(
        None, description="Timestamp of last update in ISO 8601 format"
    )
    deleted_at: Optional[str] = Field(None, description="Timestamp of deletion in ISO 8601 format")

    model_config = {
        "populate_by_name": True,
    }

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Override default model_dump to handle UUID serialization."""
        data = super().model_dump(**kwargs)
        # Convert UUID objects to strings
        if id_value := data.get("id"):
            data["id"] = str(id_value)
        if unit_id := data.get("unit_id"):
            data["unit_id"] = str(unit_id)
        if action_id := data.get("action_id"):
            data["action_id"] = str(action_id)
        if employee_id := data.get("employee_id"):
            data["employee_id"] = str(employee_id)
        return data


class DynamoDBServiceOrder(BaseModel):
    """Internal model for DynamoDB service order items.

    This model represents how service orders are stored in DynamoDB,
    including partition keys and sort keys.
    """

    PK: str  # UUID of the service order
    SK: str  # Customer ID
    location_id: Optional[str] = None
    unit_id: str
    action_id: str
    service_date: Optional[str] = None
    service_time: Optional[str] = None
    service_duration: Optional[int] = None
    service_status: Optional[str] = None
    employee_id: Optional[str] = None
    service_notes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

    @classmethod
    def from_service_order(
        cls,
        order_id: uuid.UUID,
        customer_id: str,
        service_order: Union[ServiceOrderCreate, ServiceOrderUpdate],
        timestamp: str,
    ) -> "DynamoDBServiceOrder":
        """Create a DynamoDB item from a service order model.

        Args:
            order_id: The UUID for the service order
            customer_id: The customer ID
            service_order: The service order data
            timestamp: The current timestamp in ISO 8601 format

        Returns:
            A DynamoDB representation of the service order
        """
        item: Dict[str, Any] = {
            "PK": str(order_id),
            "SK": customer_id,
            "unit_id": str(service_order.unit_id),
            "action_id": str(service_order.action_id),
            "created_at": timestamp,
        }

        # Add optional fields if present
        if isinstance(service_order, ServiceOrderCreate) and service_order.location_id:
            item["location_id"] = service_order.location_id
        if service_order.service_date:
            item["service_date"] = service_order.service_date
        if service_order.service_time:
            item["service_time"] = service_order.service_time
        if service_order.service_duration is not None:
            item["service_duration"] = int(service_order.service_duration)
        if service_order.service_status:
            item["service_status"] = service_order.service_status
        if service_order.employee_id:
            item["employee_id"] = str(service_order.employee_id)
        if service_order.service_notes:
            item["service_notes"] = service_order.service_notes

        return cls(**item)

    def to_response_model(self) -> ServiceOrderResponse:
        """Convert DynamoDB item to a response model.

        Returns:
            A ServiceOrderResponse model initialized with the DynamoDB item data
        """
        response_data: Dict[str, Any] = {
            "id": uuid.UUID(self.PK),
            "customer_id": self.SK,
            "unit_id": uuid.UUID(self.unit_id),
            "action_id": uuid.UUID(self.action_id),
            "created_at": self.created_at,
        }

        # Add optional fields if present
        if self.location_id:
            response_data["location_id"] = self.location_id
        if self.service_date:
            response_data["service_date"] = self.service_date
        if self.service_time:
            response_data["service_time"] = self.service_time
        if self.service_duration is not None:
            if isinstance(self.service_duration, str):
                response_data["service_duration"] = int(self.service_duration)
            else:
                response_data["service_duration"] = self.service_duration
        if self.service_status:
            response_data["service_status"] = self.service_status
        if self.employee_id:
            response_data["employee_id"] = uuid.UUID(self.employee_id)
        if self.service_notes:
            response_data["service_notes"] = self.service_notes
        if self.updated_at:
            response_data["updated_at"] = self.updated_at
        if self.deleted_at:
            response_data["deleted_at"] = self.deleted_at

        return ServiceOrderResponse(**response_data)
