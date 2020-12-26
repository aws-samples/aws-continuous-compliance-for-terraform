
######################################################
# Scenario: Ensure that CloudTrail has logging enabled
# Scenario: Ensure that CloudTrail has log file validation enabled
# Scenario: Ensure that CloudTrail S3 bucket ACL is set to private
# Scenario: Ensure that CloudTrail is multi region enabled
# Scenario: Ensure that CloudTrail logs are encrypted
######################################################

data "aws_caller_identity" "current" {}

resource "aws_kms_key" "mykey" {
  description             = "This key is used to encrypt bucket objects"
  deletion_window_in_days = 10
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Id": "key-default-1",
    "Statement": [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Enable admin of the key",
            "Effect": "Allow",
            "Principal": {
                "AWS": "${data.aws_caller_identity.current.arn}"
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
  	   "Sid": "Allow CloudTrail to encrypt logs",
    	   "Effect": "Allow",
  	   "Principal": {
    	       "Service": "cloudtrail.amazonaws.com"
  	   },
  	   "Action": "kms:GenerateDataKey*",
  	   "Resource": "*",
  	   "Condition": {
    	     "StringLike": {
      		"kms:EncryptionContext:aws:cloudtrail:arn": [
        	  "arn:aws:cloudtrail:*:${data.aws_caller_identity.current.account_id}:trail/*"
                ]
             } 
           }
       },
       {
  	    "Sid": "Allow CloudTrail access",
  	    "Effect": "Allow",
  	    "Principal": {
    		"Service": "cloudtrail.amazonaws.com"
       	    },
  	    "Action": "kms:DescribeKey",
  	    "Resource": "*"
       }
    ]
}
EOF
  tags = {
    Name = "example-s3-bucket-encryption-key"
    Environment = "test"
  }
}

resource "aws_s3_bucket" "foo" {
  bucket        = "tf-test-trail-${data.aws_caller_identity.current.account_id}-${var.region}"
  force_destroy = true
  acl           = "private"
  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AWSCloudTrailAclCheck",
            "Effect": "Allow",
            "Principal": {
              "Service": "cloudtrail.amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::tf-test-trail-${data.aws_caller_identity.current.account_id}-${var.region}"
        },
        {
            "Sid": "AWSCloudTrailWrite",
            "Effect": "Allow",
            "Principal": {
              "Service": "cloudtrail.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::tf-test-trail-${data.aws_caller_identity.current.account_id}-${var.region}/prefix/AWSLogs/${data.aws_caller_identity.current.account_id}/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
POLICY
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = "${aws_kms_key.mykey.arn}"
        sse_algorithm     = "aws:kms"
      }
    }
  }

  lifecycle_rule {
    prefix  = "trails/"
    enabled = true

    noncurrent_version_transition {
      days          = 60
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      days = 90
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
  include_global_service_events = true
  enable_logging                = true
  enable_log_file_validation    = true
  is_multi_region_trail         = true
  kms_key_id                    = aws_kms_key.mykey.arn
  tags = {
    Name = "tf-example"
  }
}
