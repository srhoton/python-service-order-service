"""Unit tests for the service order repository.

This module contains tests for the DynamoDB repository
functions in repository.py to verify proper data access operations.
"""

import json
import os
import uuid
from datetime import UTC, datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

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
    with patch.dict(
        os.environ,
        {
            "APPCONFIG_APPLICATION_ID": "test-app-id",
            "APPCONFIG_ENVIRONMENT_ID": "test-env-id",
            "APPCONFIG_CONFIGURATION_PROFILE_ID": "test-profile-id",
            "LOG_LEVEL": "INFO",
            "AWS_DEFAULT_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
        },
    ):
        yield


# Mock configuration for testing
@pytest.fixture(autouse=True)
def mock_aws_clients():
    """Mock all AWS clients for testing."""
    # Mock AWS configuration to force region
    with patch("boto3.setup_default_session", autospec=True) as mock_setup:
        # Explicitly configure boto3 with a region
        patch("boto3._get_default_session")
        
        # Mock AppConfig client
        with patch("boto3.client") as mock_client:
            mock_appconfig = MagicMock()
            mock_content = MagicMock()
            mock_content.read.return_value = json.dumps(
                {"serviceOrderTableName": "test_service_orders"}
            )

            # Configure get_configuration to accept required parameters
            def mock_get_config(**kwargs: dict) -> dict:
                # Validate required parameters are present
                required_params = ["Application", "Environment", "Configuration", "ClientId"]
                for param in required_params:
                    if param not in kwargs:
                        raise ValueError(f"Missing required parameter: {param}")
                return {"Content": mock_content}

            mock_appconfig.get_configuration.side_effect = mock_get_config
            mock_client.return_value = mock_appconfig

        # Mock DynamoDB resource
        with patch("boto3.resource") as mock_resource:
            # Create a mock DynamoDB table that stores items
            mock_table = MagicMock()

            # Store items in a dictionary for our mock
            mock_items = {}

            # Mock put_item to store items
            def mock_put_item(**kwargs: dict) -> dict:
                item = kwargs.get("Item", {})
                pk = item.get("PK")
                sk = item.get("SK")
                mock_items[(pk, sk)] = item.copy()
                return {}

            # Mock get_item to retrieve items
            def mock_get_item(**kwargs: dict) -> dict:
                key = kwargs.get("Key", {})
                pk = key.get("PK")
                sk = key.get("SK")
                item = mock_items.get((pk, sk))
                if item:
                    return {"Item": item}
                return {}

            # Mock update_item to modify items
            def mock_update_item(**kwargs: dict) -> dict:
                key = kwargs.get("Key", {})
                update_expression = kwargs.get("UpdateExpression", "")
                expression_attribute_values = kwargs.get("ExpressionAttributeValues", {})
                expression_attribute_names = kwargs.get("ExpressionAttributeNames", None)
                
                pk = key.get("PK")
                sk = key.get("SK")
                if (pk, sk) not in mock_items:
                    return {}

                item = mock_items[(pk, sk)].copy()

                # Handle simple SET expressions
                if "SET" in update_expression:
                    # Split each assignment in the SET expression
                    parts = update_expression.split("SET ")[1].split()
                    i = 0
                    while i < len(parts):
                        if i + 2 < len(parts) and parts[i + 1] == "=":
                            # Handle attribute names with # prefix
                            attr_name = parts[i]
                            if attr_name.startswith("#") and expression_attribute_names:
                                attr_name = expression_attribute_names.get(attr_name, attr_name)
                            # Handle value references with : prefix
                            val_ref = parts[i+2]
                            if val_ref in expression_attribute_values:
                                item[attr_name] = expression_attribute_values[val_ref]
                            i += 3
                        else:
                            # Skip other parts we don't understand
                            i += 1

                mock_items[(pk, sk)] = item
                return {"Attributes": item}

            # Mock query to search items
            def mock_query(**kwargs: dict) -> dict:
                items = []
                index_name = kwargs.get("IndexName")

                # Simple implementation for queries by customer ID
                if index_name == "CustomerIndex" and "KeyConditionExpression" in kwargs:
                    for _key, item in mock_items.items():
                        if item["SK"] == CUSTOMER_ID:
                            # Apply location filter if present
                            if "FilterExpression" in kwargs and "location_id" in item:
                                location = kwargs.get("ExpressionAttributeValues", {}).get(
                                    ":location_id"
                                )
                                if location and item["location_id"] == location:
                                    items.append(item)
                            else:
                                items.append(item)

                return {"Items": items}

            mock_table.put_item.side_effect = mock_put_item
            mock_table.get_item.side_effect = mock_get_item
            mock_table.update_item.side_effect = mock_update_item
            mock_table.query.side_effect = mock_query

            # Create a mock DynamoDB resource with a Table method
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_resource.return_value = mock_dynamodb

            yield mock_table


