##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"         {}
variable "aws_secret_key"         {}
variable "aws_region"             {}

variable "use_public_domain"      {}
variable "domainname"             {}

variable "name_prefix"            {}
variable "key_prefix"             {}

variable "stage_name"             { default = "prod" }
variable "log_level_api_gateway"  { default = "INFO" }

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

data "aws_iam_role" "api_gateway_role" {
    name = "${var.name_prefix}_api_gateway_role"
}

data "aws_iam_role" "lambda_accept_role" {
    name = "${var.name_prefix}_lambda_accept_role"
}

data "aws_iam_role" "lambda_decrypt_role" {
    name = "${var.name_prefix}_lambda_decrypt_role"
}

data "aws_iam_role" "lambda_process_role" {
    name = "${var.name_prefix}_lambda_process_role"
}

data "aws_acm_certificate" "domain_certificate" {
    count  = var.use_public_domain
    domain = "*.${var.domainname}"
}

data "aws_route53_zone" "my_zone" {
    count  = var.use_public_domain
    name = var.domainname
}

##################################################################################
# RESOURCES
#
# Order: from client to DynamoDB
# - Connection to certificate
# - Route53
# - API Gateway
# - Lambda function accept
# - SNS topic to_decrypt
# - Lambda function decrypt
# - SNS topic to_process
# - Lambda function process
##################################################################################

#
# Connection to certificate
#
# Is needed to be sure that the certificate is validated
# When count = 0, no certificate validation object will be created
#

resource "aws_acm_certificate_validation" "mycertificate_validation" {
    count = var.use_public_domain
    certificate_arn = data.aws_acm_certificate.domain_certificate[count.index].arn
}

#
# Route 53
# 
# DNS-entry for <name_prefix>.<your domainname>, will point to the gateway domain
# When count = 0, no certificate validation object will be created
#

resource "aws_route53_record" "myshop_dns_record" {
    count   = var.use_public_domain
    zone_id = data.aws_route53_zone.my_zone[count.index].zone_id
    name    = lower(var.name_prefix)
    type    = "A"

    alias {
        name                   = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].regional_domain_name
        zone_id                = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].regional_zone_id
        evaluate_target_health = true
    }
}

#
# API Gateway
#
# These objects are defined in the order in which they are used from Route53, via the moment the POST 
# request is done to the API gateway, to the Lambda function it is calling:
# - aws_api_gateway_base_path_mapping : will define what stage and what method (if any, not used here)
#                                       is used when the DNS record is used. You can have multiple 
#                                       mappings (f.e. for multiple stages, or including the 
#                                       "resource" path - or not) for one domain.
#                                       This mapping is only used when you use a route 53 DNS entry 
#                                       to go to the API gateway)
# - aws_api_gateway_domain_name       : links the name of the domain (and the certificate) to the 
#                                       API gateway that it is using
#                                       (only used when you use a route 53 DNS entry to go to the 
#                                        API gateway)
# - aws_api_gateway_stage             : stage for this solution (default prod, see variables)
# - aws_api_gateway_deployment        : is the version of the API. We only use one stage in our
#                                       example. This is also the object that contains the DNS
#                                       for the API, f.e.
#                                       https://4rgbh0ivlf.execute-api.eu-west-1.amazonaws.com/prod )
# - aws_api_gateway_rest_api          : the API gateway itself. Is also used when you use the 
#                                       DNS-name that the API gateway provides you (f.e.
# - aws_api_gateway_resource          : this is the "/shop" part of the URL. 
# - aws_api_gateway_method            : this is the way the "/shop" part is addressed. In our example,
#                                       this is POST (could also have been GET)
# - aws_api_gateway_integration       : is the connection between the API gateway and the Lambda 
#                                       function that is behind it. 
#
# When count = 0, no certificate validation object will be created, this trick will be used to not
# create objects when no public domain is used
#

