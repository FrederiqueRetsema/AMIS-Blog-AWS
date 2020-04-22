##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"         {}
variable "aws_secret_key"         {}
variable "aws_region"             {}

variable "use_public_domain"      { description = "Not used in this configurationfile" } 
variable "domainname"             { description = "Not used in this configurationfile" } 

variable "name_prefix"            {}
variable "key_prefix"             {}

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
# 
# Resources are created in the following order:
# - IAM objects
# - KMS objects
# - DynamoDB objects
##################################################################################

# IAM Objects
# -----------
#
# IAM objects are created in the following order:
# - policies
# - roles

# Policies
# --------
# We create our own policies, except for 1: we also use the 
# default AmazonAPIGatewayPushToCloudWatchLogs to log the API Gateway to CloudWatch

# Lambda accept policy
#
# Used by the Lambda accept role (and Lambda accept function)
#
# logs: needed to create entries in cloudwatch for this lambda policy
# sns : needed to send a message to the decrypt function
# kms : needed because AWS will encrypt the environment parameter with a default kms key. 
#       The public key is needed to decrypt it.

resource "aws_iam_policy" "lambda_accept_policy" {
    name        = "${var.name_prefix}_lambda_accept_policy"
    description = "Policy for the Lambda accept function"
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
                  "kms:GetPublicKey"
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

# Lambda decrypt policy
# 
# Used by the Lambda decrypt role (and Lambda decrypt function)
#
# logs: needed to create entries in cloudwatch for this lambda policy
# sns : needed to send a message to the process function
# kms : GetPublicKey needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#       to decrypt it.
#       Decrypt is used to decrypt the encrypted text from the client ("cash machine")

resource "aws_iam_policy" "lambda_decrypt_policy" {
    name        = "${var.name_prefix}_lambda_decrypt_policy"
    description = "Policy for the Lambda decrypt function" 
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
                  "kms:Decrypt"
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

# Lambda process policy
# 
# Used by the Lambda process role (and Lambda process function)
#
# logs    : needed to create entries in cloudwatch for this lambda policy
# dynamodb: needed to create and update items (update does both)
# kms     : needed because AWS will encrypt the parameter with a default kms key. The public key is needed
#           to decrypt it.

resource "aws_iam_policy" "lambda_process_policy" {
    name        = "${var.name_prefix}_lambda_process_policy"
    description = "Policy for the Lambda process function"
    policy      = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
		  "logs:CreateLogGroup",
		  "logs:CreateLogStream",
		  "logs:PutLogEvents",
		  "dynamodb:GetItem",
		  "dynamodb:UpdateItem",
		  "dynamodb:PutItem",
                  "kms:GetPublicKey"
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

# AmazonAPIGatewayPushToCloudWatchLogs
# Needed to log what happens in the API Gateway

resource "aws_iam_role" "api_gateway_role" {
    name                  = "${var.name_prefix}_api_gateway_role"
    description           =  "Needed to log what happens in the API Gateway."
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

resource "aws_iam_policy_attachment" "policy_to_cloudwatch_role" {
   name       = "${var.name_prefix}_policy_to_cloudwatch_role"
   roles      = [aws_iam_role.api_gateway_role.name]
   policy_arn = data.aws_iam_policy.AmazonAPIGatewayPushToCloudWatchLogs.arn
}

# Lambda accept role
# 
# Used by the Lambda accept function. 
#

resource "aws_iam_role" "lambda_accept_role" {
    name                  = "${var.name_prefix}_lambda_accept_role"
    description           =  "Lambda accept function role"
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

resource "aws_iam_policy_attachment" "policy_to_accept_role" {
   name       = "${var.name_prefix}_policy_to_accept_role"
   roles      = [aws_iam_role.lambda_accept_role.name]
   policy_arn = aws_iam_policy.lambda_accept_policy.arn
}

# Lambda decrypt role
# 
# Used by the Lambda decrypt function
#

resource "aws_iam_role" "lambda_decrypt_role" {
    name = "${var.name_prefix}_lambda_decrypt_role"
    description =  "Lambda decrypt function role"
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

resource "aws_iam_policy_attachment" "policy_to_decrypt_role" {
   name       = "${var.name_prefix}_policy_to_decrypt_role"
   roles      = [aws_iam_role.lambda_decrypt_role.name]
   policy_arn = aws_iam_policy.lambda_decrypt_policy.arn
}

# Lambda process role
# 
# Used by the Lambda process function
#

resource "aws_iam_role" "lambda_process_role" {
    name = "${var.name_prefix}_lambda_process_role"
    description =  "Lambda process role"
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

resource "aws_iam_policy_attachment" "policy_to_process_role" {
   name       = "${var.name_prefix}_policy_to_process_role"
   roles      = [aws_iam_role.lambda_process_role.name]
   policy_arn = aws_iam_policy.lambda_process_policy.arn
}

# Keys and key aliases
#
# Though the user interface suggests that an alias (name of the key in the user interface) is just 
# a parameter of a key, in the SDK these are two objects. 
#
# This script will create two keys: one for AMIS1 and one for AMIS2. 

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


# DynamoDB table
#
# We use a provisioned table because we are in a development/test environment. Setting the read and
# write capacity to 1 will limit the number of reads and writes to one per second - which is enough
# in our test environment.
#
# In production environments, we could use on-demand read/write capacity. This is a little bit more
# expensive, but then we do have a one-to-one relationship between the costs and the number of 
# read/writes.
#
# Mind, that trottling can still occur with on-demand capacity: the initial throughput for 
# On-Demand capacity mode is 2,000 write request units, and 6,000 read request units. This can grow
# (via auto scaling) to 40,000 write request units and 40,000 read request units. When you need to
# have more capacity, you can request this via a service ticket to AWS.

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

# aws_dynamodb_table_item (to add records to our table) doesn't work, see my github repository 
# ( https://github.com/terraform-providers/terraform-provider-aws/issues/12545 ). 
#
# Workaround: use a python-script to add the records to the database.

##################################################################################
# OUTPUT
##################################################################################


