terraform {
  required_version = ">= 0.12.10"
}

provider "aws" {
  region = var.region
}

provider "archive" {}

resource "aws_dynamodb_table" "opencity_ddb" {
  name = "OpenCity"
  read_capacity = 100
  write_capacity = 700
  hash_key = "grid"
  range_key = "ubid"

  attribute {
    name = "grid"
    type = "S"
  }

  attribute {
    name = "ubid"
    type = "S"
  }
}

data "aws_iam_role" "DynamoDBAutoscaleRole" {
  name = "AWSServiceRoleForApplicationAutoScaling_DynamoDBTable"
}

resource "aws_appautoscaling_target" "opencity_table_write_target" {
  max_capacity       = 3000
  min_capacity       = 5
  resource_id        = "table/${aws_dynamodb_table.opencity_ddb.name}"
  role_arn           = data.aws_iam_role.DynamoDBAutoscaleRole.arn
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "opencity_table_write_policy" {
  name               = "DynamoDBWriteCapacityUtilization:${aws_appautoscaling_target.opencity_table_write_target.resource_id}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.opencity_table_write_target.resource_id
  scalable_dimension = aws_appautoscaling_target.opencity_table_write_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.opencity_table_write_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }

    target_value = 80
  }
}

resource "aws_kinesis_stream" "opencity_stream" {
  name = "OpenCity"
  shard_count = 10
}

resource "aws_iam_role" "opencity_lambda_role" {
  name = "OpenCityLambdaRole"
  path = "/service-role/"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "opencity_batchwrite_policy" {
  name        = "opencity_batchwrite_policy"
  path        = "/"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "dynamodb:BatchWriteItem",
            "Resource": "${aws_dynamodb_table.opencity_ddb.arn}"
        }
    ]
}
EOF
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "opencity_emr_policy" {
  name        = "opencity_emr_policy"
  path        = "/"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCreateClusters",
            "Effect": "Allow",
            "Action": "elasticmapreduce:RunJobFlow",
            "Resource": "*"
        },
        {
            "Sid": "AllowEMRSerivceRole",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/EMR_EC2_DefaultRole",
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/EMR_DefaultRole"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "opencity_lambda_policy1" {
  role       = aws_iam_role.opencity_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"
}

resource "aws_iam_role_policy_attachment" "opencity_lambda_policy2" {
  role       = aws_iam_role.opencity_lambda_role.name
  policy_arn = aws_iam_policy.opencity_batchwrite_policy.arn
}

resource "aws_iam_role_policy_attachment" "opencity_lambda_policy3" {
  role       = aws_iam_role.opencity_lambda_role.name
  policy_arn = aws_iam_policy.opencity_emr_policy.arn
}

data "archive_file" "lambda_ddb_writer_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_ddb_writer.py"
  output_path = "${path.module}/files/lambda_ddb_writer.zip"
}

resource "aws_lambda_function" "lambda_ddb_writer" {
  function_name = "OpenCityDDBWriter"
  handler = "lambda_ddb_writer.lambda_handler"
  filename = data.archive_file.lambda_ddb_writer_zip.output_path
  source_code_hash = data.archive_file.lambda_ddb_writer_zip.output_base64sha256
  role = aws_iam_role.opencity_lambda_role.arn
  runtime = "python3.6"
}

resource "aws_lambda_event_source_mapping" "kinesis_stream_event_source" {
  batch_size = 50
  event_source_arn  = aws_kinesis_stream.opencity_stream.arn
  function_name     = aws_lambda_function.lambda_ddb_writer.arn
  starting_position = "TRIM_HORIZON"
}

data "archive_file" "lambda_emr_scheduler_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_emr_scheduler.py"
  output_path = "${path.module}/files/lambda_emr_scheduler.zip"
}

resource "aws_lambda_function" "lambda_emr_scheduler" {
  function_name = "OpenCityEMRScheduler"
  handler = "lambda_emr_scheduler.lambda_handler"
  filename = data.archive_file.lambda_emr_scheduler_zip.output_path
  source_code_hash = data.archive_file.lambda_emr_scheduler_zip.output_base64sha256
  role = aws_iam_role.opencity_lambda_role.arn
  runtime = "python3.6"
  environment {
    variables = {
      JAR_PATH = var.jar_path
    }
  }
}

resource "aws_lambda_permission" "cloudwatch_trigger" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_emr_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_cron.arn
}

resource "aws_cloudwatch_event_rule" "lambda_cron" {
  name                = "OpenCity_EMR_scheduler"
  description         = "Schedule trigger for lambda execution"
  schedule_expression = "rate(2 hours)"
}

resource "aws_cloudwatch_event_target" "lambda" {
  target_id = aws_lambda_function.lambda_emr_scheduler.id
  rule      = aws_cloudwatch_event_rule.lambda_cron.name
  arn       = aws_lambda_function.lambda_emr_scheduler.arn
}
