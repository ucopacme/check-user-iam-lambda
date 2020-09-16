terraform {
  required_version = ">= 0.12"
}

#provider "aws" {
#  region = var.aws_region
#}

provider "archive" {}

# Insert python script here
data "archive_file" "zip" {
  output_path = "finduser.zip"
  source_file = "finduser.py"
  type        = "zip"
}

data "aws_iam_policy_document" "policy" {
  statement {
    sid    = ""
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  assume_role_policy = data.aws_iam_policy_document.policy.json
  name               = "iam_for_lambda"
  tags               = merge(var.tags, map("Name", var.name))
}

resource "aws_iam_policy" "lambda_logging" {
  description = "IAM policy for logging from a lambda"
  name        = "lambda_logging"
  path        = "/"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "iam:ListAccountAliases",
        "iam:ListUsers",
        "iam:ListUserTags",
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  count      = var.enabled ? 1 : 0
  policy_arn = aws_iam_policy.lambda_logging.arn
  role       = aws_iam_role.iam_for_lambda.name
}

resource "aws_cloudwatch_event_rule" "every_thirty_minutes" {
  description         = "Fires every thirty minutes"
  name                = "every-thirty-minute"
  schedule_expression = "cron(0 15 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "check_every_thirty_minute" {
  count     = var.enabled ? 1 : 0
  arn       = aws_lambda_function.lambda.arn
  rule      = aws_cloudwatch_event_rule.every_thirty_minutes.name
  target_id = "lambda"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check" {
  count         = var.enabled ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_thirty_minutes.arn
  statement_id  = "AllowExecutionFromCloudWatch"
}

resource "aws_lambda_function" "lambda" {
  filename         = data.archive_file.zip.output_path
  function_name    = "finduser"
  handler          = "finduser.lambda_handler"
  role             = aws_iam_role.iam_for_lambda.arn
  runtime          = "python3.7"
  source_code_hash = data.archive_file.zip.output_base64sha256
  tags             = merge(var.tags, map("Name", var.name))

  environment {
    variables = {
      createdBy = "David Rivera"
    }
  }
}
