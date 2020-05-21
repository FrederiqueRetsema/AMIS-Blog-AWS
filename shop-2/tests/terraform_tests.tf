##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"            {}
variable "aws_secret_key"            {}
variable "aws_region"                {}
  
variable "use_public_route53_domain" { default = "Not used in this script. Public domain is not tested to make it possible for everybody to follow the blogs and to make it not too difficult to follow along." }
variable "use_test_objects"          { default = "Not used in this script. We assume that this will always be 1, because otherwise people wouldn't enroll this script at all" }
variable "domainname"                {}
variable "accountnumber"             {}

variable "name_prefix"               {}
variable "key_prefix"                {}

##################################################################################
# PROVIDERS
##################################################################################

provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  region     = var.aws_region
}

##################################################################################
# DATA
##################################################################################

data "aws_iam_role" "lambda_shop_accept_role" {
    name = "${var.name_prefix}_lambda_shop_accept_role"
}

data "aws_iam_role" "lambda_shop_decrypt_role" {
    name = "${var.name_prefix}_lambda_shop_decrypt_role"
}

data "aws_iam_role" "lambda_shop_update_db_role" {
    name = "${var.name_prefix}_lambda_shop_update_db_role"
}

data "aws_iam_role" "lambda_unittest_role" {
    name = "${var.name_prefix}_lambda_unittest_role"
}

data "aws_iam_role" "lambda_perftest_role" {
    name = "${var.name_prefix}_lambda_perftest_role"
}

data "aws_iam_role" "step_function_shop_tests_role" {
    name = "${var.name_prefix}_step_function_shop_tests_role"
}

data "aws_lambda_function" "perftest_test" {
    function_name = "${var.name_prefix}_perftest_test"
}

##################################################################################
# RESOURCES
##################################################################################

# unittest_object_under_test
# --------------------------
# The object_under_test version of this function uses the same code, permission and roles
# as the original function. The only difference is the name of the function and the 
# SNS topic they are delivering to.

# unittest_object_under_test_accept
# ---------------------------------
 
resource "aws_lambda_permission" "lambda_unittest_object_under_test_accept_permission" {
  depends_on    = [aws_lambda_function.unittest_object_under_test_accept]
  statement_id  = "AllowExecutionFromLambdaForUnittestAccept"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_accept.function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "unittest_object_under_test_accept" {
    function_name = "${var.name_prefix}_unittest_object_under_test_accept"
    filename      = "../shop/lambdas/shop_accept/shop_accept.zip"
    role          = data.aws_iam_role.lambda_shop_accept_role.arn
    handler       = "shop_accept.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            to_shop_decrypt_topic_arn = aws_sns_topic.to_unittest_support_echo.arn
        }
    }
    tags = {
        type            = "object_under_test"
        execute_via_gui = "no"
    }
}

# unittest_object_under_test_decrypt
# ----------------------------------

resource "aws_lambda_permission" "lambda_unittest_object_under_test_decrypt_permission" {
  depends_on    = [aws_lambda_function.unittest_object_under_test_decrypt]
  statement_id  = "AllowExecutionFromLambdaForUnittestObjectUnderTestDecrypt"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_decrypt.function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "unittest_object_under_test_decrypt" {
    function_name = "${var.name_prefix}_unittest_object_under_test_decrypt"
    filename      = "../shop/lambdas/shop_decrypt/shop_decrypt.zip"
    role          = data.aws_iam_role.lambda_shop_decrypt_role.arn
    handler       = "shop_decrypt.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            key_prefix                  = var.key_prefix,
            to_shop_update_db_topic_arn = aws_sns_topic.to_unittest_support_echo.arn
        }
    }
    tags = {
        type = "object_under_test"
        execute_via_gui = "no"
    }
}

# unittest_object_under_test_update_db
# ------------------------------------

resource "aws_lambda_permission" "lambda_unittest_object_under_test_update_db_permission" {
  depends_on    = [aws_lambda_function.unittest_object_under_test_update_db]
  statement_id  = "AllowExecutionFromLambdaForUnittestObjectUnderTestUpdateDb"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_update_db.function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "unittest_object_under_test_update_db" {
    function_name = "${var.name_prefix}_unittest_object_under_test_update_db"
    filename      = "../shop/lambdas/shop_update_db/shop_update_db.zip"
    role          = data.aws_iam_role.lambda_shop_update_db_role.arn
    handler       = "shop_update_db.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            name_prefix           = "${var.name_prefix}-unittest",
        }
    }
    tags = {
        type = "object_under_test"
        execute_via_gui = "no"
    }
}

# to_unittest_support_echo
# ------------------------

resource "aws_sns_topic" "to_unittest_support_echo" {
  name = "${var.name_prefix}_to_unittest_support_echo"
}

resource "aws_sns_topic_subscription" "to_unittest_support_echo_subscription" {
  depends_on = [aws_lambda_permission.lambda_unittest_support_echo_permission]
  topic_arn  = aws_sns_topic.to_unittest_support_echo.arn
  protocol   = "lambda"
  endpoint   = aws_lambda_function.unittest_support_echo.arn
}

