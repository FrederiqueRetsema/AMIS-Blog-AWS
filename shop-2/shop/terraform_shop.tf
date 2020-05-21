##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"            {}
variable "aws_secret_key"            {}
variable "aws_region"                {}

variable "use_public_route53_domain" { description = "1 = true, 0 = false" }
variable "use_test_objects"          { description = "1 = true, 0 = false" }
variable "domainname"                {}
variable "accountnumber"             {}

variable "name_prefix"               {}
variable "key_prefix"                {}

variable "stage_name"                { default = "prod" }
variable "log_level_api_gateway"     { default = "INFO" }

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

data "aws_iam_role" "api_gateway_logs_role" {
    name = "${var.name_prefix}_api_gateway_logs_role"
}

data "aws_iam_role" "lambda_shop_accept_role" {
    name = "${var.name_prefix}_lambda_shop_accept_role"
}

data "aws_iam_role" "lambda_shop_decrypt_role" {
    name = "${var.name_prefix}_lambda_shop_decrypt_role"
}

data "aws_iam_role" "lambda_shop_update_db_role" {
    name = "${var.name_prefix}_lambda_shop_update_db_role"
}

data "aws_iam_role" "lambda_smoketest_role" {
    name = "${var.name_prefix}_lambda_smoketest_role"
}

data "aws_iam_role" "lambda_perftest_role" {
    count = var.use_test_objects
    name  = "${var.name_prefix}_lambda_perftest_role"
}

data "aws_acm_certificate" "domain_certificate" {
    count  = var.use_public_route53_domain
    domain = "*.${var.domainname}"
}

data "aws_route53_zone" "my_zone" {
    count = var.use_public_route53_domain
    name  = var.domainname
}

##################################################################################
# RESOURCES
##################################################################################

# Certificate
# -----------
# Is needed to be sure that the certificate is valid (enforced by Terraform).

resource "aws_acm_certificate_validation" "mycertificate_validation" {
    count = var.use_public_route53_domain
    certificate_arn = data.aws_acm_certificate.domain_certificate[count.index].arn
}

# Route 53
# --------
# DNS-entry for <name_prefix>.<your domainname> (f.e. amis.retsema.eu), will point to the gateway domain.

resource "aws_route53_record" "myshop_dns_record" {
    count   = var.use_public_route53_domain
    zone_id = data.aws_route53_zone.my_zone[count.index].zone_id
    name    = lower(var.name_prefix)
    type    = "A"

    alias {
        name                   = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].regional_domain_name
        zone_id                = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].regional_zone_id
        evaluate_target_health = true
    }
}

# API Gateway
# -----------
# See for more information the blogs in AMIS-Blog-AWS/shop-1

resource "aws_api_gateway_base_path_mapping" "map_shop_stage_name_to_api_gateway_domain" {
  count       = var.use_public_route53_domain
  depends_on  = [aws_api_gateway_rest_api.api_gateway, aws_api_gateway_deployment.deployment, aws_api_gateway_domain_name.api_gateway_domain_name]
  api_id      = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = aws_api_gateway_stage.stage.stage_name
  domain_name = aws_api_gateway_domain_name.api_gateway_domain_name[count.index].domain_name
}

resource "aws_api_gateway_domain_name" "api_gateway_domain_name" {
  count                    = var.use_public_route53_domain
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
  cloudwatch_role_arn = data.aws_iam_role.api_gateway_logs_role.arn
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
  depends_on              = [aws_api_gateway_rest_api.api_gateway, aws_api_gateway_resource.api_gateway_resource_shop, aws_api_gateway_method.api_gateway_method_post, aws_lambda_function.shop_accept, aws_lambda_permission.lambda_shop_accept_permission]
  rest_api_id             = aws_api_gateway_rest_api.api_gateway.id
  resource_id             = aws_api_gateway_resource.api_gateway_resource_shop.id
  http_method             = aws_api_gateway_method.api_gateway_method_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.shop_accept.invoke_arn
}

# shop_accept
# -----------
 
resource "aws_lambda_permission" "lambda_shop_accept_permission" {
  depends_on    = [aws_lambda_function.shop_accept]
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shop_accept.function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_lambda_function" "shop_accept" {
    depends_on    = [aws_api_gateway_method.api_gateway_method_post]
    function_name = "${var.name_prefix}_shop_accept"
    filename      = "./lambdas/shop_accept/shop_accept.zip"
    role          = data.aws_iam_role.lambda_shop_accept_role.arn
    handler       = "shop_accept.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            to_shop_decrypt_topic_arn = aws_sns_topic.to_shop_decrypt.arn
        }
    }
    tags = {
        type            = "prod"
        execute_via_gui = "no"
    }
}

# to_shop_decrypt
# ---------------

resource "aws_sns_topic" "to_shop_decrypt" {
  name = "${var.name_prefix}_to_shop_decrypt"
}

