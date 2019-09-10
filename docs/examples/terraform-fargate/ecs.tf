resource "aws_ecs_cluster" "awslimitchecker" {
  name = "awslimitchecker"
  tags = "${var.tags}"
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS Cluster"
  value       = "${aws_ecs_cluster.awslimitchecker.arn}"
}

resource "aws_ecs_task_definition" "awslimitchecker" {
  family                   = "awslimitchecker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "${var.task_cpu}"
  memory                   = "${var.task_memory}"
  execution_role_arn       = "${var.execution_role_arn}"

  task_role_arn = "${var.task_role_arn}"

  container_definitions = <<EOF
[
  {
    "name": "awslimitchecker",
    "image": "jantman/awslimitchecker:${var.awslimitchecker_image_tag}",
    "essential": true,
    "command": [
      "--alert-provider=PagerDutyV1",
      "--alert-config=critical_service_key=${var.pagerduty_critical_service_key}",
      "--alert-config=account_alias=${var.account_alias}",
      "--metrics-provider=Datadog",
      "--metrics-config=extra_tags=${var.account_alias}",
      "--limit-override-json=s3://${aws_s3_bucket.config.id}/${aws_s3_bucket_object.limit_overrides.id}",
      "--threshold-override-json=s3://${aws_s3_bucket.config.id}/${aws_s3_bucket_object.threshold_overrides.id}"
    ],
    "portMappings": [],
    "environment": [
      {"name": "DATADOG_API_KEY", "value": "${var.datadog_api_key}"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${var.cw_log_group_name}",
        "awslogs-region": "${data.aws_region.current.name}",
        "awslogs-stream-prefix": "fargate"
      }
    }
  }
]
EOF

  tags = "${var.tags}"
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS Task Definition"
  value       = "${aws_ecs_task_definition.awslimitchecker.arn}"
}

output "ecs_task_definition_family" {
  description = "Family of the ECS Task Definition"
  value       = "${aws_ecs_task_definition.awslimitchecker.family}"
}
