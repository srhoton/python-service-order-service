terraform {
  backend "s3" {
    bucket  = "triage-center-tf-state"
    key     = "service-order-lambda/terraform.tfstate"
    region  = "us-west-2"
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