resource "aws_sns_topic_subscription" "to_shop_decrypt_subscription" {
  depends_on = [aws_lambda_permission.lambda_shop_decrypt_permission]
  topic_arn  = aws_sns_topic.to_shop_decrypt.arn
  protocol   = "lambda"
  endpoint   = aws_lambda_function.shop_decrypt.arn
}

# shop_decrypt
# ------------

resource "aws_lambda_permission" "lambda_shop_decrypt_permission" {
  depends_on    = [aws_lambda_function.shop_decrypt]
  statement_id  = "AllowExecutionFromSNSToShopDecrypt"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shop_decrypt.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.to_shop_decrypt.arn
}

resource "aws_lambda_function" "shop_decrypt" {
    function_name = "${var.name_prefix}_shop_decrypt"
    filename      = "./lambdas/shop_decrypt/shop_decrypt.zip"
    role          = data.aws_iam_role.lambda_shop_decrypt_role.arn
    handler       = "shop_decrypt.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            key_prefix                  = var.key_prefix,
            to_shop_update_db_topic_arn = aws_sns_topic.to_shop_update_db.arn
        }
    }
    tags = {
        type            = "prod"
        execute_via_gui = "no"
    }
}

# to_shop_update_db
# -----------------

resource "aws_sns_topic" "to_shop_update_db" {
  name = "${var.name_prefix}_to_shop_update_db"
}

resource "aws_sns_topic_subscription" "to_shop_update_db_subscription" {
  depends_on = [aws_lambda_permission.lambda_shop_update_db_permission]
  topic_arn  = aws_sns_topic.to_shop_update_db.arn
  protocol   = "lambda"
  endpoint   = aws_lambda_function.shop_update_db.arn
}

# shop_update_db
# --------------

resource "aws_lambda_permission" "lambda_shop_update_db_permission" {
  depends_on    = [aws_lambda_function.shop_update_db]
  statement_id  = "AllowExecutionFromSNSToShopUpdateDb"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shop_update_db.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.to_shop_update_db.arn
}

resource "aws_lambda_function" "shop_update_db" {
    function_name = "${var.name_prefix}_shop_update_db"
    filename      = "./lambdas/shop_update_db/shop_update_db.zip"
    role          = data.aws_iam_role.lambda_shop_update_db_role.arn
    handler       = "shop_update_db.lambda_handler"
    runtime       = "python3.8"
    environment {
        variables = {
            name_prefix = var.name_prefix
        }
    }
    tags = {
        type            = "prod"
        execute_via_gui = "no"
    }
}

# smoketest_test
# --------------

resource "aws_lambda_permission" "lambda_smoketest_test_permission" {
  depends_on    = [aws_lambda_function.smoketest_test]
  statement_id  = "AllowExecutionSmokeTestTest"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.smoketest_test.function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "smoketest_test" {
    function_name = "${var.name_prefix}_smoketest_test"
    filename      = "./lambdas/smoketest_test/smoketest_test.zip"
    role          = data.aws_iam_role.lambda_smoketest_role.arn
    handler       = "smoketest_test.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            key_prefix    = var.key_prefix
            name_prefix   = var.name_prefix
            url           = "${aws_api_gateway_deployment.deployment.invoke_url}${aws_api_gateway_stage.stage.stage_name}/${aws_api_gateway_resource.api_gateway_resource_shop.path_part}"
        }
    }
    tags = {
        type            = "smoketest"
        execute_via_gui = "yes"
    }
}

# perftest-test
# -------------
# Should not be part of this script, but currently Terraform is not able to 
# deliver enough data from the API Gateway to recover the URL. 

resource "aws_lambda_permission" "lambda_perftest_test" {
  count         = var.use_test_objects
  depends_on    = [aws_lambda_function.perftest_test]
  statement_id  = "AllowExecutionPerfTestTest"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.perftest_test[count.index].function_name
  principal     = "lambda.amazonaws.com"
}

resource "aws_lambda_function" "perftest_test" {
    count         = var.use_test_objects
    function_name = "${var.name_prefix}_perftest_test"
    filename      = "./lambdas/perftest_test/perftest_test.zip"
    role          = data.aws_iam_role.lambda_perftest_role[count.index].arn
    handler       = "perftest_test.lambda_handler"
    runtime       = "python3.8"
    timeout       = 120
    environment {
        variables = {
            key_prefix    = var.key_prefix
            name_prefix   = var.name_prefix
            url           = "${aws_api_gateway_deployment.deployment.invoke_url}${aws_api_gateway_stage.stage.stage_name}/${aws_api_gateway_resource.api_gateway_resource_shop.path_part}"
        }
    }
    tags = {
        type            = "perftest"
        execute_via_gui = "yes"
    }
}

##################################################################################
# OUTPUT
##################################################################################

output "invoke_url" {
  value = "${aws_api_gateway_deployment.deployment.invoke_url}${aws_api_gateway_stage.stage.stage_name}/${aws_api_gateway_resource.api_gateway_resource_shop.path_part}"
}

