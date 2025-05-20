"""Unit tests for the service order data models.

This module contains tests for the Pydantic models defined in models.py
to verify proper validation and serialization behavior.
"""

import json
import uuid
from datetime import UTC, datetime

import pytest

from src.service_order_lambda.models import (
    DynamoDBServiceOrder,
    ServiceOrderBase,
    ServiceOrderCreate,
    ServiceOrderResponse,
    ServiceOrderUpdate,
)


# Test data
CUSTOMER_ID = "customer123"
ORDER_ID = str(uuid.uuid4())
LOCATION_ID = "location456"
TIMESTAMP = datetime.now(UTC).isoformat()

VALID_SERVICE_ORDER_DATA = {
    "unit_id": str(uuid.uuid4()),
    "action_id": str(uuid.uuid4()),
    "service_date": "2023-06-15",
    "service_time": "14:30:00",
    "service_duration": 120,
    "service_status": "scheduled",
    "employee_id": str(uuid.uuid4()),
    "service_notes": "Test service order",
}


# Test base service order model
def test_service_order_base_valid_data():
    """Test ServiceOrderBase with valid data."""
    # Arrange
    data = VALID_SERVICE_ORDER_DATA.copy()
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    # Act
    model = ServiceOrderBase.from_dict(data)

    # Assert
    assert model.unit_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["unit_id"])
    assert model.action_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["action_id"])
    assert model.service_date == VALID_SERVICE_ORDER_DATA["service_date"]
    assert model.service_time == VALID_SERVICE_ORDER_DATA["service_time"]
    assert model.service_duration == int(VALID_SERVICE_ORDER_DATA["service_duration"])
    assert model.service_status == VALID_SERVICE_ORDER_DATA["service_status"]
    assert model.employee_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["employee_id"])
    assert model.service_notes == VALID_SERVICE_ORDER_DATA["service_notes"]


def test_service_order_base_required_fields_only():
    """Test ServiceOrderBase with only required fields."""
    # Arrange
    min_data = {
        "unit_id": uuid.uuid4(),
        "action_id": uuid.uuid4(),
    }

    # Act
    model = ServiceOrderBase.from_dict(min_data)

    # Assert
    assert model.unit_id == min_data["unit_id"]
    assert model.action_id == min_data["action_id"]
    assert model.service_date is None
    assert model.service_time is None
    assert model.service_duration is None
    assert model.service_status is None
    assert model.employee_id is None
    assert model.service_notes is None


def test_service_order_base_missing_required_fields():
    """Test ServiceOrderBase with missing required fields."""
    # Arrange
    invalid_data = {
        "service_date": "2023-06-15",
        "service_notes": "Missing required fields",
    }

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        ServiceOrderBase.from_dict(invalid_data)

    # Check that the error message mentions required fields
    error_message = str(excinfo.value)
    assert "unit_id" in error_message or "action_id" in error_message


def test_service_order_base_invalid_uuid():
    """Test ServiceOrderBase with invalid UUID format."""
    # Arrange
    invalid_uuid_data = {
        "unit_id": "not-a-uuid",
        "action_id": str(uuid.uuid4()),
    }

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        ServiceOrderBase.from_dict(invalid_uuid_data)

    # Check that the error mentions invalid UUID format
    error_message = str(excinfo.value)
    assert "Invalid UUID format" in error_message
    assert "unit_id" in error_message


def test_service_order_base_invalid_date_format():
    """Test ServiceOrderBase with invalid date format."""
    # Arrange
    invalid_date_data = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_date": "06/15/2023",  # Not ISO 8601
    }

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        ServiceOrderBase.from_dict(invalid_date_data)

    # Check that the error mentions invalid date format
    error_message = str(excinfo.value)
    assert "Invalid ISO 8601 date format" in error_message


def test_service_order_base_invalid_time_format():
    """Test ServiceOrderBase with invalid time format."""
    # Arrange
    invalid_time_data = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_time": "2:30 PM",  # Not ISO 8601
    }

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        ServiceOrderBase.from_dict(invalid_time_data)

    # Check that the error mentions invalid time format
    error_message = str(excinfo.value)
    assert "Invalid ISO 8601 time format" in error_message


def test_service_order_base_invalid_duration_type():
    """Test ServiceOrderBase with invalid duration type."""
    # Arrange
    invalid_duration_data = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_duration": "two hours",  # Not an integer
    }

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        ServiceOrderBase.from_dict(invalid_duration_data)

    # Check that the error mentions invalid duration type
    error_message = str(excinfo.value)
    assert "service_duration must be an integer" in error_message


