resource "aws_iam_role_policy" "ecs_policy" {
  count  = "${var.attach_policies}"
  name   = "awslimitchecker-fargate-policy"
  role   = "${var.task_role_id}"
  policy = "${data.aws_iam_policy_document.ecs_policy.json}"
}

data "aws_iam_policy_document" "ecs_policy" {
  statement {
    actions   = ["ecs:DescribeClusters"]
    resources = ["${aws_ecs_cluster.awslimitchecker.arn}"]
  }

  statement {
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${aws_s3_bucket.config.id}/*"]
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = "${var.task_role_id}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
