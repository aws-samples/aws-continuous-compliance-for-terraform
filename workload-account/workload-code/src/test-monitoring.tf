resource "aws_sns_topic" "netcool_alert_topic" {
  name = "netcool-alerts-topic"
  tags = {
    Name = "netcool-alerts-topic"
  }
}

resource "aws_cloudwatch_metric_alarm" "tf-example-HealthyHostCount-alarm" {
  alarm_name = "tf-example-HealthyHostCount-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/NetworkELB"
  period              = "60"
  statistic           = "Average"
  threshold           = 3
  alarm_description   = "Number of XXXX nodes healthy in Target Group"
  actions_enabled     = "true"
  alarm_actions       = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  ok_actions          = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  dimensions = {
    TargetGroup  = "arn:aws:elasticloadbalancing:${var.region}:111111111111:targetgroup/f78ac2426e59660e"
    LoadBalancer = "arn:aws:elasticloadbalancing:${var.region}:111111111111:loadbalancer/app/bibuiwbe770"
  }
  tags = {
    Name = "tf-example-HealthyHostCount-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "tf-example-CPUUtilization-alarm" {
  alarm_name = "tf-example-CPUUtilization-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU Utilization of EC2 instances"
  actions_enabled     = "true"
  alarm_actions       = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  ok_actions          = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  dimensions = {
    InstanceId  = "i-783658761758"
    AutoScalingGroupName  = "sample-autoscallinggroup"
  }
  tags = {
    Name = "tf-example-CPUUtilization-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "tf-example-CanaryLatency-alarm" {
  alarm_name = "tf-example-CanaryLatency-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "CloudWatchSynthetics"
  period              = "60"
  statistic           = "Average"
  threshold           = 3
  alarm_description   = "Number of XXXX nodes healthy in Target Group"
  actions_enabled     = "true"
  alarm_actions       = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  ok_actions          = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  dimensions = {
    CanaryName  = "test-api-latency-canary"
  }
  tags = {
    Name = "tf-example-CanaryLatency-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "tf-example-DynamoDBIOPS-alarm" {
  alarm_name = "tf-example-DynamoDBIOPS-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period              = "60"
  statistic           = "Average"
  threshold           = 3
  alarm_description   = "Consumed write IOPS exceeded limit"
  actions_enabled     = "true"
  alarm_actions       = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  ok_actions          = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  dimensions = {
    TableName  = "dynamodb-table"
  }
  tags = {
    Name = "tf-example-DynamoDBIOPS-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "tf-example-alb-error-rate-alarm" {
  alarm_name                = "tf-example-alb-error-rate-alarm"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "2"
  threshold                 = "10"
  alarm_description         = "Request error rate has exceeded 10%"
  alarm_actions             = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  ok_actions                = ["${aws_sns_topic.netcool_alert_topic.arn}"]
  insufficient_data_actions = []
  metric_query {
    id = "m1"
    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      period      = "120"
      stat        = "Sum"
      unit        = "Count"
      dimensions = {
        LoadBalancer = "app/web"
      }
    }
  }
  metric_query {
    id = "m2"
    metric {
      metric_name = "HTTPCode_ELB_5XX_Count"
      namespace   = "AWS/ApplicationELB"
      period      = "120"
      stat        = "Sum"
      unit        = "Count"
      dimensions = {
        LoadBalancer = "app/web"
      }
    }
  }
  metric_query {
    id          = "e1"
    expression  = "m2/m1*100"
    label       = "Error Rate"
    return_data = "true"
  }
  tags = {
    Name = "tf-example-alb-error-rate-alarm"
  }
}
