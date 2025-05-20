"""Service order data models.

This module contains the data models used for validation and serialization
of service order data using standard Python dataclasses.
"""

import dataclasses
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar, Union

# Type variable for generic return types with class methods
T = TypeVar("T", bound="ServiceOrderBase")

# Regular expressions for validation
ISO_DATE_REGEX: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_TIME_REGEX: re.Pattern[str] = re.compile(r"^\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")


def validate_uuid(value: Any, field_name: str = "") -> uuid.UUID:
    """Convert value to UUID or raise ValueError.

    Args:
        value: The value to convert to UUID
        field_name: The name of the field being validated (optional)

    Returns:
        Validated UUID object

    Raises:
        ValueError: If value cannot be converted to UUID
    """
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as e:
        error_prefix = (
            f"Invalid UUID format for {field_name}: " if field_name else "Invalid UUID format: "
        )
        raise ValueError(f"{error_prefix}{value}") from e


def validate_date_format(value: Optional[str]) -> Optional[str]:
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


def validate_time_format(value: Optional[str]) -> Optional[str]:
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
    if re.match(r"^\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})?$", str(value)):
        try:
            # Extract hour value from time string
            hour = int(str(value).split(":")[0])
            # Valid hours are 0-23
            if 0 <= hour <= 23:
                return value
        except (ValueError, IndexError):
            pass

    try:
        # Try more complex formats through datetime
        datetime.fromisoformat(str(value))
        return value
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 time format: {value}") from e


