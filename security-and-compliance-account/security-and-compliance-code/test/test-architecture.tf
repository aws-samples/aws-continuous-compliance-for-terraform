provider "aws" {
  profile = "default"
  region = "us-east-1"
}

provider "archive" {
}

################################################################################
# Ensure all resources have tags
# Ensure that specific tags are defined
################################################################################
resource "aws_instance" "tf-example-ec2" {
  ami                  = "ami-0323c3dd2da7fb37d"
  instance_type        = "t2.micro"
  iam_instance_profile = aws_iam_instance_profile.test_profile.name
  key_name             = "truist-ec2-key-pair"
  tags = {
    Name = "tf-eaxample-ec2"
  }
}

################################################################################
# Validate lambda function runtime environment for non-compliant runtime
# Ensure all resources have tags
# Ensure that specific tags are defined
################################################################################
data "archive_file" "ssm_tag_collector_zip" {
  type        = "zip"
  source_file = "${path.module}/files/ssmTagCollector.py"
  output_path = "${path.module}/files/ssmTagCollector.zip"
}

data template_file "ssm_tag_collector_lambda_role" {
  template = "${file("${path.module}/files/ssm_tag_collector_lambda_role.json")}"
}

resource "aws_iam_role" "ssm_tag_collector_role" {
  assume_role_policy = data.template_file.ssm_tag_collector_lambda_role.rendered
  tags = {
    Name = "ssm_tag_collector_role"
  }
}

resource "aws_lambda_function" "ssm_tag_collector_lambda" {
  filename         = data.archive_file.ssm_tag_collector_zip.output_path
  function_name    = "ssm-tag-collector"
  description      = "Send tags from the list of instances in the event context to the ssm-tag-manager lambda in parent account."
  role             = aws_iam_role.ssm_tag_collector_role.arn
  handler          = "ssmTagCollector.lambda_handler"
  source_code_hash = base64sha256("ssmTagCollector.zip")
  runtime          = "python3.6"
  timeout          = 25
  tags = {
    Name = "ssm_tag_collector_lambda"
  }
}
################################# END ##########################################


################################################################################
# API documentation check 1: API Documentation Part
# API documentation check 2: API Documentation Version
################################################################################
resource "aws_api_gateway_documentation_version" "example" {
  version     = "example_version"
  rest_api_id = aws_api_gateway_rest_api.tf_example_rest_api.id
  description = "Example description"
  depends_on  = [aws_api_gateway_documentation_part.example]
}

resource "aws_api_gateway_documentation_part" "example" {
  location {
    type   = "METHOD"
    method = "GET"
    path   = "/example"
  }
  properties  = "{\"description\":\"Example description\"}"
  rest_api_id = aws_api_gateway_rest_api.tf_example_rest_api.id
}

resource "aws_api_gateway_rest_api" "tf_example_rest_api" {
  name = "example_api"
  tags = {
    Name = "tf-example-rest-api"
  }
}
################################# END ##########################################