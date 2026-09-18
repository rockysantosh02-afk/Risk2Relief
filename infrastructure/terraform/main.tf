# Terraform Infrastructure Blueprint for Risk2Relief Production Deployment

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment identifier (staging, production)"
  type        = string
  default     = "production"
}

# VPC Configuration
resource "aws_vpc" "risk2relief_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "risk2relief-vpc"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Subnet for Application
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.risk2relief_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "risk2relief-public-subnet"
  }
}

# Subnet for Isolated Database
resource "aws_subnet" "private_db_subnet" {
  vpc_id            = aws_vpc.risk2relief_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "risk2relief-db-subnet"
  }
}
