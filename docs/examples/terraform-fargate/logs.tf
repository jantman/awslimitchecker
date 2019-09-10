resource "aws_cloudwatch_log_group" "logs" {
  name              = "${var.cw_log_group_name}"
  retention_in_days = "${var.cw_log_group_retention_days}"
  tags              = "${var.tags}"
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group that the Fargate task will log to"
  value       = "${var.cw_log_group_name}"
}
