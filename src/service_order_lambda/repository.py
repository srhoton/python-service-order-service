"""Service Order Repository.

This module handles interactions with the DynamoDB table for service orders.
It provides CRUD operations for service order management.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .config import config
from .models import (
    DynamoDBServiceOrder,
    ServiceOrderCreate,
    ServiceOrderUpdate,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ServiceOrderRepository:
    """Repository for service order operations in DynamoDB."""

    def __init__(self) -> None:
        """Initialize the repository with DynamoDB client."""
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(config.service_order_table_name)
    
    def create_service_order(
        self, order_id: str, customer_id: str, service_order: ServiceOrderCreate
    ) -> Dict:
        """Create a new service order in DynamoDB.
        
        Args:
            order_id: The UUID for the service order
            customer_id: The customer ID
            service_order: The service order data
            
        Returns:
            The created item as a dictionary
            
        Raises:
            ClientError: If there's an issue with the DynamoDB operation
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Create DynamoDB item from the service order model
        db_item = DynamoDBServiceOrder.from_service_order(
            order_id=uuid.UUID(order_id),
            customer_id=customer_id,
            service_order=service_order,
            timestamp=timestamp,
        )
        
        # Convert to dict for DynamoDB
        item_dict = db_item.dict(exclude_none=True)
        
        try:
            # Add to DynamoDB
            self.table.put_item(Item=item_dict)
            logger.info(f"Created service order {order_id} for customer {customer_id}")
            return item_dict
        except ClientError as e:
            logger.error(f"Failed to create service order: {str(e)}")
            raise
    
    def get_service_order(self, order_id: str, customer_id: str) -> Optional[Dict]:
        """Get a service order by ID and customer ID.
        
        Args:
            order_id: The UUID of the service order
            customer_id: The customer ID
            
        Returns:
            The service order item as a dictionary or None if not found
            
        Raises:
            ClientError: If there's an issue with the DynamoDB operation
        """
        try:
            response = self.table.get_item(
                Key={
                    "PK": order_id,
                    "SK": customer_id,
                }
            )
            item = response.get("Item")
            
            if not item:
                logger.info(f"Service order {order_id} for customer {customer_id} not found")
                return None
                
            logger.info(f"Retrieved service order {order_id} for customer {customer_id}")
            return item
        except ClientError as e:
            logger.error(f"Failed to get service order: {str(e)}")
            raise
    
    def update_service_order(
        self, order_id: str, customer_id: str, service_order: ServiceOrderUpdate
    ) -> Optional[Dict]:
        """Update an existing service order in DynamoDB.
        
        Args:
            order_id: The UUID of the service order
            customer_id: The customer ID
            service_order: The service order data for updating
            
        Returns:
            The updated item as a dictionary or None if not found
            
        Raises:
            ClientError: If there's an issue with the DynamoDB operation
        """
        # First check if the item exists
        existing_item = self.get_service_order(order_id, customer_id)
        if not existing_item:
            return None
        
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare update expression parts
        update_expr_parts = ["SET updated_at = :updated_at"]
        expr_attr_values = {":updated_at": timestamp}
        expr_attr_names = {}
        
        # Add fields from the service order model to the update expression
        model_dict = service_order.dict(exclude_unset=True, exclude_none=True)
        
        # Map model field names to DynamoDB attribute names
        field_mapping = {
            "unit_id": "unit_id", 
            "action_id": "action_id",
            "service_date": "service_date",
            "service_time": "service_time",
            "service_duration": "service_duration",
            "service_status": "service_status",
            "employee_id": "employee_id",
            "service_notes": "service_notes",
        }
        
        # Build the update expression
        for field, value in model_dict.items():
            if field in field_mapping:
                db_field = field_mapping[field]
                # Use attribute name placeholders to avoid reserved keywords
                expr_name = f"#{db_field}"
                expr_val = f":{db_field}"
                
                update_expr_parts.append(f"{expr_name} = {expr_val}")
                expr_attr_names[expr_name] = db_field
                
                # Convert UUIDs to strings for DynamoDB
                if field in ["unit_id", "action_id", "employee_id"] and value is not None:
                    expr_attr_values[expr_val] = str(value)
                else:
                    expr_attr_values[expr_val] = value
        
        # Combine all parts to form the final update expression
        update_expression = " ".join(update_expr_parts)
        
        try:
            response = self.table.update_item(
                Key={
                    "PK": order_id,
                    "SK": customer_id,
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expr_attr_values,
                ExpressionAttributeNames=expr_attr_names,
                ReturnValues="ALL_NEW",
            )
            
            updated_item = response.get("Attributes")
            logger.info(f"Updated service order {order_id} for customer {customer_id}")
            return updated_item
        except ClientError as e:
            logger.error(f"Failed to update service order: {str(e)}")
            raise
    
    def mark_service_order_deleted(self, order_id: str, customer_id: str) -> bool:
        """Mark a service order as deleted by setting the deleted_at timestamp.
        
        Args:
            order_id: The UUID of the service order
            customer_id: The customer ID
            
        Returns:
            True if the item was marked as deleted, False if not found
            
        Raises:
            ClientError: If there's an issue with the DynamoDB operation
        """
        # First check if the item exists
        existing_item = self.get_service_order(order_id, customer_id)
        if not existing_item:
            return False
        
        timestamp = datetime.utcnow().isoformat()
        
        try:
            self.table.update_item(
                Key={
                    "PK": order_id,
                    "SK": customer_id,
                },
                UpdateExpression="SET deleted_at = :deleted_at",
                ExpressionAttributeValues={
                    ":deleted_at": timestamp,
                },
                ReturnValues="ALL_NEW",
            )
            
            logger.info(f"Marked service order {order_id} for customer {customer_id} as deleted")
            return True
        except ClientError as e:
            logger.error(f"Failed to mark service order as deleted: {str(e)}")
            raise
    
    def query_service_orders_by_customer(
        self, customer_id: str, location_id: Optional[str] = None
    ) -> List[Dict]:
        """Query service orders by customer ID and optionally location ID.
        
        Args:
            customer_id: The customer ID
            location_id: Optional location ID to filter by
            
        Returns:
            A list of service order items
            
        Raises:
            ClientError: If there's an issue with the DynamoDB operation
        """
        try:
            # Base query parameters
            query_params = {
                "IndexName": "CustomerIndex",  # Assumes a GSI on SK (customer_id)
                "KeyConditionExpression": Key("SK").eq(customer_id),
            }
            
            # Add filter for location_id if provided
            if location_id:
                query_params["FilterExpression"] = Attr("location_id").eq(location_id)
            
            response = self.table.query(**query_params)
            items = response.get("Items", [])
            
            # Handle pagination if there are more results
            while "LastEvaluatedKey" in response:
                query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self.table.query(**query_params)
                items.extend(response.get("Items", []))
            
            logger.info(f"Retrieved {len(items)} service orders for customer {customer_id}")
            return items
        except ClientError as e:
            logger.error(f"Failed to query service orders by customer: {str(e)}")
            raise