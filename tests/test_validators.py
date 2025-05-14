"""Unit tests for the service order request validators.

This module contains tests for the validation functions in validators.py
to verify proper validation of request parameters and structures.
"""

import json
import uuid
from typing import Dict, Any, Optional, cast

import pytest

from src.service_order_lambda.validators import (
    validate_uuid,
    validate_iso_date,
    validate_iso_time,
    validate_create_request,
    validate_update_request,
    validate_delete_request,
    validate_get_request,
)


# Test UUID validation
def test_validate_uuid_valid():
    """Test validation of a valid UUID string."""
    # Arrange
    valid_uuid = str(uuid.uuid4())
    
    # Act
    is_valid, parsed_uuid = validate_uuid(valid_uuid)
    
    # Assert
    assert is_valid is True
    assert isinstance(parsed_uuid, uuid.UUID)
    assert str(parsed_uuid) == valid_uuid


def test_validate_uuid_invalid():
    """Test validation of an invalid UUID string."""
    # Arrange
    invalid_uuids = [
        "not-a-uuid",
        "123",
        "",
        None,
        "12345678-1234-1234-1234-1234567890ab-extra",
    ]
    
    # Act & Assert
    for invalid_uuid in invalid_uuids:
        is_valid, parsed_uuid = validate_uuid(invalid_uuid)
        assert is_valid is False
        assert parsed_uuid is None


# Test ISO date validation
def test_validate_iso_date_valid():
    """Test validation of valid ISO 8601 date strings."""
    # Arrange
    valid_dates = [
        "2023-01-01",
        "2023-12-31",
        "2023-05-15",
    ]
    
    # Act & Assert
    for valid_date in valid_dates:
        assert validate_iso_date(valid_date) is True


def test_validate_iso_date_invalid():
    """Test validation of invalid ISO 8601 date strings."""
    # Arrange
    invalid_dates = [
        "01/01/2023",
        "2023/01/01",
        "2023.01.01",
        "20230101",
        "not-a-date",
        "",
    ]
    
    # Act & Assert
    for invalid_date in invalid_dates:
        assert validate_iso_date(invalid_date) is False


def test_validate_iso_date_none():
    """Test validation when date is None."""
    # Act & Assert
    assert validate_iso_date(None) is True


# Test ISO time validation
def test_validate_iso_time_valid():
    """Test validation of valid ISO 8601 time strings."""
    # Arrange
    valid_times = [
        "14:30:00",
        "00:00:00",
        "23:59:59",
        "12:30:45Z",
        "12:30:45+00:00",
        "12:30:45.123",
    ]
    
    # Act & Assert
    for valid_time in valid_times:
        assert validate_iso_time(valid_time) is True


def test_validate_iso_time_invalid():
    """Test validation of invalid ISO 8601 time strings."""
    # Arrange
    invalid_times = [
        "2:30 PM",
        "14h30",
        "14.30.00",
        "143000",
        "24:00:00",  # Invalid hour
        "not-a-time",
        "",
    ]
    
    # Act & Assert
    for invalid_time in invalid_times:
        assert validate_iso_time(invalid_time) is False


def test_validate_iso_time_none():
    """Test validation when time is None."""
    # Act & Assert
    assert validate_iso_time(None) is True


# Create a mock event helper
def create_mock_event(
    path_params: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    body_as_json: bool = True,
) -> Dict[str, Any]:
    """Create a mock API Gateway event for testing validators.
    
    Args:
        path_params: Path parameters
        query_params: Query string parameters
        body: Request body
        body_as_json: Whether to stringify the body as JSON
        
    Returns:
        A mock API Gateway event
    """
    event: Dict[str, Any] = {
        "pathParameters": path_params or {},
        "queryStringParameters": query_params or {},
    }
    
    if body is not None:
        event["body"] = json.dumps(body) if body_as_json else body
    
    return event


# Test create request validation
def test_validate_create_request_valid():
    """Test validation of a valid service order creation request."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_date": "2023-06-15",
        "service_time": "14:30:00",
        "service_duration": 120,
        "service_status": "scheduled",
        "employee_id": str(uuid.uuid4()),
        "service_notes": "Test service order",
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=valid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["body"] is not None
    assert result["error"] is None
    assert result["body"]["location_id"] == location_id
    assert isinstance(result["body"]["unit_id"], uuid.UUID)
    assert isinstance(result["body"]["action_id"], uuid.UUID)
    assert isinstance(result["body"]["employee_id"], uuid.UUID)


def test_validate_create_request_missing_customer_id():
    """Test validation of a creation request with missing customer ID."""
    # Arrange
    location_id = "location456"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
    }
    
    event = create_mock_event(
        path_params={},  # Missing customerId
        query_params={"locationId": location_id},
        body=valid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Missing customerId" in result["error"]


def test_validate_create_request_missing_location_id():
    """Test validation of a creation request with missing location ID."""
    # Arrange
    customer_id = "customer123"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={},  # Missing locationId
        body=valid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Missing locationId" in result["error"]


def test_validate_create_request_missing_body():
    """Test validation of a creation request with missing body."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        # No body
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Missing request body" in result["error"]


def test_validate_create_request_invalid_json():
    """Test validation of a creation request with invalid JSON body."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
    )
    event["body"] = "not valid json"
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Invalid JSON" in result["error"]


def test_validate_create_request_missing_required_fields():
    """Test validation of a creation request with missing required fields."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    incomplete_body = {
        # Missing unit_id and action_id
        "service_date": "2023-06-15",
        "service_notes": "Test service order",
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=incomplete_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Missing required field" in result["error"]


