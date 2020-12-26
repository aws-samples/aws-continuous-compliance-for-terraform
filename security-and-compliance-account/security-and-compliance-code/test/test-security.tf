resource "aws_security_group" "elb" {
  name = "terraform-example-elb"
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "elb-security-group"
  }
}
resource "aws_lb" "sr_lb" {
  name = "terraform-asg-example"
  security_groups = ["${aws_security_group.elb.id}"]
  tags = {
    Name = "terraform-asg-example"
    Environment = "test"
  }
}
resource "aws_lb_listener" "listeners_primary" {
  load_balancer_arn = "${aws_lb.sr_lb.arn}"
  port = 443
  protocol = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"

  default_action {
    #target_group_arn = "${aws_lb_target_group.sr-tg-primary.arn}"
    type = "fixed-response"
  }
}
resource "aws_ebs_volume" "example" {
  availability_zone = "us-west-2a"
  size              = 40
  encrypted         = true

  tags = {
    Name = "HelloWorld"
  }
}

resource "aws_acm_certificate" "cert" {
  domain_name       = "example.com"
  validation_method = "DNS"

  tags = {
    Name        = "testcert"
    Environment = "test"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "default" {
  allocated_storage    = 20
  storage_type         = "gp2"
  storage_encrypted    = true
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = "db.t2.micro"
  name                 = "mydb"
  username             = "foo"
  password             = "foobarbaz"
  parameter_group_name = "default.mysql5.7"
  tags = {
    Name        = "testdb"
    Environment = "test"
  }
}

resource "aws_rds_cluster" "default" {
  cluster_identifier      = "aurora-cluster-demo"
  engine                  = "aurora-mysql"
  engine_version          = "5.7.mysql_aurora.2.03.2"
  storage_encrypted       = true
  availability_zones      = ["us-west-2a", "us-west-2b", "us-west-2c"]
  database_name           = "mydb"
  master_username         = "foo"
  master_password         = "bar"
  backup_retention_period = 5
  preferred_backup_window = "07:00-09:00"
  tags = {
    Name        = "testCluster"
    Environment = "test"
  }
}

resource "aws_rds_cluster_instance" "cluster_instances" {
  count              = 2
  identifier         = "aurora-cluster-demo-1"
  cluster_identifier = "${aws_rds_cluster.default.id}"
  instance_class     = "db.r4.large"
  #storage_encrypted  = true --> NA as it's an Aurora cluster. For all non-aurora DBs scenario covered under aws_db_instance check
  ca_cert_identifier = "${aws_acm_certificate.cert.id}"
  tags = {
    Name        = "testCluseterInstance"
    Environment = "test"
  }
}

resource "aws_iam_role" "dlm_lifecycle_role" {
  name = "dlm-lifecycle-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "dlm.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
tags = {
  Name        = "testrole"
  Environment = "test"
}
}
resource "aws_dlm_lifecycle_policy" "example" {
  description        = "example DLM lifecycle policy"
  execution_role_arn = "${aws_iam_role.dlm_lifecycle_role.arn}"
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    schedule {
      name = "2 weeks of daily snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["23:45"]
      }

      retain_rule {
        count = 14
      }

      tags_to_add = {
        SnapshotCreator = "DLM"
      }

      copy_tags = false
    }

    target_tags = {
      Snapshot = "true"
    }
  }
  tags = {
    Name        = "testpolicy"
    Environment = "test"
  }
}

resource "aws_instance" "web" {
  ami = "ami-0323c3dd2da7fb37d"
  instance_type = "t2.micro"
  iam_instance_profile = "${aws_iam_instance_profile.test_profile.name}"
  key_name             = "truist-ec2-key-pair"
  tags = {
    Name = "HelloWorld"
  }
}

resource "aws_iam_instance_profile" "test_profile" {
  name = "test_profile"
  role = "${aws_iam_role.role.name}"
}

resource "aws_iam_role" "role" {
  name = "test_role"
  path = "/"
  tags = {
    Name = "HelloWorld"
  }
  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
               "Service": "ec2.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }
    ]
}
EOF
}

############################################
# Custom Route53 records
###########################################
resource "aws_route53_zone" "customdomain" {
  name = "exampleorr.com"
  tags = {
    Name = "tf-example"
  }
}

resource "aws_route53_record" "wwwcustom" {
  zone_id = "${aws_route53_zone.customdomain.id}"
  name    = "exampleorr.com"
  type    = "A"
  ttl = 60
  records = ["10.1.1.1"]
}

resource "aws_route53_record" "mxcustom" {
  zone_id = "${aws_route53_zone.customdomain.id}"
  name    = ""
  type    = "MX"
  ttl = 60

  records = [
    "1 ASPMX.L.GOOGLE.COM",
    "5 ALT1.ASPMX.L.GOOGLE.COM",
    "5 ALT2.ASPMX.L.GOOGLE.COM",
    "10 ASPMX2.GOOGLEMAIL.COM",
    "10 ASPMX3.GOOGLEMAIL.COM"
  ]
}