@dataclass
class ServiceOrderBase:
    """Base class for service order data.

    This class contains the common fields for service order operations.
    """

    unit_id: uuid.UUID
    action_id: uuid.UUID
    service_date: Optional[str] = None
    service_time: Optional[str] = None
    service_duration: Optional[int] = None
    service_status: Optional[str] = None
    employee_id: Optional[uuid.UUID] = None
    service_notes: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and convert field values after initialization."""
        # Validate and convert UUIDs
        self.unit_id = validate_uuid(self.unit_id, "unit_id")
        self.action_id = validate_uuid(self.action_id, "action_id")

        if self.employee_id is not None:
            self.employee_id = validate_uuid(self.employee_id, "employee_id")

        # Validate date and time formats
        if self.service_date is not None:
            self.service_date = validate_date_format(self.service_date)

        if self.service_time is not None:
            self.service_time = validate_time_format(self.service_time)

        # Ensure service_duration is an integer
        if self.service_duration is not None:
            try:
                self.service_duration = int(self.service_duration)
            except (ValueError, TypeError) as e:
                raise ValueError("service_duration must be an integer") from e

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing field values

        Returns:
            New instance of the class
        """
        # Filter out keys that are not fields in the dataclass
        field_names: set[str] = {
            dataclass_field.name for dataclass_field in dataclasses.fields(cls)
        }
        filtered_data: Dict[str, Any] = {k: v for k, v in data.items() if k in field_names}

        # Check for required fields if this is ServiceOrderBase
        required_fields = ["unit_id", "action_id"]
        for required_field in required_fields:
            if required_field not in filtered_data:
                raise ValueError(f"Missing required field: {required_field}")

        return cls(**filtered_data)

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Convert the object to a dictionary.

        Args:
            exclude_none: If True, exclude None values from the dictionary

        Returns:
            Dictionary representation of the object
        """
        result: Dict[str, Any] = asdict(self)

        # Convert UUID objects to strings
        for key, value in result.items():
            if isinstance(value, uuid.UUID):
                result[key] = str(value)

        # Remove None values if requested
        if exclude_none:
            return {k: v for k, v in result.items() if v is not None}

        return result


@dataclass
class ServiceOrderCreate(ServiceOrderBase):
    """Model for creating a new service order.

    This class extends the base class with location_id which is required
    for creation but not stored directly in the main service order attributes.
    """

    location_id: str = field(default="")  # Required field initialized with empty default

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        super().__post_init__()

        if not self.location_id:
            raise ValueError("location_id is required")


@dataclass
class ServiceOrderUpdate(ServiceOrderBase):
    """Model for updating an existing service order.

    This class extends the base class without additional fields.
    """

    pass


@dataclass
class ServiceOrderResponse:
    """Model for service order responses.

    This class contains service order data with tracking fields like
    created_at, updated_at, and other metadata.
    """

    # Required fields first
    id: uuid.UUID
    customer_id: str
    unit_id: uuid.UUID
    action_id: uuid.UUID
    created_at: str
    # Optional fields with defaults
    location_id: Optional[str] = None
    service_date: Optional[str] = None
    service_time: Optional[str] = None
    service_duration: Optional[int] = None
    service_status: Optional[str] = None
    employee_id: Optional[uuid.UUID] = None
    service_notes: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        # Validate UUIDs
        self.id = validate_uuid(self.id, "id")
        self.unit_id = validate_uuid(self.unit_id, "unit_id")
        self.action_id = validate_uuid(self.action_id, "action_id")

        if self.employee_id is not None:
            self.employee_id = validate_uuid(self.employee_id, "employee_id")

        if not self.customer_id:
            raise ValueError("customer_id is required")

        # Validate timestamps
        if self.created_at:
            validate_date_format(self.created_at.split("T")[0] if "T" in self.created_at else None)

        if self.updated_at:
            validate_date_format(self.updated_at.split("T")[0] if "T" in self.updated_at else None)

        if self.deleted_at:
            validate_date_format(self.deleted_at.split("T")[0] if "T" in self.deleted_at else None)

        # Validate other formats
        if self.service_date is not None:
            self.service_date = validate_date_format(self.service_date)

        if self.service_time is not None:
            self.service_time = validate_time_format(self.service_time)

        # Ensure service_duration is an integer
        if self.service_duration is not None:
            try:
                self.service_duration = int(self.service_duration)
            except (ValueError, TypeError) as e:
                raise ValueError("service_duration must be an integer") from e

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Convert the object to a dictionary.

        Args:
            exclude_none: If True, exclude None values from the dictionary

        Returns:
            Dictionary representation of the object
        """
        result = asdict(self)

        # Convert UUID objects to strings
        for key, value in result.items():
            if isinstance(value, uuid.UUID):
                result[key] = str(value)

        # Remove None values if requested
        if exclude_none:
            return {k: v for k, v in result.items() if v is not None}

        return result

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Maintain compatibility with previous Pydantic model interface.

        Args:
            **kwargs: Additional arguments (for compatibility)

        Returns:
            Dictionary representation of the object
        """
        exclude_none: bool = bool(kwargs.get("exclude_none", False))
        return self.to_dict(exclude_none=exclude_none)

    def model_dump_json(self, **kwargs: Any) -> str:
        """Convert the model to a JSON string.

        Args:
            **kwargs: Additional arguments (for compatibility)

        Returns:
            JSON string representation of the object
        """
        return json.dumps(self.model_dump(**kwargs), default=str)


@dataclass
class DynamoDBServiceOrder:
    """Internal model for DynamoDB service order items.

    This class represents how service orders are stored in DynamoDB,
    including partition keys and sort keys.
    """

    PK: str  # UUID of the service order
    SK: str  # Customer ID
    unit_id: str
    action_id: str
    created_at: str
    location_id: Optional[str] = None
    service_date: Optional[str] = None
    service_time: Optional[str] = None
    service_duration: Optional[int] = None
    service_status: Optional[str] = None
    employee_id: Optional[str] = None
    service_notes: Optional[str] = None
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

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Convert the object to a dictionary.

        Args:
            exclude_none: If True, exclude None values from the dictionary

        Returns:
            Dictionary representation of the object
        """
        result = asdict(self)

        # Remove None values if requested
        if exclude_none:
            return {k: v for k, v in result.items() if v is not None}

        return result

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
