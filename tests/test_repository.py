"""Unit tests for the service order repository.

This module contains tests for the DynamoDB repository
functions in repository.py to verify proper data access operations.
"""

import json
import os
import uuid
from datetime import datetime, UTC
from unittest import mock

import boto3
import pytest
from botocore.exceptions import ClientError
from unittest.mock import MagicMock, patch


from src.service_order_lambda.models import ServiceOrderCreate, ServiceOrderUpdate
from src.service_order_lambda.repository import ServiceOrderRepository


# Test data
CUSTOMER_ID = "customer123"
ORDER_ID = str(uuid.uuid4())
LOCATION_ID = "location456"
TIMESTAMP = datetime.now(UTC).isoformat()

VALID_SERVICE_ORDER = {
    "unit_id": str(uuid.uuid4()),
    "action_id": str(uuid.uuid4()),
    "service_date": "2023-06-15",
    "service_time": "14:30:00",
    "service_duration": 120,
    "service_status": "scheduled",
    "employee_id": str(uuid.uuid4()),
    "service_notes": "Test service order",
    "location_id": LOCATION_ID,
}


# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "APPCONFIG_APPLICATION_ID": "test-app-id",
        "APPCONFIG_ENVIRONMENT_ID": "test-env-id",
        "APPCONFIG_CONFIGURATION_PROFILE_ID": "test-profile-id",
        "LOG_LEVEL": "INFO"
    }):
        yield

# Mock configuration for testing
@pytest.fixture(autouse=True)
def mock_aws_clients():
    """Mock all AWS clients for testing."""
    # Mock AppConfig client
    with patch("boto3.client") as mock_client:
        mock_appconfig = MagicMock()
        mock_content = MagicMock()
        mock_content.read.return_value = json.dumps({"serviceOrderTableName": "test_service_orders"})
        mock_appconfig.get_configuration.return_value = {"Content": mock_content}
        mock_client.return_value = mock_appconfig
        
        # Mock DynamoDB resource
        with patch("boto3.resource") as mock_resource:
            mock_table = MagicMock()
            mock_table.put_item.return_value = {}
            mock_table.get_item.return_value = {}
            mock_table.update_item.return_value = {}
            mock_table.query.return_value = {"Items": []}
            mock_resource.return_value.Table.return_value = mock_table
            
            yield mock_table


@pytest.fixture
def repository(mock_aws_clients):
    """Create a repository instance with mocked dependencies."""
    repo = ServiceOrderRepository()
    repo.table = mock_aws_clients
    return repo


# Test create service order
def test_create_service_order(repository):
    """Test creating a service order in DynamoDB."""
    # Arrange
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    
    # Act
    result = repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)
    
    # Assert
    assert result["PK"] == ORDER_ID
    assert result["SK"] == CUSTOMER_ID
    assert result["unit_id"] == str(service_order.unit_id)
    assert result["action_id"] == str(service_order.action_id)
    assert result["location_id"] == LOCATION_ID
    assert "created_at" in result


def test_create_service_order_error(repository):
    """Test handling errors when creating a service order."""
    # Arrange
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    
    # Mock DynamoDB error
    repository.table.put_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
        "PutItem"
    )
    
    # Act & Assert
    with pytest.raises(ClientError):
        repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)


# Test get service order
def test_get_service_order(repository):
    """Test retrieving a service order from DynamoDB."""
    # Arrange - Create a service order first
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)
    
    # Act
    result = repository.get_service_order(ORDER_ID, CUSTOMER_ID)
    
    # Assert
    assert result["PK"] == ORDER_ID
    assert result["SK"] == CUSTOMER_ID
    assert result["unit_id"] == str(service_order.unit_id)
    assert result["location_id"] == LOCATION_ID


def test_get_service_order_not_found(repository):
    """Test retrieving a non-existent service order."""
    # Act
    result = repository.get_service_order("non-existent", CUSTOMER_ID)
    
    # Assert
    assert result is None


def test_get_service_order_error(repository):
    """Test handling errors when retrieving a service order."""
    # Mock DynamoDB error
    repository.table.get_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
        "GetItem"
    )
    
    # Act & Assert
    with pytest.raises(ClientError):
        repository.get_service_order(ORDER_ID, CUSTOMER_ID)


# Test update service order
def test_update_service_order(repository):
    """Test updating a service order in DynamoDB."""
    # Arrange - Create a service order first
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)
    
    # Create update data
    update_data = {
        "unit_id": service_order.unit_id,
        "action_id": service_order.action_id,
        "service_status": "in_progress",
        "service_notes": "Updated notes",
    }
    update_order = ServiceOrderUpdate(**update_data)
    
    # Act
    result = repository.update_service_order(ORDER_ID, CUSTOMER_ID, update_order)
    
    # Assert
    assert result["service_status"] == "in_progress"
    assert result["service_notes"] == "Updated notes"
    assert "updated_at" in result


