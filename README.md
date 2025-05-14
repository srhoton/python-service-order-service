# Service Order Lambda

This AWS Lambda function manages service orders through a RESTful API. It provides CRUD operations for service orders stored in DynamoDB, retrieving configuration from AWS AppConfig.

## Features

- Handles API Gateway and AppSync events
- Processes CRUD operations on service orders:
  - **Create**: Add new service orders with customer and location information
  - **Read**: Retrieve service orders by ID, customer, or location
  - **Update**: Modify existing service orders
  - **Delete**: Mark service orders as deleted (soft delete)
- DynamoDB integration for persistent storage
- AWS AppConfig integration for configuration management
- Comprehensive validation of request parameters
- Complete test suite for all components
- Support for Python 3.13+ with type hints, pattern matching, and modern language features

This project follows a modular implementation in the `src/` directory, adhering to Python best practices with:
- Type hints throughout the codebase
- Comprehensive docstrings
- Proper separation of concerns
- Extensive test coverage 
- Pydantic data validation

## API Endpoints

| HTTP Method | Path | Description |
|-------------|------|-------------|
| POST | /customers/{customerId}/service-orders?locationId={locationId} | Create a new service order |
| GET | /customers/{customerId}/service-orders | List all service orders for a customer |
| GET | /customers/{customerId}/service-orders?locationId={locationId} | List service orders for a customer at a specific location |
| GET | /customers/{customerId}/service-orders/{id} | Get a specific service order |
| PUT | /customers/{customerId}/service-orders/{id} | Update a service order |
| DELETE | /customers/{customerId}/service-orders/{id} | Delete a service order |

## Project Structure

### Modular Approach

```
service-order-lambda/
├── src/
│   ├── service_order_lambda/
│   │   ├── __init__.py
│   │   ├── app.py            # Lambda handler
│   │   ├── config.py         # Configuration management
│   │   ├── models.py         # Data models
│   │   ├── repository.py     # DynamoDB interactions
│   │   └── validators.py     # Request validation
├── tests/
│   ├── __init__.py
│   ├── test_app.py           # Handler tests
│   ├── test_models.py        # Model tests
│   ├── test_repository.py    # Repository tests
│   └── test_validators.py    # Validator tests
├── pyproject.toml            # Project configuration
└── requirements.txt          # Dependencies
```


## Setup and Deployment

### Prerequisites

- Python 3.13 or higher
- AWS CLI configured with appropriate permissions
- AWS AppConfig setup with the following configuration:
  - `serviceOrderTableName`: Name of the DynamoDB table for service orders

### Python 3.13 Features

This service leverages several Python 3.13 features:
- Modern type annotations with `TypedDict` for structured API responses
- Pattern matching for more concise validation logic
- Improved error handling with structured exceptions
- Better performance characteristics of Python 3.13 runtime

### Environment Variables

The Lambda requires the following environment variables:

- `APPCONFIG_APPLICATION_ID`: The AWS AppConfig application ID
- `APPCONFIG_ENVIRONMENT_ID`: The AWS AppConfig environment ID
- `APPCONFIG_CONFIGURATION_PROFILE_ID`: The AWS AppConfig configuration profile ID
- `LOG_LEVEL`: (Optional) The logging level (default: INFO)

### Local Development

1. Create a Python virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run tests:
   ```
   pytest
   ```

4. Deploy with provided script:
   ```
   ./deploy.sh
   ```
   This script creates a deployment package optimized for Python 3.13 Lambda runtime.

### Deployment

#### Option 1: Deploy the Modular Version

1. Package the Lambda function:
   ```
   cd src
   zip -r ../lambda_function.zip .
   cd ..
   ```

2. Deploy to AWS Lambda:
   ```
   aws lambda create-function \
     --function-name service-order-lambda \
     --runtime python3.13 \
     --handler service_order_lambda.app.lambda_handler \
     --zip-file fileb://lambda_function.zip \
     --role <your-lambda-execution-role-arn>
   ```

#### Python 3.13 Lambda Runtime Considerations

When deploying to AWS Lambda with Python 3.13:

- Lambda cold starts are faster with Python 3.13 compared to older versions
- Ensure your dependencies are compatible with Python 3.13
- Set memory appropriately (minimum 256MB recommended)
- Consider setting reserved concurrency for production workloads
- The deployment package size limit is 50MB zipped, 250MB unzipped


## Testing

The project includes comprehensive unit tests for all components. To run the tests:

```
# For modular implementation
pytest


```

To generate coverage reports:

```
# For modular implementation
pytest --cov=src/service_order_lambda --cov-report=term-missing --cov-report=xml


```

**Note:** When testing locally, you may need to configure AWS credentials for tests that interact with AWS services, or use mocking as shown in the test files.
