variable "datadog_api_key" {
  description = "Datadog API key, for sending metrics"
  type        = "string"
}

variable "pagerduty_critical_service_key" {
  description = "PagerDuty Service Key (Events V1 integration) for alerting on critical thresholds crossed"
  type        = "string"
}

variable "datadog_notification_string" {
  description = "A string containing one or more Datadog '@' notification tags, to use as destinations for the Datadog Monitor that detects if awslimitchecker stops running successfully."
  type        = "string"
}

variable "awslimitchecker_image_tag" {
  description = "jantman/awslimitchecker Docker image tag to run"
  default     = "latest"
  type        = "string"
}

variable "account_alias" {
  description = "AWS account alias/name"
  type        = "string"
}

variable "limit_overrides" {
  description = "Map of limit overrides to pass to awslimitchecker; see awslimitchecker documentation for more information"
  default     = {}
  type        = "map"
}

variable "threshold_overrides" {
  description = "Map of threshold overrides to pass to awslimitchecker; see awslimitchecker documentation for more information"
  default     = {}
  type        = "map"
}

variable "task_role_arn" {
  description = "ARN of an IAM role that can be assumed by ecs-tasks.amazonaws.com, to run the ECS Task under"
  type        = "string"
}

variable "task_role_id" {
  description = "ID of the role specified in task_role_arn"
  type        = "string"
}

variable "execution_role_arn" {
  description = "ARN of an IAM role that can be assumed by ecs-tasks.amazonaws.com, for ECS to send logs"
  type        = "string"
}

variable "execution_role_id" {
  description = "ID of the role specified in execution_role_arn"
  type        = "string"
}

variable "attach_policies" {
  description = "Whether or not to attach required policies to the task_role and execution_role; 0 to disable or 1 to enable"
  type        = "string"
  default     = "1"
}

variable "events_role_arn" {
  description = "ARN of an IAM role that can be assumed by events.amazonaws.com, for triggering the Fargate task on a timer"
  type        = "string"
}

variable "events_role_id" {
  description = "ID of the role specified in events_role_arn"
  type        = "string"
}

variable "attach_events_policies" {
  description = "Whether or not to attach required policies to the events_role; 0 to disable or 1 to enable"
  type        = "string"
  default     = "1"
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression for how often to run awslimitchecker task; see: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = "string"
  default     = "cron(0 6 * * ? *)"
}

variable "cw_log_group_name" {
  description = "Name of the CloudWatch Log Group to log to"
  default     = "fargate-awslimitchecker"
  type        = "string"
}

variable "cw_log_group_retention_days" {
  description = "Number of days the CloudWatch Log Group will retain logs"
  type        = "string"
  default     = "14"
}

variable "task_cpu" {
  description = "Fargate task definition CPU quantity; this must be one of a documented set of specific values for Fargate tasks"
  type        = "string"
  default     = "512"
}

variable "task_memory" {
  description = "Fargate task definition memory quantity; this must be one of a documented set of specific values for Fargate tasks"
  type        = "string"
  default     = "1024"
}

variable "tags" {
  description = "Map of tags to apply to all taggable resources"
  type        = "map"
  default     = {}
}

variable "tooling_repo" {
  description = "URL to the repository that manages this terraform"
  type        = "string"
}

variable "security_groups" {
  description = "List of Security Groups to run Fargate task with; this must at least allow outbound traffic to AWS."
  type        = "list"
}

variable "subnet_ids" {
  description = "List of Subnet IDs for subnets that can communicate to the Internet, to run Fargate task in."
  type        = "list"
}
