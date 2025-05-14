terraform {
  backend "s3" {
    bucket  = "srhoton-tfstate"
    key     = "service-order-lambda/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "service-order-lambda"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}