def test_update_service_order_not_found(repository):
    """Test updating a non-existent service order."""
    # Arrange
    update_data = {
        "unit_id": uuid.uuid4(),
        "action_id": uuid.uuid4(),
        "service_status": "in_progress",
    }
    update_order = ServiceOrderUpdate(**update_data)
    
    # Act
    result = repository.update_service_order("non-existent", CUSTOMER_ID, update_order)
    
    # Assert
    assert result is None


def test_update_service_order_error(repository):
    """Test handling errors when updating a service order."""
    # Arrange
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    
    # Mock get_service_order to return an item
    repository.table.get_item.return_value = {
        "Item": {
            "PK": ORDER_ID,
            "SK": CUSTOMER_ID,
            "unit_id": str(service_order.unit_id),
            "action_id": str(service_order.action_id),
        }
    }
    
    update_data = {
        "unit_id": service_order.unit_id,
        "action_id": service_order.action_id,
        "service_status": "in_progress",
    }
    update_order = ServiceOrderUpdate(**update_data)
    
    # Mock DynamoDB error
    repository.table.update_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
        "UpdateItem"
    )
    
    # Act & Assert
    with pytest.raises(ClientError):
        repository.update_service_order(ORDER_ID, CUSTOMER_ID, update_order)


# Test mark service order deleted
def test_mark_service_order_deleted(repository):
    """Test marking a service order as deleted in DynamoDB."""
    # Arrange - Create a service order first
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)
    
    # Act
    result = repository.mark_service_order_deleted(ORDER_ID, CUSTOMER_ID)
    
    # Assert
    assert result is True
    
    # Verify the service order has a deleted_at timestamp
    updated_item = repository.get_service_order(ORDER_ID, CUSTOMER_ID)
    assert "deleted_at" in updated_item


def test_mark_service_order_deleted_not_found(repository):
    """Test marking a non-existent service order as deleted."""
    # Act
    result = repository.mark_service_order_deleted("non-existent", CUSTOMER_ID)
    
    # Assert
    assert result is False


def test_mark_service_order_deleted_error(repository):
    """Test handling errors when marking a service order as deleted."""
    # Mock get_service_order to return an item
    repository.table.get_item.return_value = {
        "Item": {
            "PK": ORDER_ID,
            "SK": CUSTOMER_ID,
        }
    }
    
    # Mock DynamoDB error
    repository.table.update_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
        "UpdateItem"
    )
    
    # Act & Assert
    with pytest.raises(ClientError):
        repository.mark_service_order_deleted(ORDER_ID, CUSTOMER_ID)


# Test query service orders by customer
def test_query_service_orders_by_customer(repository):
    """Test querying service orders by customer in DynamoDB."""
    # Arrange - Create multiple service orders
    for i in range(3):
        order_data = VALID_SERVICE_ORDER.copy()
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)
    
    # Act
    results = repository.query_service_orders_by_customer(CUSTOMER_ID)
    
    # Assert
    assert len(results) == 3
    for item in results:
        assert item["SK"] == CUSTOMER_ID


def test_query_service_orders_by_customer_and_location(repository):
    """Test querying service orders by customer and location in DynamoDB."""
    # Arrange - Create service orders with different locations
    location1 = "location1"
    location2 = "location2"
    
    # Orders for location1
    for i in range(2):
        order_data = VALID_SERVICE_ORDER.copy()
        order_data["location_id"] = location1
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)
    
    # Orders for location2
    for i in range(3):
        order_data = VALID_SERVICE_ORDER.copy()
        order_data["location_id"] = location2
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)
    
    # Act
    results1 = repository.query_service_orders_by_customer(CUSTOMER_ID, location1)
    results2 = repository.query_service_orders_by_customer(CUSTOMER_ID, location2)
    
    # Assert
    assert len(results1) == 2
    for item in results1:
        assert item["SK"] == CUSTOMER_ID
        assert item["location_id"] == location1
    
    assert len(results2) == 3
    for item in results2:
        assert item["SK"] == CUSTOMER_ID
        assert item["location_id"] == location2


def test_query_service_orders_by_customer_empty_results(repository):
    """Test querying service orders with no matching results."""
    # Act
    results = repository.query_service_orders_by_customer("non-existent-customer")
    
    # Assert
    assert len(results) == 0


def test_query_service_orders_by_customer_error(repository):
    """Test handling errors when querying service orders."""
    # Mock DynamoDB error
    repository.table.query.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
        "Query"
    )
    
    # Act & Assert
    with pytest.raises(ClientError):
        repository.query_service_orders_by_customer(CUSTOMER_ID)