def test_validate_create_request_invalid_uuid_field():
    """Test validation of a creation request with invalid UUID fields."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    invalid_body = {
        "unit_id": "not-a-uuid",  # Invalid UUID
        "action_id": str(uuid.uuid4()),
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=invalid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Invalid UUID format" in result["error"]


def test_validate_create_request_invalid_date_format():
    """Test validation of a creation request with invalid date format."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    invalid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_date": "06/15/2023",  # Invalid format
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=invalid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Invalid ISO 8601 format for service_date" in result["error"]


def test_validate_create_request_invalid_time_format():
    """Test validation of a creation request with invalid time format."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    invalid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_time": "2:30 PM",  # Invalid format
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=invalid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "Invalid ISO 8601 format for service_time" in result["error"]


def test_validate_create_request_invalid_duration():
    """Test validation of a creation request with invalid duration."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    invalid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_duration": "two hours",  # Not an integer
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
        body=invalid_body,
    )
    
    # Act
    result = validate_create_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["error"] is not None
    assert "service_duration must be an integer" in result["error"]


# Test update request validation
def test_validate_update_request_valid():
    """Test validation of a valid service order update request."""
    # Arrange
    order_id = str(uuid.uuid4())
    customer_id = "customer123"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
        "service_status": "in_progress",
        "service_notes": "Updated notes",
    }
    
    event = create_mock_event(
        path_params={"id": order_id, "customerId": customer_id},
        body=valid_body,
    )
    
    # Act
    result = validate_update_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["body"] is not None
    assert result["customer_id"] == customer_id
    assert result["error"] is None
    assert isinstance(result["body"]["unit_id"], uuid.UUID)
    assert isinstance(result["body"]["action_id"], uuid.UUID)


def test_validate_update_request_missing_id():
    """Test validation of an update request with missing service order ID."""
    # Arrange
    customer_id = "customer123"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
    }
    
    event = create_mock_event(
        path_params={"customerId": customer_id},  # Missing id
        body=valid_body,
    )
    
    # Act
    result = validate_update_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["customer_id"] is None
    assert result["error"] is not None
    assert "Missing service order id" in result["error"]


def test_validate_update_request_invalid_id():
    """Test validation of an update request with invalid service order ID."""
    # Arrange
    customer_id = "customer123"
    
    valid_body = {
        "unit_id": str(uuid.uuid4()),
        "action_id": str(uuid.uuid4()),
    }
    
    event = create_mock_event(
        path_params={"id": "not-a-uuid", "customerId": customer_id},
        body=valid_body,
    )
    
    # Act
    result = validate_update_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["body"] is None
    assert result["customer_id"] is None
    assert result["error"] is not None
    assert "Invalid UUID format" in result["error"]


# Test delete request validation
def test_validate_delete_request_valid():
    """Test validation of a valid service order deletion request."""
    # Arrange
    order_id = str(uuid.uuid4())
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"id": order_id, "customerId": customer_id},
    )
    
    # Act
    result = validate_delete_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["order_id"] == order_id
    assert result["customer_id"] == customer_id
    assert result["error"] is None


def test_validate_delete_request_missing_id():
    """Test validation of a deletion request with missing service order ID."""
    # Arrange
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"customerId": customer_id},  # Missing id
    )
    
    # Act
    result = validate_delete_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["order_id"] is None
    assert result["customer_id"] is None
    assert result["error"] is not None
    assert "Missing service order id" in result["error"]


def test_validate_delete_request_invalid_id():
    """Test validation of a deletion request with invalid service order ID."""
    # Arrange
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"id": "not-a-uuid", "customerId": customer_id},
    )
    
    # Act
    result = validate_delete_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["order_id"] is None
    assert result["customer_id"] is None
    assert result["error"] is not None
    assert "Invalid UUID format" in result["error"]


# Test get request validation
def test_validate_get_request_valid_with_id():
    """Test validation of a valid service order get request with ID."""
    # Arrange
    order_id = str(uuid.uuid4())
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"id": order_id, "customerId": customer_id},
    )
    
    # Act
    result = validate_get_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["order_id"] == order_id
    assert result["customer_id"] == customer_id
    assert result["location_id"] is None
    assert result["error"] is None


def test_validate_get_request_valid_with_location():
    """Test validation of a valid service order get request with location ID."""
    # Arrange
    customer_id = "customer123"
    location_id = "location456"
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
        query_params={"locationId": location_id},
    )
    
    # Act
    result = validate_get_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["order_id"] is None
    assert result["customer_id"] == customer_id
    assert result["location_id"] == location_id
    assert result["error"] is None


def test_validate_get_request_valid_customer_only():
    """Test validation of a valid service order get request with customer ID only."""
    # Arrange
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"customerId": customer_id},
    )
    
    # Act
    result = validate_get_request(event)
    
    # Assert
    assert result["is_valid"] is True
    assert result["order_id"] is None
    assert result["customer_id"] == customer_id
    assert result["location_id"] is None
    assert result["error"] is None


def test_validate_get_request_missing_customer_id():
    """Test validation of a get request with missing customer ID."""
    # Arrange
    event = create_mock_event(
        path_params={},  # Missing customerId
    )
    
    # Act
    result = validate_get_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["order_id"] is None
    assert result["customer_id"] is None
    assert result["location_id"] is None
    assert result["error"] is not None
    assert "Missing customerId" in result["error"]


def test_validate_get_request_invalid_id():
    """Test validation of a get request with invalid service order ID."""
    # Arrange
    customer_id = "customer123"
    
    event = create_mock_event(
        path_params={"id": "not-a-uuid", "customerId": customer_id},
    )
    
    # Act
    result = validate_get_request(event)
    
    # Assert
    assert result["is_valid"] is False
    assert result["order_id"] is None
    assert result["customer_id"] is None
    assert result["location_id"] is None
    assert result["error"] is not None
    assert "Invalid UUID format" in result["error"]