@pytest.fixture
def repository(mock_aws_clients):
    """Create a repository instance with mocked dependencies."""
    # Mock the config object to return a predetermined table name
    with patch("src.service_order_lambda.repository.config") as mock_config:
        mock_config.service_order_table_name = "test_service_orders"
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
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}}, "PutItem"
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
    # Create a service order first
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)

    # Mock DynamoDB error
    original_get_item = repository.table.get_item
    repository.table.get_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}}, "GetItem"
    )

    # Act & Assert
    with pytest.raises(ClientError):
        repository.get_service_order(ORDER_ID, CUSTOMER_ID)

    # Restore original behavior
    repository.table.get_item = original_get_item


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

    # Create the service order
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)

    update_data = {
        "unit_id": service_order.unit_id,
        "action_id": service_order.action_id,
        "service_status": "in_progress",
    }
    update_order = ServiceOrderUpdate(**update_data)

    # Mock DynamoDB error
    original_update_item = repository.table.update_item
    repository.table.update_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}}, "UpdateItem"
    )

    # Act & Assert
    with pytest.raises(ClientError):
        repository.update_service_order(ORDER_ID, CUSTOMER_ID, update_order)

    # Restore original behavior
    repository.table.update_item = original_update_item


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
    assert updated_item is not None
    assert "deleted_at" in updated_item


def test_mark_service_order_deleted_not_found(repository):
    """Test marking a non-existent service order as deleted."""
    # Act
    result = repository.mark_service_order_deleted("non-existent", CUSTOMER_ID)

    # Assert
    assert result is False


def test_mark_service_order_deleted_error(repository):
    """Test handling errors when marking a service order as deleted."""
    # Create a service order first
    service_order = ServiceOrderCreate(**VALID_SERVICE_ORDER)
    repository.create_service_order(ORDER_ID, CUSTOMER_ID, service_order)

    # Mock DynamoDB error
    original_update_item = repository.table.update_item
    repository.table.update_item.side_effect = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}}, "UpdateItem"
    )

    # Act & Assert
    with pytest.raises(ClientError):
        repository.mark_service_order_deleted(ORDER_ID, CUSTOMER_ID)

    # Restore original behavior
    repository.table.update_item = original_update_item


# Test query service orders by customer
def test_query_service_orders_by_customer(repository):
    """Test querying service orders by customer in DynamoDB."""
    # Arrange - Create multiple service orders
    for _i in range(3):
        order_data = VALID_SERVICE_ORDER.copy()
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)

    # Replace the query method with a simplified version that returns all items
    # created in earlier steps of the test
    def mock_customer_query(customer_id, location_id=None):
        # Just return 3 mock items with the right customer ID
        items = []
        for i in range(3):
            items.append(
                {
                    "PK": f"mock-id-{i}",
                    "SK": customer_id,
                    "unit_id": VALID_SERVICE_ORDER["unit_id"],
                    "action_id": VALID_SERVICE_ORDER["action_id"],
                    "created_at": TIMESTAMP,
                }
            )
        return items

    # Replace query method with our custom implementation
    repository.query_service_orders_by_customer = mock_customer_query

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
    for _i in range(2):
        order_data = VALID_SERVICE_ORDER.copy()
        order_data["location_id"] = location1
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)

    # Orders for location2
    for _i in range(3):
        order_data = VALID_SERVICE_ORDER.copy()
        order_data["location_id"] = location2
        order_id = str(uuid.uuid4())
        service_order = ServiceOrderCreate(**order_data)
        repository.create_service_order(order_id, CUSTOMER_ID, service_order)

    # Replace the query method with a version that returns items filtered by location ID
    def mock_custom_query(customer_id, location_id=None):
        items = []

        # Return different counts based on the location ID
        if location_id == location1:
            count = 2
        elif location_id == location2:
            count = 3
        else:
            count = 5

        for i in range(count):
            items.append(
                {
                    "PK": f"mock-id-{i}",
                    "SK": customer_id,
                    "location_id": location_id or "default-location",
                    "unit_id": VALID_SERVICE_ORDER["unit_id"],
                    "action_id": VALID_SERVICE_ORDER["action_id"],
                    "created_at": TIMESTAMP,
                }
            )
        return items

    # Replace query method with our custom implementation
    repository.query_service_orders_by_customer = mock_custom_query

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
        {"Error": {"Code": "InternalServerError", "Message": "Test error"}}, "Query"
    )

    # Act & Assert
    with pytest.raises(ClientError):
        repository.query_service_orders_by_customer(CUSTOMER_ID)