resource "aws_route53_record" "spfcustom" {
  zone_id = "${aws_route53_zone.customdomain.id}"
  name    = ""
  type    = "TXT"
  ttl     = "600"
  records = ["v=spf1 include:amazonses.com -all"]
}

# resource "aws_route53_record" "spfold" {
#   zone_id = "${aws_route53_zone.customdomain.id}"
#   name    = ""
#   type    = "SPF"
#   ttl     = "600"
#   records = ["v=spf1 include:amazonses.com -all"]
# }

######################
# Cloudfront WAF Usage
######################
resource "aws_s3_bucket" "b" {
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
  s3_origin_id = "myS3Origin"
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  web_acl_id = "arn:aws:wafv2:us-east-1:111111111111:regional/webacl/test-config-rule-waf-regional/5fa6cafb-ab0c-47ed-a47c-9c38eb045346"
  origin {
    domain_name = "${aws_s3_bucket.b.bucket_regional_domain_name}"
    origin_id   = "${local.s3_origin_id}"
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
  aliases = ["mysite.example.com", "yoursite.example.com"]
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${local.s3_origin_id}"
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
  # Cache behavior with precedence 0
  ordered_cache_behavior {
    path_pattern     = "/content/immutable/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "${local.s3_origin_id}"
    forwarded_values {
      query_string = false
      headers      = ["Origin"]
      cookies {
        forward = "none"
      }
    }
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }
  # Cache behavior with precedence 1
  ordered_cache_behavior {
    path_pattern     = "/content/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${local.s3_origin_id}"
    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }
  price_class = "PriceClass_200"
  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US", "CA", "GB", "DE"]
    }
  }
  tags = {
    Name = "production"
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

###############################################
# Region WAF ALB association
###############################################
resource "aws_wafregional_ipset" "ipset" {
  name = "tfIPSet"
  ip_set_descriptor {
    type  = "IPV4"
    value = "192.0.7.0/24"
  }
}

resource "aws_wafregional_rule" "foo" {
  name        = "tfWAFRule"
  metric_name = "tfWAFRule"
  predicate {
    data_id = "${aws_wafregional_ipset.ipset.id}"
    negated = false
    type    = "IPMatch"
  }
  tags = {
    Name = "tf-example"
  }
}

################################################################################
# Ensure Application load balancer resource is accompanied by an WAF resource
# If WAF Web ACL resource is present then ensure that there is atleast one eligible resources is associated with it
################################################################################
resource "aws_wafregional_web_acl" "foo" {
  name        = "foo"
  metric_name = "foo"
  default_action {
    type = "ALLOW"
  }
  rule {
    action {
      type = "BLOCK"
    }
    priority = 1
    rule_id  = aws_wafregional_rule.foo.id
  }
  tags = {
    Name = "tf-example"
  }
}

resource "aws_vpc" "foo" {
  cidr_block = "10.1.0.0/16"
  tags = {
    Name = "tf-example"
  }
}

data "aws_availability_zones" "available" {}

resource "aws_subnet" "foo" {
  vpc_id            = "${aws_vpc.foo.id}"
  cidr_block        = "10.1.1.0/24"
  availability_zone = "${data.aws_availability_zones.available.names[0]}"
  tags = {
    Name = "tf-example"
  }
}

resource "aws_subnet" "bar" {
  vpc_id            = "${aws_vpc.foo.id}"
  cidr_block        = "10.1.2.0/24"
  availability_zone = "${data.aws_availability_zones.available.names[1]}"
  tags = {
    Name = "tf-example"
  }
}

resource "aws_alb" "foo" {
  internal = true
  subnets  = ["${aws_subnet.foo.id}", "${aws_subnet.bar.id}"]
  tags = {
    Name = "tf-example"
  }
}

resource "aws_wafregional_web_acl_association" "foo" {
  resource_arn = aws_alb.foo.arn
  web_acl_id   = aws_wafregional_web_acl.foo.id
}
################################# END ##########################################

###############################################
# Region WAF API Gateway association
###############################################
# resource "aws_wafregional_ipset" "ipset" {
#   name = "tfIPSet"
#   ip_set_descriptor {
#     type  = "IPV4"
#     value = "192.0.7.0/24"
#   }
# }

# resource "aws_wafregional_rule" "foo" {
#   name        = "tfWAFRule"
#   metric_name = "tfWAFRule"
#   predicate {
#     data_id = "${aws_wafregional_ipset.ipset.id}"
#     negated = false
#     type    = "IPMatch"
#   }
# }

################################################################################
# Ensure API gateway rest api resource is accompanied by an WAF resource
# If WAF Web ACL resource is present then ensure that there is atleast one eligible resources is associated with it
################################################################################
resource "aws_wafregional_web_acl" "apigw_foo" {
  name        = "foo"
  metric_name = "foo"
  default_action {
    type = "ALLOW"
  }
  rule {
    action {
      type = "BLOCK"
    }
    priority = 1
    rule_id  = "${aws_wafregional_rule.foo.id}"
  }
  tags = {
    Name = "tf-example"
  }
}

resource "aws_api_gateway_rest_api" "test" {
  name = "foo"
  tags = {
    Name = "tf-example"
  }
}

resource "aws_api_gateway_resource" "test" {
  parent_id   = "${aws_api_gateway_rest_api.test.root_resource_id}"
  path_part   = "test"
  rest_api_id = "${aws_api_gateway_rest_api.test.id}"
}

resource "aws_api_gateway_method" "test" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = "${aws_api_gateway_resource.test.id}"
  rest_api_id   = "${aws_api_gateway_rest_api.test.id}"
}