# Test service order create model
def test_service_order_create_valid_data():
    """Test ServiceOrderCreate with valid data."""
    # Arrange
    create_data = VALID_SERVICE_ORDER_DATA.copy()
    create_data["location_id"] = LOCATION_ID
    create_data["unit_id"] = uuid.UUID(create_data["unit_id"])
    create_data["action_id"] = uuid.UUID(create_data["action_id"])
    create_data["employee_id"] = uuid.UUID(create_data["employee_id"])
    create_data["service_duration"] = int(create_data["service_duration"])

    # Act
    model = ServiceOrderCreate.from_dict(create_data)

    # Assert
    assert model.unit_id == create_data["unit_id"]
    assert model.action_id == create_data["action_id"]
    assert model.location_id == LOCATION_ID


def test_service_order_create_missing_location_id():
    """Test ServiceOrderCreate with missing location_id."""
    # Arrange & Act & Assert
    # Prepare data with UUIDs
    data = VALID_SERVICE_ORDER_DATA.copy()
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    with pytest.raises(ValueError) as excinfo:
        ServiceOrderCreate.from_dict(data)  # Missing location_id

    # Check that the error mentions missing location_id
    error_message = str(excinfo.value)
    assert "location_id is required" in error_message


# Test service order update model
def test_service_order_update_valid_data():
    """Test ServiceOrderUpdate with valid data."""
    # Arrange
    data = VALID_SERVICE_ORDER_DATA.copy()
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    # Act
    model = ServiceOrderUpdate.from_dict(data)

    # Assert
    assert model.action_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["action_id"])
    assert str(model.action_id) == VALID_SERVICE_ORDER_DATA["action_id"]


# Test service order response model
def test_service_order_response_valid_data():
    """Test ServiceOrderResponse with valid data."""
    # Arrange
    response_data = VALID_SERVICE_ORDER_DATA.copy()
    response_data["id"] = uuid.UUID(ORDER_ID)
    response_data["customer_id"] = CUSTOMER_ID
    response_data["location_id"] = LOCATION_ID
    response_data["created_at"] = TIMESTAMP
    response_data["unit_id"] = uuid.UUID(response_data["unit_id"])
    response_data["action_id"] = uuid.UUID(response_data["action_id"])
    response_data["employee_id"] = uuid.UUID(response_data["employee_id"])
    response_data["service_duration"] = int(response_data["service_duration"])

    # Act
    # Create a ServiceOrderResponse directly since it now requires all fields
    model = ServiceOrderResponse(
        id=response_data["id"],
        customer_id=response_data["customer_id"],
        created_at=response_data["created_at"],
        unit_id=response_data["unit_id"],
        action_id=response_data["action_id"],
        location_id=response_data["location_id"],
        service_date=response_data.get("service_date"),
        service_time=response_data.get("service_time"),
        service_duration=response_data.get("service_duration"),
        service_status=response_data.get("service_status"),
        employee_id=response_data.get("employee_id"),
        service_notes=response_data.get("service_notes"),
    )

    # Assert
    assert model.id == uuid.UUID(ORDER_ID)
    assert model.customer_id == CUSTOMER_ID
    assert model.location_id == LOCATION_ID
    assert model.created_at == TIMESTAMP


def test_service_order_response_missing_required_fields():
    """Test ServiceOrderResponse with missing required fields."""
    # Arrange
    incomplete_data = VALID_SERVICE_ORDER_DATA.copy()
    # Missing id, customer_id, created_at

    # Act & Assert
    # Prepare data with UUIDs
    data = incomplete_data.copy()
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    with pytest.raises(TypeError) as excinfo:
        # This will fail because we're missing required arguments
        ServiceOrderResponse(**data)

    # Check that the error mentions missing required fields
    error_message = str(excinfo.value)
    assert "__init__" in error_message
    assert "missing" in error_message.lower()


def test_service_order_response_json_serialization():
    """Test that ServiceOrderResponse can be JSON serialized."""
    # Arrange
    response_data = VALID_SERVICE_ORDER_DATA.copy()
    response_data["id"] = ORDER_ID
    response_data["customer_id"] = CUSTOMER_ID
    response_data["created_at"] = TIMESTAMP

    # Prepare data with UUIDs
    data = response_data.copy()
    data["id"] = uuid.UUID(data["id"])
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    model = ServiceOrderResponse(
        id=data["id"],
        customer_id=data["customer_id"],
        created_at=data["created_at"],
        unit_id=data["unit_id"],
        action_id=data["action_id"],
        employee_id=data["employee_id"],
        service_duration=data["service_duration"],
        service_date=data.get("service_date"),
        service_time=data.get("service_time"),
        service_status=data.get("service_status"),
        service_notes=data.get("service_notes"),
    )

    # Act
    json_str = model.model_dump_json(exclude_none=True)
    parsed_json = json.loads(json_str)

    # Assert
    assert parsed_json["id"] == str(uuid.UUID(ORDER_ID))
    assert parsed_json["customer_id"] == CUSTOMER_ID
    assert parsed_json["unit_id"] == str(uuid.UUID(VALID_SERVICE_ORDER_DATA["unit_id"]))
    assert parsed_json["created_at"] == TIMESTAMP


