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

@log
Feature: Logging Compliance Checks
  Resources should have relevant logs enabled for analysis and debuging purpose.

  Scenario: Ensure that CloudTrail has logging enabled
    Given I have aws_cloudtrail defined
    Then it must contain enable_logging
    And its value must not be false

  Scenario: Ensure that CloudTrail has log file validation enabled
    Given I have aws_cloudtrail defined
    Then it must contain enable_log_file_validation
    And its value must be true

  Scenario: Ensure that CloudTrail S3 bucket ACL is set to private
    Given I have aws_cloudtrail defined
    Then it must contain aws_s3_bucket
    Then it must contain acl
    And its value must be private

  Scenario: Ensure that CloudTrail is multi region enabled
    Given I have aws_cloudtrail defined
    Then it must contain is_multi_region_trail
    And its value must be true

  Scenario: Ensure that CloudTrail logs are encrypted
    Given I have aws_cloudtrail defined
    Then it must contain kms_key_id
    And its value must not be null
