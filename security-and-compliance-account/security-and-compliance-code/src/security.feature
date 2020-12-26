# Copyright 2019-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

@security
Feature: Service & Data Protection
  This feature file implements Security related compliance check

  Scenario Outline: Validate Security group ingress rule for public open port(s) for all
    Given I have aws_security_group defined
    When it has ingress
    Then it must not have <proto> protocol and port <portNumber> for 0.0.0.0/0

    Examples:
    | proto  | portNumber       |
    | tcp    | 1024-65535       |
    | udp    | 1-65535          |
    | icmp   | 1-65535          |
    | icmpv6 | 1-65535          |
    #| -1    | 1-65535          | --> catch all. Use if port range is same for all protocols.


#####################
# Encryption at rest
#####################
  Scenario: Validate S3 bucket encryption enabled
    Given I have aws_s3_bucket defined
    Then it must contain server_side_encryption_configuration

  Scenario: Validate EBS volume encryption enabled. Alternatively can check for presence of resource - aws_ebs_encryption_by_default
    Given I have aws_ebs_volume defined
    Then it must contain encrypted

#######################################
# Critical data backup schedule defined
#######################################
  Scenario: Validate S3 Lifecycle rule
    Given I have aws_s3_bucket defined
    Then it must contain lifecycle_rule

  @failonskip
  Scenario: Validate presence of EBS snapshot lifecycle policy
    Given I have aws_ebs_volume defined
    Given I have aws_dlm_lifecycle_policy defined
    Then it must contain state

#############################################
# Check for EC2 with Instance Roles attached
#############################################
  Scenario: Ensure that instance profile resource has role defined
    Given I have aws_iam_instance_profile defined
    Then it must contain role
    And its value must not be null

  Scenario: Ensure EC2 have instance profiles
  # Terraform plan puts iam_instance_profile value as null when not specified. So we do a null check here.
    Given I have aws_instance defined
    Then it must contain iam_instance_profile
    And its value must not be null