resource "aws_api_gateway_method_response" "test" {
  http_method = "${aws_api_gateway_method.test.http_method}"
  resource_id = "${aws_api_gateway_resource.test.id}"
  rest_api_id = "${aws_api_gateway_rest_api.test.id}"
  status_code = "400"
}

resource "aws_api_gateway_integration" "test" {
  http_method             = "${aws_api_gateway_method.test.http_method}"
  integration_http_method = "GET"
  resource_id             = "${aws_api_gateway_resource.test.id}"
  rest_api_id             = "${aws_api_gateway_rest_api.test.id}"
  type                    = "HTTP"
  uri                     = "http://www.example.com"
}

resource "aws_api_gateway_integration_response" "test" {
  rest_api_id = "${aws_api_gateway_rest_api.test.id}"
  resource_id = "${aws_api_gateway_resource.test.id}"
  http_method = "${aws_api_gateway_integration.test.http_method}"
  status_code = "${aws_api_gateway_method_response.test.status_code}"
}

resource "aws_api_gateway_deployment" "test" {
  depends_on = ["aws_api_gateway_integration_response.test"]

  rest_api_id = "${aws_api_gateway_rest_api.test.id}"
}

resource "aws_api_gateway_stage" "test" {
  deployment_id = "${aws_api_gateway_deployment.test.id}"
  rest_api_id   = "${aws_api_gateway_rest_api.test.id}"
  stage_name    = "test"
  tags = {
    Name = "tf-example"
  }
}

resource "aws_wafregional_web_acl_association" "association" {
  resource_arn = "${aws_api_gateway_stage.test.arn}"
  web_acl_id   = "${aws_wafregional_web_acl.apigw_foo.id}"
}
################################# END ##########################################

################################################################################
# EC2 instance must contain a specific predefined ec2 key-pair
################################################################################
resource "aws_instance" "tf_instance_with_keyPair" {
  ami                  = "ami-0323c3dd2da7fb37d"
  instance_type        = "t3.micro"
  key_name             = "truist-ec2-key-pair"
  iam_instance_profile = "${aws_iam_instance_profile.test_profile.name}"
  tags = {
    Name = "HelloWorld"
  }
}
################################# END ##########################################

################################################################################
# EC2 instance must be spun up from an approved AMI
################################################################################
resource "aws_instance" "tf_instance_with_approved_ami" {
  ami                  = "ami-0323c3dd2da7fb37d"
  instance_type        = "t3.micro"
  key_name             = "truist-ec2-key-pair"
  iam_instance_profile = "${aws_iam_instance_profile.test_profile.name}"
  tags = {
    Name = "HelloWorld"
  }
}
################################# END ##########################################

################################################################################
# Network ACL rule should allow/deny outbound communication for specific protocol and ports
# Network ACL rule should allow/deny inbound communication for specific protocol and ports
################################################################################
resource "aws_network_acl" "bar_nacl" {
  vpc_id = aws_vpc.foo.id
  tags = {
    Name = "bar_nacl"
  }
}

resource "aws_network_acl_rule" "out_bar_nacle_rule" {
  network_acl_id = aws_network_acl.bar_nacl.id
  rule_number    = 200
  egress         = true
  protocol       = "tcp"
  rule_action    = "deny"
  cidr_block     = aws_vpc.foo.cidr_block
  from_port      = 22
  to_port        = 22
}

resource "aws_network_acl_rule" "in_bar_nacle_rule" {
  network_acl_id = aws_network_acl.bar_nacl.id
  rule_number    = 100
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = aws_vpc.foo.cidr_block
  from_port      = 80
  to_port        = 8080
}

resource "aws_network_acl" "foo_nacl" {
  vpc_id = aws_vpc.foo.id

  egress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "10.3.0.0/18"
    from_port  = 443
    to_port    = 443
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "deny"
    cidr_block = "10.3.0.0/18"
    from_port  = 22
    to_port    = 22
  }

  tags = {
    Name = "main"
  }
}
################################# END ##########################################