resource "aws_cloudwatch_log_subscription_filter" "test_lambdafunction_logfilter" {
  name            = "test_lambdafunction_logfilter"
  role_arn        = "arn:aws:iam::<account-number>:role:lambda-role"
  log_group_name  = "/aws/lambda/example_lambda_name"
  filter_pattern  = "logtype test"
  destination_arn = "central-log-stream-arn"
  distribution    = "Random"
}

resource "aws_flow_log" "example-flow-log-1" {
  log_destination      = "${aws_s3_bucket.example-s3-flow-log-bucket.arn}"
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = "vpc-765873656"
  tags = {
    Name = "example-flow-log-1"
  }
}

resource "aws_kms_key" "mykey" {
  description             = "This key is used to encrypt bucket objects"
  deletion_window_in_days = 10
  tags = {
    Name = "example-s3-bucket-encryption-key"
    Environment = "test"
  }
}

resource "aws_s3_bucket" "example-s3-flow-log-bucket" {
  bucket = "example"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = "${aws_kms_key.mykey.arn}"
        sse_algorithm     = "aws:kms"
      }
    }
  }
  lifecycle_rule {
    prefix  = "config/"
    enabled = true

    noncurrent_version_transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      days          = 60
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      days = 90
    }
  }
  tags = {
    Name = "example-s3-flow-log-bucket"
  }
}

resource "aws_flow_log" "example-flow-log-2" {
  log_destination      = "arn:aws:cloudwatch:us-east-1:111111111111:log:vpc/flowlog"
  traffic_type         = "ALL"
  vpc_id               = "vpc-111111111"
  tags = {
    Name = "example-flow-log-2"
  }
}

#######################################################
# Scenario: Ensure that CLoudFront has logging enabled
#######################################################
resource "aws_s3_bucket" "c" {
  bucket = "mybucket"
  acl    = "private"
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "AES256"
      }
    }
  }

  lifecycle_rule {
    id      = "tmp"
    prefix  = "tmp/"
    enabled = true

    expiration {
      date = "2021-01-12"
    }
  }
  tags = {
    Name = "My bucket"
  }
}

locals {
  s3_origin_id2 = "myS3Origin"
}

resource "aws_cloudfront_distribution" "s3_distribution2" {
  origin {
    domain_name = "${aws_s3_bucket.c.bucket_regional_domain_name}"
    origin_id   = "${local.s3_origin_id2}"

    s3_origin_config {
      origin_access_identity = "origin-access-identity/cloudfront/ABCDEFG1234567"
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Some comment"
  default_root_object = "index.html"

  logging_config {
    include_cookies = false
    bucket          = "mylogs.s3.amazonaws.com"
    prefix          = "myprefix"
  }

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${local.s3_origin_id2}"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "allow-all"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US", "CA", "GB", "DE"]
    }
  }

  tags = {
    Environment = "production"
    Name = "s3_distribution2"
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

######################################################
# Scenario: Ensure that CloudTrail has logging enabled
# Scenario: Ensure that CloudTrail has log file validation enabled
# Scenario: Ensure that CloudTrail S3 bucket ACL is set to private
# Scenario: Ensure that CloudTrail is multi region enabled
# Scenario: Ensure that CloudTrail logs are encrypted
######################################################
resource "aws_s3_bucket" "foo" {
  bucket        = "tf-test-trail"
  force_destroy = true
  acl           = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "AES256"
      }
    }
  }

  lifecycle_rule {
    id      = "tmp"
    prefix  = "tmp/"
    enabled = true

    expiration {
      date = "2021-01-12"
    }
  }
  tags = {
    Name = "My bucket"
  }
}

resource "aws_cloudtrail" "foobar" {
  name                          = "tf-trail-foobar"
  s3_bucket_name                = aws_s3_bucket.foo.id
  s3_key_prefix                 = "prefix"
  include_global_service_events = false
  enable_logging                = true
  enable_log_file_validation    = true
  is_multi_region_trail         = true
  kms_key_id                    = aws_kms_key.mykey.arn
  tags = {
    Name = "tf-trail-foobar"
  }
}
