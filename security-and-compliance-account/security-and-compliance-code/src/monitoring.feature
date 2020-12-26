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

@monitor
Feature: Monitoring And Alert Compliance Checks
  Resources should have appropriate metrics and alarms for monitoring.

  Scenario Outline: Ensure 1-minute alarms for all critical metrics
    Given I have aws_cloudwatch_metric_alarm defined
    When its metric_name is <critical-metrics>
    Then it must contain period
    And its value must be equal to <period>

    Examples:
      | critical-metrics  | period |
      | CPUUtilization    | 60     |
      | HealthyHostCount  | 60     |

  Scenario Outline: Ensure metric alarms are monitored at an appropriate individual resource level
    Given I have aws_cloudwatch_metric_alarm defined
    When its namespace is <namespace>
    And its metric_name is <metric>
    Then it must contain dimensions
    And it must contain <dimension>

    Examples:
      | namespace            | metric                     | dimension            |
      | AWS/EC2              | CPUUtilization             | AutoScalingGroupName |
      | AWS/NetworkELB       | HealthyHostCount           | LoadBalancer         |
      | AWS/NetworkELB       | UnHealthyHostCount         | LoadBalancer         |
      | AWS/DynamoDB         | ConsumedWriteCapacityUnits | TableName            |