# unittest_support_echo
# ---------------------

resource "aws_lambda_permission" "lambda_unittest_support_echo_permission" {
  depends_on    = [aws_lambda_function.unittest_support_echo]
  statement_id  = "AllowExecutionUnittestSupportEcho"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_support_echo.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.to_unittest_support_echo.arn
}

resource "aws_lambda_function" "unittest_support_echo" {
    function_name = "${var.name_prefix}_unittest_support_echo"
    filename      = "./lambdas/unittest_support_echo/unittest_support_echo.zip"
    role          = data.aws_iam_role.lambda_unittest_role.arn
    handler       = "unittest_support_echo.lambda_handler"
    runtime       = "python3.8"
    tags = {
        type            = "unittest"
        execute_via_gui = "no"
    }
}

# unittest_test_accept
# --------------------

resource "aws_lambda_permission" "lambda_unittest_test_accept_permission" {
  depends_on    = [aws_lambda_function.unittest_test_accept]
  statement_id  = "AllowExecutionUnittestTestAcccept"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_accept.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.unittest_test_accept.arn
}

resource "aws_lambda_function" "unittest_test_accept" {
    function_name = "${var.name_prefix}_unittest_test_accept"
    filename      = "./lambdas/unittest_test_accept/unittest_test_accept.zip"
    role          = data.aws_iam_role.lambda_unittest_role.arn
    handler       = "unittest_test_accept.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            name_prefix   = var.name_prefix
            sqs_queue_url = aws_sqs_queue.log_messages_from_unittest_support_echo.id
        }
    }
    tags = {
        type            = "unittest"
        execute_via_gui = "yes"
    }
}

# unittest_test_decrypt
# ---------------------

resource "aws_lambda_permission" "lambda_unittest_test_decrypt_permission" {
  depends_on    = [aws_lambda_function.unittest_test_decrypt]
  statement_id  = "AllowExecutionUnittestTestDecrypt"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_decrypt.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.unittest_test_decrypt.arn
}

resource "aws_lambda_function" "unittest_test_decrypt" {
    function_name = "${var.name_prefix}_unittest_test_decrypt"
    filename      = "./lambdas/unittest_test_decrypt/unittest_test_decrypt.zip"
    role          = data.aws_iam_role.lambda_unittest_role.arn
    handler       = "unittest_test_decrypt.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            name_prefix   = var.name_prefix
            key_prefix    = var.key_prefix
            sqs_queue_url = aws_sqs_queue.log_messages_from_unittest_support_echo.id
        }
    }
    tags = {
        type            = "unittest"
        execute_via_gui = "yes"
    }
}

# unittest_test_update_db
# -----------------------

resource "aws_lambda_permission" "lambda_unittest_test_update_db_permission" {
  depends_on    = [aws_lambda_function.unittest_test_update_db]
  statement_id  = "AllowExecutionUnittestTestUpdateDb"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unittest_object_under_test_update_db.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.unittest_test_update_db.arn
}

resource "aws_lambda_function" "unittest_test_update_db" {
    function_name = "${var.name_prefix}_unittest_test_update_db"
    filename      = "./lambdas/unittest_test_update_db/unittest_test_update_db.zip"
    role          = data.aws_iam_role.lambda_unittest_role.arn
    handler       = "unittest_test_update_db.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            name_prefix   = var.name_prefix
        }
    }
    tags = {
        type            = "unittest"
        execute_via_gui = "yes"
    }
}

# unittest_support_send_logs_from_echo
# ------------------------------------
# See also:
# https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html#LambdaFunctionExample

resource "aws_lambda_permission" "lambda_unittest_support_send_logs_from_unittest_support_echo_permission" {
  depends_on     = [aws_lambda_function.unittest_support_send_logs_from_unittest_support_echo]
  statement_id   = "AllowExecutionUnittestSupportSendLogsFromUnittestSupportEcho"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.unittest_support_send_logs_from_unittest_support_echo.function_name
  principal      = "logs.${var.aws_region}.amazonaws.com"
  source_arn     = "arn:aws:logs:${var.aws_region}:${var.accountnumber}:log-group:/aws/lambda/*"
  source_account = var.accountnumber
}

resource "aws_cloudwatch_log_group" "loggroup_lambda_unittest_support_echo" {
  name           = "/aws/lambda/${var.name_prefix}_unittest_support_echo"
}

resource "aws_lambda_function" "unittest_support_send_logs_from_unittest_support_echo" {
    function_name = "${var.name_prefix}_unittest_support_send_logs_from_unittest_support_echo"
    filename      = "./lambdas/unittest_support_send_logs_from_unittest_support_echo/unittest_support_send_logs_from_unittest_support_echo.zip"
    role          = data.aws_iam_role.lambda_unittest_role.arn
    handler       = "unittest_support_send_logs_from_unittest_support_echo.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            sqs_queue_url = aws_sqs_queue.log_messages_from_unittest_support_echo.id
        }
    }
    tags = {
        type            = "unittest"
        execute_via_gui = "no"
    }
}

