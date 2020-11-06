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
  name               = "chs_iam_for_lambda_cloudwatch"
  tags               = merge(var.tags, map("Name", var.name))
}

data "aws_iam_policy" "secret_manager" {
  arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

resource "aws_iam_policy" "lambda_logging" {
  description = "IAM policy for logging from a lambda"
  name        = "chs_lambda_logging_cloudwatch"
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

resource "aws_iam_role_policy_attachment" "secrets_lambda_logs" {
  count      = var.enabled ? 1 : 0
  policy_arn = data.aws_iam_policy.secret_manager.arn
  role       = aws_iam_role.iam_for_lambda.name
}

resource "aws_cloudwatch_event_rule" "every_thirty" {
  description         = "Fires off on the first of month - As a security precaution, this check is looking for local users that may have been created"
  name                = "check-for-local-users"
  schedule_expression = "cron(0 17 1 * ? *)"
}

resource "aws_cloudwatch_event_target" "check_every_thirty" {
  count     = var.enabled ? 1 : 0
  arn       = aws_lambda_function.lambda.arn
  rule      = aws_cloudwatch_event_rule.every_thirty.name
  target_id = "lambda"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check" {
  count         = var.enabled ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_thirty.arn
  statement_id  = "AllowExecutionFromCloudWatch"
}

resource "aws_lambda_function" "lambda" {
  filename         = data.archive_file.zip.output_path
  function_name    = "finduser"
  handler          = "finduser.lambda_handler"
  role             = aws_iam_role.iam_for_lambda.arn
  runtime          = "python3.8"
  timeout       = 10
  source_code_hash = data.archive_file.zip.output_base64sha256
  tags             = merge(var.tags, map("Name", var.name))

  environment {
    variables = {
      createdBy = "David Rivera"
    }
  }
}
