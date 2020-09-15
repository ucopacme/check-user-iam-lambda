terraform {
  required_version = ">= 0.12"
}

provider "aws" {
  region = var.aws_region
}

provider "archive" {}

# Insert python script here
data "archive_file" "zip" {
  type        = "zip"
  source_file = "finduser.py"
  output_path = "finduser.zip"
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

# Note: since this TF script creates a new role, it must be unique.
# suggestion is: call it 'application_region'_for_lambda
# I only used 'chs_region'_for_lambda for testing

resource "aws_iam_role" "chs_oregon_iam_for_lambda" {
  name               = "chs_oregon_iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.policy.json
}

resource "aws_iam_policy" "chs_oregon_lambda_logging" {
  name        = "chs_oregon_lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
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
  role       = aws_iam_role.chs_oregon_iam_for_lambda.name
  policy_arn = aws_iam_policy.chs_oregon_lambda_logging.arn
}

resource "aws_cloudwatch_event_rule" "every_thirty_minutes" {
  name                = "every-thirty-minute"
  description         = "Fires every thirty minutes"
 # schedule_expression = "cron(0/30 * * * ? *)"
  schedule_expression = "cron(0 15 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "check_every_thirty_minute" {
  rule      = aws_cloudwatch_event_rule.every_thirty_minutes.name
  target_id = "lambda"
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_thirty_minutes.arn
}

resource "aws_lambda_function" "lambda" {
  function_name = "finduser"

  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256

  role    = aws_iam_role.chs_oregon_iam_for_lambda.arn
  handler = "finduser.lambda_handler"
  runtime = "python3.7"

  environment {
    variables = {
      createdBy = "David Rivera"
    }
  }
}