# Test DynamoDB service order model
def test_dynamodb_service_order_from_service_order():
    """Test conversion from ServiceOrderCreate to DynamoDBServiceOrder."""
    # Arrange
    create_data = VALID_SERVICE_ORDER_DATA.copy()
    create_data["location_id"] = LOCATION_ID
    # Prepare data with UUIDs
    data = create_data.copy()
    data["unit_id"] = uuid.UUID(data["unit_id"])
    data["action_id"] = uuid.UUID(data["action_id"])
    data["employee_id"] = uuid.UUID(data["employee_id"])
    data["service_duration"] = int(data["service_duration"])

    service_order = ServiceOrderCreate.from_dict(data)

    # Act
    db_item = DynamoDBServiceOrder.from_service_order(
        order_id=uuid.UUID(ORDER_ID),
        customer_id=CUSTOMER_ID,
        service_order=service_order,
        timestamp=TIMESTAMP,
    )

    # Assert
    assert db_item.PK == ORDER_ID
    assert db_item.SK == CUSTOMER_ID
    assert db_item.location_id == LOCATION_ID
    assert db_item.unit_id == str(service_order.unit_id)
    assert db_item.action_id == str(service_order.action_id)
    assert db_item.created_at == TIMESTAMP


def test_dynamodb_service_order_to_response_model():
    """Test conversion from DynamoDBServiceOrder to ServiceOrderResponse."""
    # Arrange
    db_data = {
        "PK": ORDER_ID,
        "SK": CUSTOMER_ID,
        "unit_id": VALID_SERVICE_ORDER_DATA["unit_id"],
        "action_id": VALID_SERVICE_ORDER_DATA["action_id"],
        "service_date": VALID_SERVICE_ORDER_DATA["service_date"],
        "service_time": VALID_SERVICE_ORDER_DATA["service_time"],
        "service_duration": VALID_SERVICE_ORDER_DATA["service_duration"],
        "service_status": VALID_SERVICE_ORDER_DATA["service_status"],
        "employee_id": VALID_SERVICE_ORDER_DATA["employee_id"],
        "service_notes": VALID_SERVICE_ORDER_DATA["service_notes"],
        "location_id": LOCATION_ID,
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }

    db_item = DynamoDBServiceOrder(**db_data)

    # Act
    response_model = db_item.to_response_model()

    # Assert
    assert response_model.id == uuid.UUID(ORDER_ID)
    assert response_model.customer_id == CUSTOMER_ID
    assert response_model.location_id == LOCATION_ID
    assert response_model.unit_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["unit_id"])
    assert response_model.action_id == uuid.UUID(VALID_SERVICE_ORDER_DATA["action_id"])
    assert response_model.created_at == TIMESTAMP
    assert response_model.updated_at == TIMESTAMP


def test_dynamodb_service_order_optional_fields():
    """Test that DynamoDBServiceOrder handles optional fields correctly."""
    # Arrange - minimal fields
    minimal_db_data = {
        "PK": ORDER_ID,
        "SK": CUSTOMER_ID,
        "unit_id": VALID_SERVICE_ORDER_DATA["unit_id"],
        "action_id": VALID_SERVICE_ORDER_DATA["action_id"],
        "created_at": TIMESTAMP,
    }

    # Act
    db_item = DynamoDBServiceOrder(**minimal_db_data)
    response_model = db_item.to_response_model()

    # Assert
    assert db_item.service_date is None
    assert db_item.service_time is None
    assert db_item.service_duration is None
    assert db_item.service_status is None
    assert db_item.employee_id is None
    assert db_item.service_notes is None
    assert db_item.updated_at is None
    assert db_item.deleted_at is None

    # Check response model
    assert response_model.service_date is None
    assert response_model.service_time is None
    assert response_model.service_duration is None
    assert response_model.service_status is None
    assert response_model.employee_id is None
    assert response_model.service_notes is None
    assert response_model.updated_at is None
    assert response_model.deleted_at is None
