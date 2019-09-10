data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  region      = "${data.aws_region.current.name}"
  account_id  = "${data.aws_caller_identity.current.account_id}"
  bucket_name = "awslimitchecker-${local.account_id}-${local.region}"
}
