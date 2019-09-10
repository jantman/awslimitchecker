resource "aws_s3_bucket" "config" {
  bucket = "${local.bucket_name}"
  acl    = "private"
  tags   = "${var.tags}"
}

output "config_s3_bucket_name" {
  description = "Name of the S3 bucket used to store limit and threshold override JSON files"
  value       = "${aws_s3_bucket.config.id}"
}

resource "aws_s3_bucket_object" "limit_overrides" {
  bucket  = "${aws_s3_bucket.config.id}"
  key     = "limit_overrides_${local.region}.json"
  content = "${jsonencode(var.limit_overrides)}"
}

output "limit_overrides_config_s3_url" {
  description = "URL of the limit overrides JSON config file in S3."
  value       = "s3://${aws_s3_bucket.config.id}/${aws_s3_bucket_object.limit_overrides.id}"
}

resource "aws_s3_bucket_object" "threshold_overrides" {
  bucket  = "${aws_s3_bucket.config.id}"
  key     = "threshold_overrides_${local.region}.json"
  content = "${jsonencode(var.threshold_overrides)}"
}

output "threshold_overrides_config_s3_url" {
  description = "URL of the threshold overrides JSON config file in S3."
  value       = "s3://${aws_s3_bucket.config.id}/${aws_s3_bucket_object.threshold_overrides.id}"
}
