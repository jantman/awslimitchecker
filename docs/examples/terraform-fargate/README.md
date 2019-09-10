# fargate-awslimitchecker

Example terraform (**0.11.x**) module to run awslimitchecker as a daily ECS Fargate scheduled task, with metrics to Datadog and alerts to PagerDuty.

This terraform module runs the official [awslimitchecker](https://awslimitchecker.readthedocs.io/en/latest/) [Docker image](https://hub.docker.com/r/jantman/awslimitchecker) as an ECS Fargate task, sending metrics to Datadog (tagged with account alias and region name) and alerts to PagerDuty.

## What It Manages (Resources)

* An ECS cluster dedicated to awslimitchecker.
* An ECS Task Definition to run the awslimitchecker Docker image via Fargate.
* By default, IAM Policy Attachments to add all required policies to the required IAM Roles (**Note: if running in multiple regions, disable this on all but one.**)
* A Datadog Monitor to detect if awslimitchecker fails to run at least once in the last 25 hours, and notify you of this.
* A CloudWatch Log Group for the Task, that by default retains logs for only 14 days.
* An S3 Bucket to hold the (optional) Limit and Threshold Override configuration files, as well as managing those files as S3 Objects.
* A CloudWatch Event Rule to run awslimitchecker (the Fargate task) on a regular basis (by default, at 06:00 UTC daily).
* A CloudWatch Event Target for the Rule, to run the task in Fargate.

## Dependencies

* An instance of the ``aws`` provider for each region you wish to run awslimitchecker in
* An instance of the ``datadog`` provider

## Example Usage

An example of using this module to monitor limits in the us-east-1 and us-west-2 regions of an account (note, the example below does not include variable definitions):

```hcl
provider "aws" {
  region  = "us-east-1"
  version = "~> 2.0"
}

provider "aws" {
  region  = "us-west-2"
  version = "~> 2.0"
  alias   = "us-west-2"
}

provider "datadog" {
  api_key = "${var.datadog_api_key}"
  app_key = "${var.datadog_app_key}"
}

resource "aws_iam_role" "awslimitchecker" {
  name               = "awslimitchecker-fargate"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role" "awslimitchecker-events" {
  name               = "awslimitchecker-events"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

module "awslimitchecker-us-east-1" {
  source = "Your-Module-Source"

  pagerduty_critical_service_key = "${var.pagerduty_critical_service_key}"
  datadog_notification_string    = "${var.datadog_notification_string}"
  datadog_api_key                = "${var.datadog_api_key}"
  account_alias                  = "${var.account_alias}"
  task_role_arn                  = "${aws_iam_role.awslimitchecker.arn}"
  task_role_id                   = "${aws_iam_role.awslimitchecker.id}"
  execution_role_arn             = "${aws_iam_role.awslimitchecker.arn}"
  execution_role_id              = "${aws_iam_role.awslimitchecker.id}"
  events_role_arn                = "${aws_iam_role.awslimitchecker-events.arn}"
  events_role_id                 = "${aws_iam_role.awslimitchecker-events.id}"
  tags                           = "${local.tags}"
  tooling_repo                   = "${local.tags["tooling_repo"]}"
  security_groups                = ["${var.security_group_ids}"]
  subnet_ids                     = ["${var.internal_subnet_ids}"]
}

module "awslimitchecker-us-west-2" {
  source = "Your-Module-Source"

  pagerduty_critical_service_key = "${var.pagerduty_critical_service_key}"
  datadog_notification_string    = "${var.datadog_notification_string}"
  datadog_api_key                = "${var.datadog_api_key}"
  account_alias                  = "${var.account_alias}"
  task_role_arn                  = "${aws_iam_role.awslimitchecker.arn}"
  task_role_id                   = "${aws_iam_role.awslimitchecker.id}"
  execution_role_arn             = "${aws_iam_role.awslimitchecker.arn}"
  execution_role_id              = "${aws_iam_role.awslimitchecker.id}"
  events_role_arn                = "${aws_iam_role.awslimitchecker-events.arn}"
  events_role_id                 = "${aws_iam_role.awslimitchecker-events.id}"
  tags                           = "${local.tags}"
  tooling_repo                   = "${local.tags["tooling_repo"]}"
  security_groups                = ["${var.security_group_ids}"]
  subnet_ids                     = ["${var.internal_subnet_ids}"]
  attach_policies                = "0"  # needed on all instances of module after the first
  attach_events_policies         = "0"  # needed on all instances of module after the first
  providers = {
    aws = "aws.us-west-2"
  }
}
```

## Inputs

| Name                              | Description                                                                                                                                                               |  Type  |           Default           | Required |
|:----------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------:|:---------------------------:|::|
| account\_alias                    | AWS account alias/name for use in notifications and Datadog monitor                                                                                                       | string |             n/a             | yes |
| attach\_events\_policies          | Whether or not to attach required policies to the events_role; 0 to disable or 1 to enable                                                                                | string |            `"1"`            | no |
| attach\_policies                  | Whether or not to attach required policies to the task_role and execution_role; 0 to disable or 1 to enable                                                               | string |            `"1"`            | no |
| awslimitchecker\_image\_tag       | jantman/awslimitchecker Docker image tag to run                                                                                                                           | string |         `"latest"`          | no |
| cw\_log\_group\_name              | Name of the CloudWatch Log Group to log to                                                                                                                                | string | `"fargate-awslimitchecker"` | no |
| cw\_log\_group\_retention\_days   | Number of days the CloudWatch Log Group will retain logs                                                                                                                  | string |           `"14"`            | no |
| datadog\_api\_key                 | Datadog API key, for sending metrics                                                                                                                                      | string |             n/a             | yes |
| datadog\_notification\_string     | A string containing one or more Datadog '@' notification tags, to use as destinations for the Datadog Monitor that detects if awslimitchecker stops running successfully. | string |             n/a             | yes |
| events\_role\_arn                 | ARN of an IAM role that can be assumed by events.amazonaws.com, for triggering the Fargate task on a timer                                                                | string |             n/a             | yes |
| events\_role\_id                  | ID of the role specified in events_role_arn                                                                                                                               | string |             n/a             | yes |
| execution\_role\_arn              | ARN of an IAM role that can be assumed by ecs-tasks.amazonaws.com, for ECS to send logs                                                                                   | string |             n/a             | yes |
| execution\_role\_id               | ID of the role specified in execution_role_arn                                                                                                                            | string |             n/a             | yes |
| limit\_overrides                  | Map of limit overrides to pass to awslimitchecker; see awslimitchecker documentation for more information                                                                 |  map   |           `<map>`           | no |
| pagerduty\_critical\_service\_key | PagerDuty Service Key (Events V1 integration) for alerting on critical thresholds crossed                                                                                 | string |             n/a             | yes |
| schedule\_expression              | CloudWatch Events schedule expression for how often to run awslimitchecker task; see: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html     | string |    `"cron(0 6 * * ? *)"`    | no |
| security\_groups                  | List of Security Groups to run Fargate task with; this must at least allow outbound traffic to AWS.                                                                       |  list  |             n/a             | yes |
| subnet\_ids                       | List of Subnet IDs for subnets that can communicate to the Internet, to run Fargate task in.                                                                              |  list  |             n/a             | yes |
| tags                              | Map of tags to apply to all taggable resources                                                                                                                            |  map   |           `<map>`           | no |
| task\_cpu                         | Fargate task definition CPU quantity; this must be one of a documented set of specific values for Fargate tasks                                                           | string |           `"512"`           | no |
| task\_memory                      | Fargate task definition memory quantity; this must be one of a documented set of specific values for Fargate tasks                                                        | string |          `"1024"`           | no |
| task\_role\_arn                   | ARN of an IAM role that can be assumed by ecs-tasks.amazonaws.com, to run the ECS Task under                                                                              | string |             n/a             | yes |
| task\_role\_id                    | ID of the role specified in task_role_arn                                                                                                                                 | string |             n/a             | yes |
| threshold\_overrides              | Map of threshold overrides to pass to awslimitchecker; see awslimitchecker documentation for more information                                                             |  map   |           `<map>`           | no |
| tooling\_repo                     | URL to the repository that manages this terraform                                                                                                                         | string |             n/a             | yes |

## Outputs

| Name                                  | Description                          |
|:--------------------------------------|:-------------------------------------|
| cloudwatch\_log\_group\_name          | Name of the CloudWatch Log Group that the Fargate task will log to |
| config\_s3\_bucket\_name              | Name of the S3 bucket used to store limit and threshold override JSON files |
| datadog\_monitor\_id                  | ID of the Datadog monitor to detect if awslimitchecker isn't running. |
| ecs\_cluster\_arn                     | ARN of the ECS Cluster               |
| ecs\_task\_definition\_arn            | ARN of the ECS Task Definition       |
| ecs\_task\_definition\_family         | Family of the ECS Task Definition    |
| limit\_overrides\_config\_s3\_url     | URL of the limit overrides JSON config file in S3. |
| threshold\_overrides\_config\_s3\_url | URL of the threshold overrides JSON config file in S3. |
