"""Unit tests for the service order Lambda handler.

This module contains tests for the Lambda handler functions in app.py
to verify proper handling of service order CRUD operations.
"""

import json
import os
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from unittest import mock

import pytest

from src.service_order_lambda.app import lambda_handler, handle_create_request, handle_update_request, handle_delete_request, handle_get_request


# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with mock.patch.dict(os.environ, {
        "APPCONFIG_APPLICATION_ID": "test-app-id",
        "APPCONFIG_ENVIRONMENT_ID": "test-env-id",
        "APPCONFIG_CONFIGURATION_PROFILE_ID": "test-profile-id",
        "LOG_LEVEL": "INFO"
    }):
        yield

# Mock AWS clients
@pytest.fixture(autouse=True)
def mock_aws_services():
    """Mock all AWS services for testing."""
    # Mock AppConfig client
    with mock.patch("boto3.client") as mock_client:
        mock_app_config = mock.MagicMock()
        mock_content = mock.MagicMock()
        mock_content.read.return_value = json.dumps({"serviceOrderTableName": "test_service_orders"})
        mock_app_config.get_configuration.return_value = {"Content": mock_content}
        mock_client.return_value = mock_app_config
        
        # Mock DynamoDB
        with mock.patch("boto3.resource") as mock_resource:
            mock_table = mock.MagicMock()
            mock_resource.return_value.Table.return_value = mock_table
            
            # Set return values for mock table methods
            mock_table.get_item.return_value = {}
            mock_table.put_item.return_value = {}
            mock_table.update_item.return_value = {}
            mock_table.query.return_value = {"Items": []}
            
            yield mock_table

# Mock repository for testing
@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    mock_repo = mock.MagicMock()
    return mock_repo