resource "aws_cloudwatch_log_subscription_filter" "filter_begin_on_support_echo" {
  depends_on      = [aws_lambda_permission.lambda_unittest_support_send_logs_from_unittest_support_echo_permission, aws_cloudwatch_log_group.loggroup_lambda_unittest_support_echo]
  name            = "filter_begin_on_unittest_support_echo"
  log_group_name  = "/aws/lambda/${var.name_prefix}_unittest_support_echo"
  filter_pattern  = "\"DEBUG: BEGIN: event:\""
  destination_arn = aws_lambda_function.unittest_support_send_logs_from_unittest_support_echo.arn
}

# log_messages_from_unittest_support_echo
# ---------------------------------------
# Parameters for the SQS queue:
#
# message_retention_seconds: defaults to 4 days. That is way too long for our example:
#   when the Lambda function that waits for messages doesn't retrieve them for 5 minutes,
#   then just ignore the message
# receive_wait_time_seconds: time for which a ReceiveMessage call will wait for a message
#   to arrive. Defaults to 0 seconds (so: the Lambda function should implement the waiting -
#   if desired), but it is better to let the SQS queue do the waiting and return immediately
#   when there is a new message
#
# For the other parameters, the defaults are fine (see also: 
# https://www.terraform.io/docs/providers/aws/r/sqs_queue.html )
#
# We don't need a fifo queue: it doesn't matter to get the same CloudWatch message more than once,
# we will just check off that a CloudWatch message with certain characteristics has been there. 

resource "aws_sqs_queue" "log_messages_from_unittest_support_echo" {
  name                      = "${var.name_prefix}_log_messages_from_unittest_support_echo"
  message_retention_seconds = 300
  receive_wait_time_seconds = 5
}

# perftest_get_stats
# ------------------
# Reminder: the perftest_test function is in the shop Terraform because Terraform doesn't
# have data objects for the API Gateway objects we need to get the Amazon URL that is used.

resource "aws_lambda_permission" "lambda_perftest_get_stats" {
  depends_on    = [aws_lambda_function.perftest_get_stats]
  statement_id  = "AllowExecutionPerftestCheckResults"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.perftest_get_stats.function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "perftest_get_stats" {
    function_name = "${var.name_prefix}_perftest_get_stats"
    filename      = "./lambdas/perftest_get_stats/perftest_get_stats.zip"
    role          = data.aws_iam_role.lambda_perftest_role.arn
    handler       = "perftest_get_stats.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            name_prefix          = var.name_prefix
            limit_value_duration = 500
            limit_value_diff_mem = 28
        }
    }
    tags = {
        type            = "perftest"
        execute_via_gui = "yes"
    }
}

# shop_tests
# ----------

resource "aws_sfn_state_machine" "shop_tests" {
  name     = "${var.name_prefix}_shop_tests"
  role_arn = data.aws_iam_role.step_function_shop_tests_role.arn

  definition = <<EOF
{
  "Comment": "Combine all tests (except for the smoketest) for the shop example.",
  "StartAt": "Parallel",
  "States" : {
    "Parallel": {
      "Type": "Parallel",
      "Next": "End of tests",
      "Branches": [
        {
          "StartAt": "Unittest accept",
          "States" : {
            "Unittest accept": {  
              "Type"       : "Task",
              "Resource"   : "${aws_lambda_function.unittest_test_accept.arn}",
              "Next"       : "Unittest decrypt"
            },
            "Unittest decrypt": {
                "Type"     : "Task",
                "Resource" : "${aws_lambda_function.unittest_test_decrypt.arn}",
                "End"      : true
              }
            }
        },
        {
          "StartAt": "Unittest update_db",
          "States": {
            "Unittest update_db": {  
              "Type"    : "Task",
              "Resource": "${aws_lambda_function.unittest_test_update_db.arn}",
              "End"     : true
            }
           }
        },
        {
           "StartAt": "Performance test",
           "States": {
             "Performance test": {  
               "Type"      : "Task",
               "Resource"  : "${data.aws_lambda_function.perftest_test.arn}",
               "Next"      : "Wait 4 min"
             },
            "Wait 4 min": {
              "Type"       : "Wait",
              "Comment"    : "Wait untill the CloudWatch logs are available for the Lambda function. Mind, that the logs are earlier available in the user interface than they are available for Lambda function...",
              "Seconds"    : 240,
              "Next"       : "Get statistics"
            },
            "Get statistics": {
                "Type"     : "Task",
                "Resource" : "${aws_lambda_function.perftest_get_stats.arn}",
                "End"      : true
            }
          }
        }
      ]
    },
    "End of tests": {
      "Type" : "Pass",
      "End"  : true
    }
  }
}
EOF
}

##################################################################################
# OUTPUT
##################################################################################

