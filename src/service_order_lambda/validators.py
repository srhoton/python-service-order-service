"""Request validators for the Service Order Lambda.

This module contains validation functions for API requests
to the service order Lambda function. Compatible with Python 3.13+.
"""

import logging
import re
import uuid
from typing import Any, Dict, Optional, Tuple, TypeAlias, TypedDict

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Regular expression for ISO 8601 date validation
ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Regular expression for ISO 8601 time validation
ISO_TIME_REGEX = re.compile(r"^(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")

# Type aliases for improved readability
UUIDValidationResult: TypeAlias = Tuple[bool, Optional[uuid.UUID]]
ValidationResult: TypeAlias = Tuple[bool, Optional[str]]


# TypedDict definitions for more structured return types
class CreateValidationResult(TypedDict):
    """Result type for create validation."""

    is_valid: bool
    body: Optional[Dict[str, Any]]
    error: Optional[str]


class UpdateValidationResult(TypedDict):
    """Result type for update validation."""

    is_valid: bool
    body: Optional[Dict[str, Any]]
    customer_id: Optional[str]
    error: Optional[str]


class DeleteValidationResult(TypedDict):
    """Result type for delete validation."""

    is_valid: bool
    order_id: Optional[str]
    customer_id: Optional[str]
    error: Optional[str]


class GetValidationResult(TypedDict):
    """Result type for get validation."""

    is_valid: bool
    order_id: Optional[str]
    customer_id: Optional[str]
    location_id: Optional[str]
    error: Optional[str]


def validate_uuid(uuid_str: str) -> UUIDValidationResult:
    """Validate a UUID string.

    Args:
        uuid_str: The UUID string to validate

    Returns:
        A tuple containing a boolean indicating if the UUID is valid,
        and the parsed UUID object if valid, None otherwise
    """
    try:
        parsed_uuid = uuid.UUID(uuid_str)
        return True, parsed_uuid
    except (ValueError, AttributeError, TypeError):
        logger.warning(f"Invalid UUID format: {uuid_str}")
        return False, None


def validate_iso_date(date_str: Optional[str]) -> bool:
    """Validate an ISO 8601 date string (YYYY-MM-DD).

    Args:
        date_str: The date string to validate

    Returns:
        True if the date is valid ISO 8601 format, False otherwise
    """
    match date_str:
        case None:
            return True
        case str() as date:
            return bool(ISO_DATE_REGEX.match(date))
        case _:
            return False


def validate_iso_time(time_str: Optional[str]) -> bool:
    """Validate an ISO 8601 time string.

    Args:
        time_str: The time string to validate

    Returns:
        True if the time is valid ISO 8601 format, False otherwise
    """
    match time_str:
        case None:
            return True
        case str() as time if not ISO_TIME_REGEX.match(time):
            return False
        case str() as time:
            # Additional checks for valid time values
            try:
                # Extract hour value from time string
                hour = int(time.split(":")[0])
                # Valid hours are 0-23
                return 0 <= hour <= 23
            except (ValueError, IndexError):
                return False
        case _:
            return False


