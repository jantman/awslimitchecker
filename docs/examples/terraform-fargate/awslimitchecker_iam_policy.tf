resource "aws_iam_role_policy" "awslimitchecker" {
  count  = "${var.attach_events_policies}"
  name   = "awslimitchecker"
  role   = "${var.task_role_id}"
  policy = "${file("${path.module}/iam_policy.json")}"
}
