resource "aws_cloudwatch_event_rule" "scheduled_task" {
  name                = "awslimitchecker"
  description         = "Runs awslimitchecker on a regular basis"
  schedule_expression = "${var.schedule_expression}"
}

resource "aws_cloudwatch_event_target" "scheduled_task" {
  rule      = "${aws_cloudwatch_event_rule.scheduled_task.name}"
  target_id = "awslimitchecker"
  arn       = "${aws_ecs_cluster.awslimitchecker.arn}"
  role_arn  = "${var.events_role_arn}"
  input     = "{}"

  ecs_target {
    task_count          = 1
    task_definition_arn = "${aws_ecs_task_definition.awslimitchecker.arn}"
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      assign_public_ip = false
      # With terraform 0.11.x, these lines result in a "should be a list" error,
      # presumably from some HCL issue. See similar issues:
      # https://github.com/terraform-providers/terraform-provider-aws/issues/5315#issuecomment-407744760
      # https://github.com/terraform-providers/terraform-provider-aws/issues/5037#issuecomment-401836797
      security_groups  = ["${var.security_groups}"]
      subnets          = ["${var.subnet_ids}"]
    }
  }
}
