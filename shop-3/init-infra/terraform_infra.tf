##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"            {}
variable "aws_secret_key"            {}
variable "aws_region"                {}
variable "accountnumber"             {}

variable "use_public_route53_domain" { description = "Not used in this configurationfile, defined to prevent warnings." } 
variable "use_test_objects"          { description = "1 = true, 0 = false" }
variable "domainname"                { description = "Not used in this configurationfile, defined to prevent warnings." } 

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

data "aws_iam_policy" "AmazonAPIGatewayPushToCloudWatchLogs" {
    arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

##################################################################################
# RESOURCES
##################################################################################

# Policies
# --------

# lambda_shop_accept_policy
# -------------------------
# logs: needed to create entries in cloudwatch for the lambda function
# sns : needed to send a message to the SNS to_shop_decrypt topic
# kms : needed because AWS will encrypt the environment variabled with a default kms key. 
#       The public key is needed to decrypt it.
# xray: for sending trace information to xray (see blog about xray)

resource "aws_iam_policy" "lambda_shop_accept_policy" {
    name        = "${var.name_prefix}_lambda_shop_accept_policy"
    description = "Policy for the Lambda shop_accept function"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:CreateLogGroup",
		  "logs:CreateLogStream",
		  "logs:PutLogEvents",
		  "sns:Publish",
                  "kms:GetPublicKey",
                  "xray:PutTraceSegments",
                  "xray:PutTelemetryRecords"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
	}
      ]
}
EOF
}

# lambda_shop_decrypt_policy
# --------------------------
# logs: needed to create entries in cloudwatch for the lambda function
# sns : needed to send a message to the SNS to_shop_update_db topic
# kms : GetPublicKey needed because AWS will encrypt the environment variable with a default kms key. 
#       The public key is needed to decrypt it.
#       Decrypt is used to decrypt the encrypted text from the client ("cash machine")
# xray: for sending trace information to xray (see blog about xray)

resource "aws_iam_policy" "lambda_shop_decrypt_policy" {
    name        = "${var.name_prefix}_lambda_shop_decrypt_policy"
    description = "Policy for the Lambda shop_decrypt function" 
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:CreateLogGroup",
		  "logs:CreateLogStream",
		  "logs:PutLogEvents",
		  "sns:Publish",
                  "kms:GetPublicKey",
                  "kms:Decrypt",
                  "xray:PutTraceSegments",
                  "xray:PutTelemetryRecords"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
	}
      ]
}
EOF
}

# lambda_shop_update_db_policy
# ----------------------------
# logs    : needed to create entries in cloudwatch for the lambda function
# dynamodb: needed to create and update items
# kms     : needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#           to decrypt it.
# xray    : for sending trace information to xray (see blog about xray)

resource "aws_iam_policy" "lambda_shop_update_db_policy" {
    name        = "${var.name_prefix}_lambda_shop_update_db_policy"
    description = "Policy for the Lambda shop_update_db function"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:CreateLogGroup",
		  "logs:CreateLogStream",
		  "logs:PutLogEvents",
		  "dynamodb:PutItem",
		  "dynamodb:UpdateItem",
                  "kms:GetPublicKey",
                  "xray:PutTraceSegments",
                  "xray:PutTelemetryRecords"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
      }
     ]
}
EOF
}

# lambda_unittest_policy
# ----------------------
# lambda  : used to invoke other functions ("object_under_test" objects) and also to get and set the 
#           environment variables of these functions (to create errors)
# logs    : needed to create entries in cloudwatch for the lambda function, but also to get log information
#           from CloudWatch from other functions.
# sqs     : to put messages on a queue and to get messages from a queue
# dynamodb: to update items and to get information
# kms     : needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#           to decrypt it. Also needed to encrypt the information before sending it to an object_under_test.

resource "aws_iam_policy" "lambda_unittest_policy" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_lambda_unittest_policy"
    description = "Policy for the Lambda unittest functions"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
                  "lambda:InvokeFunction",
                  "lambda:GetFunctionConfiguration",
                  "lambda:UpdateFunctionConfiguration",
		  "logs:*",
                  "sqs:SendMessage",
                  "sqs:ReceiveMessage",
                  "sqs:DeleteMessage",
                  "dynamodb:GetItem",
                  "dynamodb:UpdateItem",
		  "dynamodb:DeleteItem",
                  "kms:GetPublicKey",
                  "kms:Encrypt"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
      }
     ]
}
EOF
}

