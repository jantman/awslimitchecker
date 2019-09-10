# allow events role to run ecs tasks
resource "aws_iam_role_policy" "events_ecs" {
  count  = "${var.attach_events_policies}"
  name   = "awslimitchecker-events-ecs"
  role   = "${var.events_role_id}"
  policy = "${data.aws_iam_policy_document.events_ecs.json}"
}

data "aws_iam_policy_document" "events_ecs" {
  statement {
    effect    = "Allow"
    actions   = ["ecs:RunTask"]
    resources = ["arn:aws:ecs:${local.region}:${local.account_id}:task-definition/awslimitchecker:*"]

    condition {
      test     = "StringLike"
      variable = "ecs:cluster"
      values   = ["${aws_ecs_cluster.awslimitchecker.arn}"]
    }
  }
}

# allow events role to pass role to task execution role and app role
resource "aws_iam_role_policy" "events_ecs_passrole" {
  count  = "${var.attach_events_policies}"
  name   = "awslimitchecker-events-ecs-passrole"
  role   = "${var.events_role_id}"
  policy = "${data.aws_iam_policy_document.passrole.json}"
}

data "aws_iam_policy_document" "passrole" {
  statement {
    effect  = "Allow"
    actions = ["iam:PassRole"]

    resources = [
      "${var.task_role_arn}",
      "${var.execution_role_arn}",
    ]
  }
}
