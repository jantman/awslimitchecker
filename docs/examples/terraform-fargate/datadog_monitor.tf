resource "datadog_monitor" "not_running" {
  name  = "awslimitchecker not running in ${var.account_alias} ${local.region}"
  type  = "metric alert"
  query = "max(last_1d):sum:awslimitchecker.runtime{${var.account_alias},region:${local.region}} <= 0"

  thresholds = {
    critical = "0"
  }

  notify_no_data      = true
  no_data_timeframe   = "1500" # 25 hours
  require_full_window = false

  message = <<EOF
{{#is_alert}}
awslimitchecker is reporting a runtime sum of zero to datadog in ${var.account_alias} ${local.region}. This likely means it is not running.
Please investigate, or you will not receive alerts when this account is in danger of reaching AWS service limits.
{{/is_alert}}
{{#is_no_data}}
awslimitchecker is not reporting to datadog in ${var.account_alias} ${local.region}. This likely means it is not running.
Please investigate, or you will not receive alerts when this account is in danger of reaching AWS service limits.
{{/is_no_data}}
{{#is_recovery}}
awslimitchecker in ${var.account_alias} ${local.region} has recovered and is reporting to Datadog again.
{{/is_recovery}}
{{#is_no_data_recovery}}
awslimitchecker in ${var.account_alias} ${local.region} has recovered and is reporting to Datadog again.
{{/is_no_data_recovery}}
This monitor is managed by terraform in ${var.tooling_repo}
${var.datadog_notification_string}
EOF
}

output "datadog_monitor_id" {
  description = "ID of the Datadog monitor to detect if awslimitchecker isn't running."
  value       = "${datadog_monitor.not_running.id}"
}