# lambda_smoketest_policy
# -----------------------
# logs    : needed to create entries in cloudwatch for the lambda function
# kms     : needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#           to decrypt it. Encrypt is used to encrypt the data that is sent to the API Gateway.

resource "aws_iam_policy" "lambda_smoketest_policy" {
    name        = "${var.name_prefix}_lambda_smoketest_policy"
    description = "Policy for the Lambda smoketest_test function"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:CreateLogGroup",
		  "logs:CreateLogStream",
		  "logs:PutLogEvents",
                  "kms:GetPublicKey",
                  "kms:Encrypt"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
      }
     ]
}
EOF
}

# lambda_perftest_policy
# ----------------------
# logs    : needed to create entries in cloudwatch for the lambda function. Also needed to read logs in the
#           stats function.
# kms     : needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#           to decrypt it.

resource "aws_iam_policy" "lambda_perftest_policy" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_lambda_perftest_policy"
    description = "Policy for the Lambda perftest functions"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:*",
                  "kms:GetPublicKey",
                  "kms:Encrypt"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
      }
     ]
}
EOF
}

# step_function_shop_tests_policy
# -------------------------------
# lambda  : invokes the test functions

resource "aws_iam_policy" "step_function_shop_tests_policy" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_step_function_shop_tests_policy"
    description = "Policy for the step functions shop tests function"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
                  "lambda:InvokeFunction"
                  ],
		"Effect": "Allow",
		"Resource": "*",
                "Condition": {
                   "StringEquals": {
                       "aws:RequestedRegion": "${var.aws_region}"
                   }
                }
      }
     ]
}
EOF
}

# Roles
# -----

# api_gateway_logs_role
# ---------------------
# Uses the default AmazonAPIGatewayPushToCloudWatchLogs that is provided by Amazon 
# for logging of API Gateway calls

