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

#### Option 3: Deploy with Terraform

This project includes Terraform configurations to automate the deployment of all necessary AWS resources:

1. Set up AWS credentials:
   ```bash
   aws configure
   ```

2. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

3. Review the execution plan:
   ```bash
   terraform plan
   ```

4. Apply the configuration:
   ```bash
   terraform apply
   ```

5. To destroy the resources when no longer needed:
   ```bash
   terraform destroy
   ```

##### Terraform Resources

The Terraform configuration creates the following resources:

- **DynamoDB Table**: For storing service orders with proper indexes
- **AWS AppConfig**: Application, environment, configuration profile and deployment
- **S3 Bucket**: For storing Lambda deployment packages
- **Lambda Function**: With proper IAM roles and permissions
- **CloudWatch Log Group**: For Lambda function logs

##### Configuration

You can customize the deployment by modifying variables in `terraform/variables.tf` or by creating a `terraform.tfvars` file with your preferred values:

```hcl
# Example terraform.tfvars
aws_region = "us-west-2"
environment = "prod"
service_name = "service-order"
dynamodb_billing_mode = "PROVISIONED"
dynamodb_read_capacity = 10
dynamodb_write_capacity = 10
lambda_memory_size = 512
lambda_timeout = 60
```

The Terraform state is stored in the S3 bucket `srhoton-tfstate` to enable team collaboration.


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

## Infrastructure as Code

### Terraform Configuration

This project uses Terraform to provision and manage the required AWS infrastructure. The Terraform configuration is located in the `terraform/` directory and is structured as follows:

```
terraform/
├── providers.tf       # AWS provider configuration and S3 backend
├── variables.tf       # Input variables
├── locals.tf          # Local variables and derived values
├── dynamodb.tf        # DynamoDB table for service orders
├── appconfig.tf       # AWS AppConfig resources for configuration
├── s3.tf              # S3 bucket for Lambda deployment packages
├── lambda.tf          # Lambda function and related resources
└── outputs.tf         # Output values from the deployment
```

### Infrastructure Components

The Terraform configuration provisions the following AWS resources:

1. **DynamoDB Table**:
   - Primary key: PK (service order UUID)
   - Sort key: SK (customer ID)
   - Global Secondary Index (GSI): CustomerIndex on the SK field
   - Point-in-time recovery enabled

2. **AWS AppConfig**:
   - Application, Environment, and Configuration Profile
   - Hosted configuration with DynamoDB table name
   - Deployment strategy for configuration updates

3. **S3 Bucket**:
   - Secure configuration with encryption and versioning
   - Used for storing Lambda deployment packages

4. **Lambda Function**:
   - Python 3.13 runtime
   - Environment variables for AppConfig integration
   - IAM role with necessary permissions for DynamoDB and AppConfig
   - CloudWatch Log Group for monitoring

### Managing Infrastructure

For detailed instructions on deploying and managing the infrastructure, see the deployment section above.
