#!/bin/bash
set -e

# Configuration
LAMBDA_FUNCTION_NAME="service-order-lambda"
PACKAGE_NAME="lambda_function.zip"
PYTHON_VERSION="python3.13"
HANDLER="service_order_lambda.app.lambda_handler"
RUNTIME="python3.13"
REGION="us-east-1"  # Change to your preferred region

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment process for $LAMBDA_FUNCTION_NAME${NC}"

# Check if virtual environment exists, create if it doesn't
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_VERSION -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create a temporary build directory
echo -e "${YELLOW}Creating build directory...${NC}"
rm -rf build
mkdir -p build

# Copy source files to build directory
echo -e "${YELLOW}Copying source files...${NC}"
cp -r src/* build/

# Install dependencies in the build directory (for Lambda layer)
echo -e "${YELLOW}Installing dependencies in build directory...${NC}"
pip install -r requirements.txt --target ./build

# Create deployment package
echo -e "${YELLOW}Creating deployment package...${NC}"
cd build && zip -r ../$PACKAGE_NAME . && cd ..

# Check if the Lambda function exists
echo -e "${YELLOW}Checking if Lambda function exists...${NC}"
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION 2>&1 | grep -q "Function not found"; then
    # Create Lambda function
    echo -e "${YELLOW}Creating Lambda function...${NC}"
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --zip-file fileb://$PACKAGE_NAME \
        --role "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_EXECUTION_ROLE" \
        --region $REGION
    
    echo -e "${GREEN}Lambda function created successfully!${NC}"
else
    # Update Lambda function
    echo -e "${YELLOW}Updating Lambda function...${NC}"
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://$PACKAGE_NAME \
        --region $REGION
    
    echo -e "${GREEN}Lambda function updated successfully!${NC}"
fi

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --environment "Variables={APPCONFIG_APPLICATION_ID=your-app-id,APPCONFIG_ENVIRONMENT_ID=your-env-id,APPCONFIG_CONFIGURATION_PROFILE_ID=your-profile-id,LOG_LEVEL=INFO}" \
    --region $REGION

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -rf build
# Uncomment the line below if you want to remove the zip file after deployment
# rm $PACKAGE_NAME

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Deactivate virtual environment
deactivate