resource "aws_api_gateway_base_path_mapping" "map_shop_stage_name_to_api_gateway_domain" {
  count       = var.use_public_domain
  depends_on  = [aws_api_gateway_rest_api.api_gateway, aws_api_gateway_deployment.deployment, aws_api_gateway_domain_name.api_gateway_domain_name]
  api_id      = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = aws_api_gateway_stage.stage.stage_name
  domain_name = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].domain_name
}

resource "aws_api_gateway_domain_name" "api_gateway_domain_name" {
  count                    = var.use_public_domain
  domain_name              = "${lower(var.name_prefix)}.${var.domainname}"
  regional_certificate_arn = aws_acm_certificate_validation.mycertificate_validation[count.index].certificate_arn
  security_policy          = "TLS_1_2"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_stage" "stage" {
  stage_name    = var.stage_name
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  deployment_id = aws_api_gateway_deployment.deployment.id
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on  = [aws_api_gateway_integration.integration,aws_api_gateway_rest_api.api_gateway, aws_api_gateway_resource.api_gateway_resource_shop, aws_api_gateway_method.api_gateway_method_post]
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
}

resource "aws_api_gateway_account" "api_gateway_account" {
  cloudwatch_role_arn = data.aws_iam_role.api_gateway_role.arn
}

resource "aws_api_gateway_rest_api" "api_gateway" {
  name        = "${var.name_prefix}_api_gateway"
  description = "API Gateway for the shop example"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "api_gateway_resource_shop" {
  depends_on  = [aws_api_gateway_rest_api.api_gateway]
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  parent_id   = aws_api_gateway_rest_api.api_gateway.root_resource_id
  path_part   = "shop"
}

resource "aws_api_gateway_method" "api_gateway_method_post" {
  depends_on     = [aws_api_gateway_rest_api.api_gateway, aws_api_gateway_resource.api_gateway_resource_shop]
  rest_api_id    = aws_api_gateway_rest_api.api_gateway.id
  resource_id    = aws_api_gateway_resource.api_gateway_resource_shop.id
  http_method    = "POST"
  authorization  = "NONE"
  request_models = {"application/json"="Empty"}
}

resource "aws_api_gateway_method_settings" "method_settings" {
  rest_api_id    = aws_api_gateway_rest_api.api_gateway.id
  stage_name     = aws_api_gateway_stage.stage.stage_name
  method_path    = "*/*" 

  settings {
    metrics_enabled    = true
    data_trace_enabled = true
    logging_level      = var.log_level_api_gateway
  }
}

resource "aws_api_gateway_integration" "integration" {
  depends_on              = [aws_api_gateway_rest_api.api_gateway, aws_api_gateway_resource.api_gateway_resource_shop, aws_api_gateway_method.api_gateway_method_post, aws_lambda_function.accept, aws_lambda_permission.lambda_accept_permission]
  rest_api_id             = aws_api_gateway_rest_api.api_gateway.id
  resource_id             = aws_api_gateway_resource.api_gateway_resource_shop.id
  http_method             = aws_api_gateway_method.api_gateway_method_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.accept.invoke_arn
}

# Lambda accept
#
# These objects are defined in the order in which they are used from the call 
# from the API gateway to the SNS topic:
# - aws_lambda_permissions: connection between the API gateway (which needs 
#                           permission to call this specific Lambda function)
#                           and the Lambda function accept.
# - aws_lambda_function:    the actual Lambda function. The use of a zip file
#                           is mandatory in Terraform.
#                           We use environment variables to pass the AWS Resource Name (ARN) of the
#                           SNS topic to the Lambda code.
# 
resource "aws_lambda_permission" "lambda_accept_permission" {
  depends_on    = [aws_lambda_function.accept]
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.accept.function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_lambda_function" "accept" {
    depends_on    = [aws_api_gateway_method.api_gateway_method_post]
    function_name = "${var.name_prefix}_accept"
    filename      = "./lambdas/accept/accept.zip"
    role          = data.aws_iam_role.lambda_accept_role.arn
    handler       = "accept.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            to_decrypt_topic_arn = aws_sns_topic.to_decrypt.arn
        }
    }
}