# Helper function to create a mock API Gateway event
def create_api_gateway_event(
    http_method: str,
    path_params: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a mock API Gateway event for testing.
    
    Args:
        http_method: The HTTP method (GET, POST, PUT, DELETE)
        path_params: The path parameters
        query_params: The query string parameters
        body: The request body
        
    Returns:
        A mock API Gateway event
    """
    event = {
        "httpMethod": http_method,
        "pathParameters": path_params or {},
        "queryStringParameters": query_params or {},
    }
    
    if body:
        event["body"] = json.dumps(body)
    
    return event


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
}

DB_SERVICE_ORDER = {
    "PK": ORDER_ID,
    "SK": CUSTOMER_ID,
    "unit_id": VALID_SERVICE_ORDER["unit_id"],
    "action_id": VALID_SERVICE_ORDER["action_id"],
    "service_date": VALID_SERVICE_ORDER["service_date"],
    "service_time": VALID_SERVICE_ORDER["service_time"],
    "service_duration": VALID_SERVICE_ORDER["service_duration"],
    "service_status": VALID_SERVICE_ORDER["service_status"],
    "employee_id": VALID_SERVICE_ORDER["employee_id"],
    "service_notes": VALID_SERVICE_ORDER["service_notes"],
    "location_id": LOCATION_ID,
    "created_at": TIMESTAMP,
}


# Test create service order
def test_create_service_order_success(mock_repository):
    """Test successful service order creation."""
    # Arrange
    event = create_api_gateway_event(
        http_method="POST",
        path_params={"customerId": CUSTOMER_ID},
        query_params={"locationId": LOCATION_ID},
        body=VALID_SERVICE_ORDER,
    )
    
    # Configure mock
    mock_repository.create_service_order.return_value = DB_SERVICE_ORDER
    
    # Act
    with mock.patch("uuid.uuid4", return_value=uuid.UUID(ORDER_ID)):
        with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
            response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 201
    response_body = json.loads(response["body"])
    assert response_body["id"] == ORDER_ID
    assert response_body["customer_id"] == CUSTOMER_ID
    assert response_body["unit_id"] == VALID_SERVICE_ORDER["unit_id"]
    assert response_body["action_id"] == VALID_SERVICE_ORDER["action_id"]


def test_create_service_order_missing_customer_id(mock_aws_services, mock_repository):
    """Test service order creation with missing customer ID."""
    # Arrange
    event = create_api_gateway_event(
        http_method="POST",
        path_params={},  # Missing customerId
        query_params={"locationId": LOCATION_ID},
        body=VALID_SERVICE_ORDER,
    )
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Missing customerId" in response_body["error"]


def test_create_service_order_missing_location_id(mock_aws_services, mock_repository):
    """Test service order creation with missing location ID."""
    # Arrange
    event = create_api_gateway_event(
        http_method="POST",
        path_params={"customerId": CUSTOMER_ID},
        query_params={},  # Missing locationId
        body=VALID_SERVICE_ORDER,
    )
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Missing locationId" in response_body["error"]


def test_create_service_order_missing_required_fields(mock_aws_services, mock_repository):
    """Test service order creation with missing required fields."""
    # Arrange
    invalid_body = {
        "service_date": "2023-06-15",
        "service_notes": "Test service order",
    }
    
    event = create_api_gateway_event(
        http_method="POST",
        path_params={"customerId": CUSTOMER_ID},
        query_params={"locationId": LOCATION_ID},
        body=invalid_body,
    )
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Missing required field" in response_body["error"]


# Test update service order
def test_update_service_order_success(mock_repository):
    """Test successful service order update."""
    # Arrange
    update_body = {
        "unit_id": VALID_SERVICE_ORDER["unit_id"],
        "action_id": VALID_SERVICE_ORDER["action_id"],
        "service_status": "in_progress",
        "service_notes": "Updated notes",
    }
    
    event = create_api_gateway_event(
        http_method="PUT",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
        body=update_body,
    )
    
    # Updated service order in DB
    updated_db_item = DB_SERVICE_ORDER.copy()
    updated_db_item["service_status"] = "in_progress"
    updated_db_item["service_notes"] = "Updated notes"
    updated_db_item["updated_at"] = TIMESTAMP
    
    # Configure mock
    mock_repository.update_service_order.return_value = updated_db_item
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["id"] == ORDER_ID
    assert response_body["service_status"] == "in_progress"
    assert response_body["service_notes"] == "Updated notes"


def test_update_service_order_not_found(mock_repository, mock_aws_services):
    """Test updating a non-existent service order."""
    # Arrange
    event = create_api_gateway_event(
        http_method="PUT",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
        body=VALID_SERVICE_ORDER,
    )
    
    # Configure mock
    mock_repository.update_service_order.return_value = None
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "not found" in response_body["error"]


# Test delete service order
def test_delete_service_order_success(mock_repository, mock_aws_services):
    """Test successful service order deletion."""
    # Arrange
    event = create_api_gateway_event(
        http_method="DELETE",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
    )
    
    # Configure mock
    mock_repository.mark_service_order_deleted.return_value = True
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 204
    assert "body" not in response


def test_delete_service_order_not_found(mock_repository, mock_aws_services):
    """Test deleting a non-existent service order."""
    # Arrange
    event = create_api_gateway_event(
        http_method="DELETE",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
    )
    
    # Configure mock
    mock_repository.mark_service_order_deleted.return_value = False
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "not found" in response_body["error"]


# Test get service order
def test_get_service_order_by_id_success(mock_repository, mock_aws_services):
    """Test successful retrieval of a specific service order."""
    # Arrange
    event = create_api_gateway_event(
        http_method="GET",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
    )
    
    # Configure mock
    mock_repository.get_service_order.return_value = DB_SERVICE_ORDER
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["id"] == ORDER_ID
    assert response_body["customer_id"] == CUSTOMER_ID


def test_get_service_order_by_id_not_found(mock_repository, mock_aws_services):
    """Test retrieval of a non-existent service order."""
    # Arrange
    event = create_api_gateway_event(
        http_method="GET",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
    )
    
    # Configure mock
    mock_repository.get_service_order.return_value = None
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "not found" in response_body["error"]


def test_get_service_orders_by_customer(mock_repository, mock_aws_services):
    """Test retrieval of all service orders for a customer."""
    # Arrange
    event = create_api_gateway_event(
        http_method="GET",
        path_params={"customerId": CUSTOMER_ID},
    )
    
    # Create multiple DB items
    db_items = [
        DB_SERVICE_ORDER,
        {**DB_SERVICE_ORDER, "PK": str(uuid.uuid4()), "service_status": "completed"}
    ]
    
    # Configure mock
    mock_repository.query_service_orders_by_customer.return_value = db_items
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert isinstance(response_body, list)
    assert len(response_body) == 2
    assert response_body[0]["customer_id"] == CUSTOMER_ID
    assert response_body[1]["customer_id"] == CUSTOMER_ID


def test_get_service_orders_by_location(mock_repository, mock_aws_services):
    """Test retrieval of service orders filtered by location."""
    # Arrange
    event = create_api_gateway_event(
        http_method="GET",
        path_params={"customerId": CUSTOMER_ID},
        query_params={"locationId": LOCATION_ID},
    )
    
    # Configure mock
    mock_repository.query_service_orders_by_customer.return_value = [DB_SERVICE_ORDER]
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert isinstance(response_body, list)
    assert len(response_body) == 1
    assert response_body[0]["location_id"] == LOCATION_ID


# Test error handling
def test_method_not_allowed(mock_aws_services, mock_repository):
    """Test handling of unsupported HTTP methods."""
    # Arrange
    event = create_api_gateway_event(http_method="PATCH")
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 405
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Method not allowed" in response_body["error"]


def test_internal_server_error(mock_repository, mock_aws_services):
    """Test handling of internal server errors."""
    # Arrange
    event = create_api_gateway_event(
        http_method="GET",
        path_params={"id": ORDER_ID, "customerId": CUSTOMER_ID},
    )
    
    # Configure mock to raise an exception
    # Mock the repository to raise an exception
    mock_repository.get_service_order.side_effect = Exception("Database error")
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Internal server error" in response_body["error"]


def test_options_request(mock_aws_services, mock_repository):
    """Test handling of OPTIONS requests for CORS."""
    # Arrange
    event = create_api_gateway_event(http_method="OPTIONS")
    
    # Act
    with mock.patch("src.service_order_lambda.app.ServiceOrderRepository", return_value=mock_repository):
        response = lambda_handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in response["headers"]
    assert "Access-Control-Allow-Methods" in response["headers"]