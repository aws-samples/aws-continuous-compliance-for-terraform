################################################################################
# Validate lambda function runtime environment for non-compliant runtime
# Ensure all resources have tags
# Ensure that specific tags are defined
################################################################################
data "archive_file" "demo_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/files/demo_lambda.py"
  output_path = "${path.module}/files/demo_lambda.zip"
}

data template_file "demo_lambda_role" {
  template = "${file("${path.module}/files/demo_lambda_role.json")}"
}

resource "aws_iam_role" "demo_lambda_role" {
  assume_role_policy = "${data.template_file.demo_lambda_role.rendered}"
  tags = {
    Name = "demo_lambda_role"
  }
}

resource "aws_lambda_function" "demo_lambda" {
  filename         = "${data.archive_file.demo_lambda_zip.output_path}"
  function_name    = "demo-lambda"
  description      = "Hello world."
  role             = "${aws_iam_role.demo_lambda_role.arn}"
  handler          = "demo_lambda.lambda_handler"
  source_code_hash = "${base64sha256("demo_lambda.zip")}"
  runtime          = "python3.6"
  timeout          = 25
  tags = {
    Name = "demo_lambda"
  }
}
################################# END ##########################################