resource "aws_iam_role" "api_gateway_logs_role" {
    name                  = "${var.name_prefix}_api_gateway_logs_role"
    description           =  "Log what happens in the API Gateway."
    force_detach_policies = true
    assume_role_policy    =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "apigateway.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_api_gateway_role" {
   name       = "${var.name_prefix}_policy_to_api_gateway_role"
   roles      = [aws_iam_role.api_gateway_logs_role.name]
   policy_arn = data.aws_iam_policy.AmazonAPIGatewayPushToCloudWatchLogs.arn
}

# lambda_shop_accept_role
# -----------------------

resource "aws_iam_role" "lambda_shop_accept_role" {
    name                  = "${var.name_prefix}_lambda_shop_accept_role"
    description           =  "Lambda shop_accept function role"
    force_detach_policies = true
    assume_role_policy    =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_shop_accept_role" {
   name       = "${var.name_prefix}_policy_to_shop_accept_role"
   roles      = [aws_iam_role.lambda_shop_accept_role.name]
   policy_arn = aws_iam_policy.lambda_shop_accept_policy.arn
}

# lambda_shop_decrypt_role
# ------------------------

resource "aws_iam_role" "lambda_shop_decrypt_role" {
    name = "${var.name_prefix}_lambda_shop_decrypt_role"
    description =  "Lambda shop_decrypt function role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_shop_decrypt_role" {
   name       = "${var.name_prefix}_policy_to_shop_decrypt_role"
   roles      = [aws_iam_role.lambda_shop_decrypt_role.name]
   policy_arn = aws_iam_policy.lambda_shop_decrypt_policy.arn
}

# lambda_shop_update_db_role
# --------------------------

resource "aws_iam_role" "lambda_shop_update_db_role" {
    name = "${var.name_prefix}_lambda_shop_update_db_role"
    description =  "Lambda shop_update_db role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_shop_update_db_role" {
   name       = "${var.name_prefix}_policy_to_shop_update_db_role"
   roles      = [aws_iam_role.lambda_shop_update_db_role.name]
   policy_arn = aws_iam_policy.lambda_shop_update_db_policy.arn
}

# lambda_unittest_role
# --------------------

resource "aws_iam_role" "lambda_unittest_role" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_lambda_unittest_role"
    description =  "Lambda unittest role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_unittest_role" {
   count      = var.use_test_objects
   name       = "${var.name_prefix}_policy_to_unittest_role"
   roles      = [aws_iam_role.lambda_unittest_role[count.index].name]
   policy_arn = aws_iam_policy.lambda_unittest_policy[count.index].arn
}

# lambda_smoketest_role
# ---------------------

resource "aws_iam_role" "lambda_smoketest_role" {
    name = "${var.name_prefix}_lambda_smoketest_role"
    description =  "Lambda smoketest role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_smoketest_role" {
   name       = "${var.name_prefix}_policy_to_smoketest_role"
   roles      = [aws_iam_role.lambda_smoketest_role.name]
   policy_arn = aws_iam_policy.lambda_smoketest_policy.arn
}

# lambda_perftest_role
# --------------------

resource "aws_iam_role" "lambda_perftest_role" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_lambda_perftest_role"
    description =  "Lambda perftest role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_perftest_role" {
   count      = var.use_test_objects
   name       = "${var.name_prefix}_policy_to_perftest_role"
   roles      = [aws_iam_role.lambda_perftest_role[count.index].name]
   policy_arn = aws_iam_policy.lambda_perftest_policy[count.index].arn
}

# step_function_shop_tests_role
# -----------------------------

resource "aws_iam_role" "step_function_shop_tests_role" {
    count       = var.use_test_objects
    name        = "${var.name_prefix}_step_function_shop_tests_role"
    description =  "Step function shop tests role"
    force_detach_policies = true
    assume_role_policy =  <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "states.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
} 

resource "aws_iam_policy_attachment" "policy_to_step_function_shop_tests_role" {
   count      = var.use_test_objects
   name       = "${var.name_prefix}_policy_to_step_function_shop_tests_role"
   roles      = [aws_iam_role.step_function_shop_tests_role[count.index].name]
   policy_arn = aws_iam_policy.step_function_shop_tests_policy[count.index].arn
}

# Keys
# ----
# Both KeyQ-AMIS1 and KeyQ-AMIS2 will be created

resource "aws_kms_key" "key" {
    count                    = 2
    description              = "${var.name_prefix}${count.index + 1}"
    key_usage                = "ENCRYPT_DECRYPT"
    customer_master_key_spec = "RSA_2048"
}

resource "aws_kms_alias" "key_alias" {
  count          = 2
  name           = "alias/${var.key_prefix}${var.name_prefix}${count.index + 1}"
  target_key_id  = aws_kms_key.key[count.index].key_id 
}


# DynamoDB tables
# ---------------

resource "aws_dynamodb_table" "shops-table" {
    name           = "${var.name_prefix}-shops"
    billing_mode   = "PROVISIONED"
    read_capacity  = 1
    write_capacity = 1
    hash_key       = "shop_id"
    range_key      = "record_type"

    attribute {
        name = "shop_id"
        type = "S"
    }

    attribute {
        name = "record_type"
        type = "S"
    }
}

resource "aws_dynamodb_table" "shops-message-ids" {
    name           = "${var.name_prefix}-shops-message-ids"
    billing_mode   = "PROVISIONED"
    read_capacity  = 1
    write_capacity = 1
    hash_key       = "shop_id"
    range_key      = "message_id"

    attribute {
        name = "shop_id"
        type = "S"
    }

    attribute {
        name = "message_id"
        type = "S"
    }

    ttl {
        attribute_name = "time_to_live"
        enabled        = true
    }
}

resource "aws_dynamodb_table" "unittest-shops" {
    count          = var.use_test_objects
    name           = "${var.name_prefix}-unittest-shops"
    billing_mode   = "PROVISIONED"
    read_capacity  = 1
    write_capacity = 1
    hash_key       = "shop_id"
    range_key      = "record_type"

    attribute {
        name = "shop_id"
        type = "S"
    }

    attribute {
        name = "record_type"
        type = "S"
    }
}

resource "aws_dynamodb_table" "unittest-shops-message-ids" {
    name           = "${var.name_prefix}-unittest-shops-message-ids"
    billing_mode   = "PROVISIONED"
    read_capacity  = 1
    write_capacity = 1
    hash_key       = "shop_id"
    range_key      = "message_id"

    attribute {
        name = "shop_id"
        type = "S"
    }

    attribute {
        name = "message_id"
        type = "S"
    }

    ttl {
        attribute_name = "time_to_live"
        enabled        = true
    }
}

# aws_dynamodb_table_item (to add records to our table) doesn't work, see for links the
# addDynamoDBRecords.py script for more information.

##################################################################################
# OUTPUT
##################################################################################


