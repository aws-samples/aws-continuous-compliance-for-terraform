# Configure the AWS Provider
provider "aws" {
  version = "~> 3.9"
  profile = "default"
  region = var.region
}

terraform {
  backend "s3" {
    key            = "terraform.tfstate"
  }
}

provider "archive" {
}

variable "region" {
}