# SNS topic to_decrypt
#
# These objects are defined in the order in which they are used from the call 
# from Lambda function accept to the delivery to the Lambda function 
# decrypt:
# - aws_sns_topic:              topic of the SNS messaging system
# - aws_sns_topic_subscription: subscribers to the topic

resource "aws_sns_topic" "to_decrypt" {
  name = "${var.name_prefix}_to_decrypt"
}

resource "aws_sns_topic_subscription" "to_decrypt_subscription" {
  depends_on = [aws_lambda_permission.lambda_decrypt_permission]
  topic_arn  = aws_sns_topic.to_decrypt.arn
  protocol   = "lambda"
  endpoint   = aws_lambda_function.decrypt.arn
}

# Lambda decrypt
#
# These objects are defined in the order in which they are used from the call 
# from the SNS topic to the lambda function:
# - aws_lambda_permissions: connection between the SNS topic to_decrypt (which needs
#                           permission to call this specific Lambda function)
#                           and the Lambda function decrypt.
# - aws_lambda_function:    the actual Lambda function. The use of a zip file
#                           is mandatory in Terraform.
#                           We use environment variables to pass the AWS Resource Name (ARN) of the
#                           SNS topic and the key prefix to the Lambda code.

resource "aws_lambda_permission" "lambda_decrypt_permission" {
  depends_on    = [aws_lambda_function.decrypt]
  statement_id  = "AllowExecutionFromSNSToDecrypt"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.decrypt.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.to_decrypt.arn
}

resource "aws_lambda_function" "decrypt" {
    function_name = "${var.name_prefix}_decrypt"
    filename      = "./lambdas/decrypt/decrypt.zip"
    role          = data.aws_iam_role.lambda_decrypt_role.arn
    handler       = "decrypt.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            key_prefix           = var.key_prefix,
            to_process_topic_arn = aws_sns_topic.to_process.arn
        }
    }
}

# SNS topic to_process
#
# These objects are defined in the order in which they are used from the call 
# from Lambda function decrypt to the delivery to the Lambda function 
# process:
# - aws_sns_topic:              topic of the SNS messaging system
# - aws_sns_topic_subscription: subscribers to the topic

resource "aws_sns_topic" "to_process" {
  name = "${var.name_prefix}_to_process"
}

resource "aws_sns_topic_subscription" "to_process_subscription" {
  depends_on = [aws_lambda_permission.lambda_process_permission]
  topic_arn  = aws_sns_topic.to_process.arn
  protocol   = "lambda"
  endpoint   = aws_lambda_function.process.arn
}

# Lambda process
#
# These objects are defined in the order in which they are used from the call 
# from the SNS topic to the lambda function:
# - aws_lambda_permissions: connection between the SNS topic to_process (which needs
#                           permission to call this specific Lambda function)
#                           and the Lambda function process.
# - aws_lambda_function:    the actual Lambda function. The use of a zip file
#                           is mandatory in Terraform.
#                           We use environment variables to pass the prefix of the
#                           table name to the Lambda code.

resource "aws_lambda_permission" "lambda_process_permission" {
  depends_on    = [aws_lambda_function.process]
  statement_id  = "AllowExecutionFromSNSToProcess"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.to_process.arn
}

resource "aws_lambda_function" "process" {
    function_name = "${var.name_prefix}_process"
    filename = "./lambdas/process/process.zip"
    role = data.aws_iam_role.lambda_process_role.arn
    handler = "process.lambda_handler"
    runtime = "python3.8"
    environment {
        variables = {
            name_prefix = var.name_prefix
        }
    }
}

##################################################################################
# OUTPUT
#
# The output is needed for people who don't have (or don't want to use) a
# domain in Route53
##################################################################################

output "invoke_url" {
  value = "${aws_api_gateway_deployment.deployment.invoke_url}${aws_api_gateway_stage.stage.stage_name}/${aws_api_gateway_resource.api_gateway_resource_shop.path_part}"
}