def _validate_request_common(body: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate common fields for service order requests.

    Args:
        body: The request body to validate

    Returns:
        A tuple containing:
        - Boolean indicating if the request is valid
        - Error message if validation failed, None otherwise
    """
    # Check for required fields
    if "unit_id" not in body:
        return False, "Missing required field: unit_id"

    if "action_id" not in body:
        return False, "Missing required field: action_id"

    # Validate UUID fields
    for field in ["unit_id", "action_id", "employee_id"]:
        if value := body.get(field):
            is_valid, parsed_uuid = validate_uuid(str(value))
            if not is_valid:
                return False, f"Invalid UUID format for {field}"
            # Convert string to UUID object
            body[field] = parsed_uuid

    # Validate date and time fields
    if "service_date" in body and not validate_iso_date(body["service_date"]):
        return False, "Invalid ISO 8601 format for service_date"

    if "service_time" in body and not validate_iso_time(body["service_time"]):
        return False, "Invalid ISO 8601 format for service_time"

    # Validate service_duration is an integer
    if "service_duration" in body:
        try:
            body["service_duration"] = int(body["service_duration"])
        except (ValueError, TypeError):
            return False, "service_duration must be an integer"

    return True, None


def validate_create_request(event: Dict[str, Any]) -> CreateValidationResult:
    """Validate a service order creation request.

    Args:
        event: The event received by the Lambda function

    Returns:
        A validation result containing:
        - is_valid: Boolean indicating if the request is valid
        - body: Validated request body if valid, None otherwise
        - error: Error message if validation failed, None otherwise
    """
    # Check path parameters for customer_id
    path_params = event.get("pathParameters", {}) or {}
    customer_id = path_params.get("customerId")

    if not customer_id:
        return {"is_valid": False, "body": None, "error": "Missing customerId in path parameters"}

    # Check for request body
    body = event.get("body")
    if not body:
        return {"is_valid": False, "body": None, "error": "Missing request body"}

    # Parse request body (assuming it's already parsed from JSON)
    if isinstance(body, str):
        import json

        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return {"is_valid": False, "body": None, "error": "Invalid JSON in request body"}

    # Check for required location_id in query parameters
    query_params = event.get("queryStringParameters", {}) or {}
    location_id = query_params.get("locationId")

    if not location_id:
        return {"is_valid": False, "body": None, "error": "Missing locationId in query parameters"}

    # Add location_id to the body
    body["location_id"] = location_id

    # Validate common fields
    is_valid, error_msg = _validate_request_common(body)
    if not is_valid:
        return {"is_valid": False, "body": None, "error": error_msg}

    return {"is_valid": True, "body": body, "error": None}


def validate_update_request(event: Dict[str, Any]) -> UpdateValidationResult:
    """Validate a service order update request.

    Args:
        event: The event received by the Lambda function

    Returns:
        A validation result containing:
        - is_valid: Boolean indicating if the request is valid
        - body: Validated request body if valid, None otherwise
        - customer_id: Customer ID if valid, None otherwise
        - error: Error message if validation failed, None otherwise
    """
    # Check path parameters for service_order_id and customer_id
    path_params = event.get("pathParameters", {}) or {}
    service_order_id = path_params.get("id")
    customer_id = path_params.get("customerId")

    if not service_order_id:
        return {
            "is_valid": False,
            "body": None,
            "customer_id": None,
            "error": "Missing service order id in path parameters",
        }

    # Validate service_order_id is a valid UUID
    is_valid, _ = validate_uuid(service_order_id)
    if not is_valid:
        return {
            "is_valid": False,
            "body": None,
            "customer_id": None,
            "error": "Invalid UUID format for service order id",
        }

    if not customer_id:
        return {
            "is_valid": False,
            "body": None,
            "customer_id": None,
            "error": "Missing customerId in path parameters",
        }

    # Check for request body and parse it
    match event.get("body"):
        case None:
            return {
                "is_valid": False,
                "body": None,
                "customer_id": None,
                "error": "Missing request body",
            }
        case str() as json_str:
            import json

            try:
                body = json.loads(json_str)
            except json.JSONDecodeError:
                return {
                    "is_valid": False,
                    "body": None,
                    "customer_id": None,
                    "error": "Invalid JSON in request body",
                }
        case body:
            pass  # body is already parsed

    # Validate common fields
    is_valid, error_msg = _validate_request_common(body)
    if not is_valid:
        return {"is_valid": False, "body": None, "customer_id": None, "error": error_msg}

    return {"is_valid": True, "body": body, "customer_id": customer_id, "error": None}


def validate_delete_request(event: Dict[str, Any]) -> DeleteValidationResult:
    """Validate a service order deletion request.

    Args:
        event: The event received by the Lambda function

    Returns:
        A validation result containing:
        - is_valid: Boolean indicating if the request is valid
        - order_id: Service order ID if valid, None otherwise
        - customer_id: Customer ID if valid, None otherwise
        - error: Error message if validation failed, None otherwise
    """
    # Check path parameters for service_order_id and customer_id
    path_params = event.get("pathParameters", {}) or {}

    service_order_id = path_params.get("id")
    customer_id = path_params.get("customerId")

    # Check for missing service order ID
    if service_order_id is None:
        return {
            "is_valid": False,
            "order_id": None,
            "customer_id": None,
            "error": "Missing service order id in path parameters",
        }

    # Check for missing customer ID
    if customer_id is None:
        return {
            "is_valid": False,
            "order_id": None,
            "customer_id": None,
            "error": "Missing customerId in path parameters",
        }

    # Validate service_order_id is a valid UUID
    is_valid, _ = validate_uuid(str(service_order_id))
    if not is_valid:
        return {
            "is_valid": False,
            "order_id": None,
            "customer_id": None,
            "error": "Invalid UUID format for service order id",
        }

    # All validations passed
    return {
        "is_valid": True,
        "order_id": service_order_id,
        "customer_id": customer_id,
        "error": None,
    }


def validate_get_request(event: Dict[str, Any]) -> GetValidationResult:
    """Validate a service order retrieval request.

    Args:
        event: The event received by the Lambda function

    Returns:
        A validation result containing:
        - is_valid: Boolean indicating if the request is valid
        - order_id: Service order ID if provided, None otherwise
        - customer_id: Customer ID if valid, None otherwise
        - location_id: Location ID if provided, None otherwise
        - error: Error message if validation failed, None otherwise
    """
    # Check path parameters for customer_id and optionally service_order_id
    path_params = event.get("pathParameters", {}) or {}
    service_order_id = path_params.get("id")
    customer_id = path_params.get("customerId")

    if not customer_id:
        return {
            "is_valid": False,
            "order_id": None,
            "customer_id": None,
            "location_id": None,
            "error": "Missing customerId in path parameters",
        }

    # Check query parameters for optional location_id
    query_params = event.get("queryStringParameters", {}) or {}
    location_id = query_params.get("locationId")

    # Validate service_order_id is a valid UUID if provided
    if service_order_id:
        is_valid, _ = validate_uuid(str(service_order_id))
        if not is_valid:
            return {
                "is_valid": False,
                "order_id": None,
                "customer_id": None,
                "location_id": None,
                "error": "Invalid UUID format for service order id",
            }

    return {
        "is_valid": True,
        "order_id": service_order_id,
        "customer_id": customer_id,
        "location_id": location_id,
        "error": None,
    }
