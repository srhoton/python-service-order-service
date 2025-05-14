"""Lambda handler for service order operations.

This module contains the AWS Lambda handler for processing service orders
through CRUD operations on a DynamoDB table.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from .config import config
from .models import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    DynamoDBServiceOrder,
)
from .repository import ServiceOrderRepository
from .validators import (
    validate_create_request,
    validate_update_request,
    validate_delete_request,
    validate_get_request,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_response(
    status_code: int, body: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """Create a response object for API Gateway.
    
    Args:
        status_code: HTTP status code
        body: Response body (optional)
        
    Returns:
        A formatted response object
    """
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
        },
    }
    
    if body is not None:
        response["body"] = json.dumps(body, default=str)
    
    return response


def handle_create_request(event: Dict[str, Any], repo: ServiceOrderRepository) -> Dict[str, Any]:
    """Handle a service order creation request.
    
    Args:
        event: The Lambda event
        repo: The service order repository
        
    Returns:
        The API Gateway response
    """
    # Validate the request
    is_valid, body, error_message = validate_create_request(event)
    if not is_valid:
        return create_response(400, {"error": error_message})
    
    # Get customer_id from path parameters
    customer_id = event.get("pathParameters", {}).get("customerId")
    
    try:
        # Create Pydantic model from request body
        service_order = ServiceOrderCreate.model_validate(body)
        
        # Generate a new UUID for the service order
        order_id = str(uuid.uuid4())
        
        # Create the service order in DynamoDB
        item = repo.create_service_order(order_id, customer_id, service_order)
        
        # Convert to response model
        db_item = DynamoDBServiceOrder(**item)
        response_model = db_item.to_response_model()
        
        # Return the created service order
        return create_response(201, response_model.model_dump())
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return create_response(400, {"error": str(e)})
    except Exception as e:
        logger.error(f"Error creating service order: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def handle_update_request(event: Dict[str, Any], repo: ServiceOrderRepository) -> Dict[str, Any]:
    """Handle a service order update request.
    
    Args:
        event: The Lambda event
        repo: The service order repository
        
    Returns:
        The API Gateway response
    """
    # Validate the request
    is_valid, body, customer_id, error_message = validate_update_request(event)
    if not is_valid:
        return create_response(400, {"error": error_message})
    
    # Get order_id from path parameters
    order_id = event.get("pathParameters", {}).get("id")
    
    try:
        # Create Pydantic model from request body
        service_order = ServiceOrderUpdate.model_validate(body)
        
        # Update the service order in DynamoDB
        # We know customer_id is not None because we passed validation
        assert customer_id is not None
        updated_item = repo.update_service_order(order_id, customer_id, service_order)
        
        if not updated_item:
            return create_response(404, {"error": "Service order not found"})
        
        # Convert to response model
        db_item = DynamoDBServiceOrder(**updated_item)
        response_model = db_item.to_response_model()
        
        # Return the updated service order
        return create_response(200, response_model.model_dump())
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return create_response(400, {"error": str(e)})
    except Exception as e:
        logger.error(f"Error updating service order: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def handle_delete_request(event: Dict[str, Any], repo: ServiceOrderRepository) -> Dict[str, Any]:
    """Handle a service order deletion request.
    
    Args:
        event: The Lambda event
        repo: The service order repository
        
    Returns:
        The API Gateway response
    """
    # Validate the request
    is_valid, order_id, customer_id, error_message = validate_delete_request(event)
    if not is_valid:
        return create_response(400, {"error": error_message})
    
    try:
        # Mark the service order as deleted in DynamoDB
        # We know order_id and customer_id are not None because we passed validation
        assert order_id is not None
        assert customer_id is not None
        success = repo.mark_service_order_deleted(order_id, customer_id)
        
        if not success:
            return create_response(404, {"error": "Service order not found"})
        
        # Return success with no content
        return create_response(204)
    except Exception as e:
        logger.error(f"Error deleting service order: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def handle_get_request(event: Dict[str, Any], repo: ServiceOrderRepository) -> Dict[str, Any]:
    """Handle a service order retrieval request.
    
    Args:
        event: The Lambda event
        repo: The service order repository
        
    Returns:
        The API Gateway response
    """
    # Validate the request
    is_valid, order_id, customer_id, location_id, error_message = validate_get_request(event)
    if not is_valid:
        return create_response(400, {"error": error_message})
    
    try:
        # If order_id is provided, retrieve a specific service order
        if order_id:
            # We know customer_id is not None because we passed validation
            assert customer_id is not None
            item = repo.get_service_order(order_id, customer_id)
            
            if not item:
                return create_response(404, {"error": "Service order not found"})
            
            # Convert to response model
            db_item = DynamoDBServiceOrder(**item)
            response_model = db_item.to_response_model()
            
            # Return the service order
            return create_response(200, response_model.model_dump())
        
        # Otherwise, query service orders for the customer, optionally filtered by location_id
        # We know customer_id is not None because we passed validation
        assert customer_id is not None
        items = repo.query_service_orders_by_customer(customer_id, location_id)
        
        # Convert all items to response models
        response_models = []
        for item in items:
            db_item = DynamoDBServiceOrder(**item)
            response_model = db_item.to_response_model()
            response_models.append(response_model.model_dump())
        
        # Return the service orders
        return create_response(200, response_models)
    except Exception as e:
        logger.error(f"Error retrieving service order(s): {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for service order operations.
    
    This function handles the following HTTP methods:
    - POST: Create a new service order
    - PUT: Update an existing service order
    - DELETE: Mark a service order as deleted
    - GET: Retrieve service order(s)
    
    Args:
        event: The Lambda event from API Gateway or AppSync
        context: The Lambda context
        
    Returns:
        The response to be returned to the client
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    # Extract the HTTP method
    http_method = event.get("httpMethod")
    
    # Handle OPTIONS requests for CORS
    if http_method == "OPTIONS":
        return create_response(200)
    
    # Initialize the repository
    repo = ServiceOrderRepository()
    
    # Handle CRUD operations
    if http_method == "POST":
        return handle_create_request(event, repo)
    elif http_method == "PUT":
        return handle_update_request(event, repo)
    elif http_method == "DELETE":
        return handle_delete_request(event, repo)
    elif http_method == "GET":
        return handle_get_request(event, repo)
    else:
        # Unsupported HTTP method
        return create_response(405, {"error": "Method not allowed"})