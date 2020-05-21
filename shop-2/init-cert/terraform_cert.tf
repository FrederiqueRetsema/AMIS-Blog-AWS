##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key"            {}
variable "aws_secret_key"            {}
variable "aws_region"                {}
variable "accountnumber"             { description = "Is not used in this script. Declaration is done to prevent warnings." }

variable "use_public_route53_domain" { description = "Is not used in this script. The fact that you use this script means that you will use a public domain" }
variable "use_test_objects"          { description = "Is not used in this script. Declaration is done to prevent warnings." }
variable "domainname"                {}

variable "name_prefix"               { description = "Is not used in this script. Declaration is done to prevent warnings." }
variable "key_prefix"                { description = "Is not used in this script. Declaration is done to prevent warnings." }

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

data "aws_route53_zone" "my_zone" {
    name         = var.domainname
    private_zone = false
}

##################################################################################
# RESOURCES
##################################################################################

#
# Certificate: needed for use of domain within API gateway
#

resource "aws_acm_certificate" "certificate" {
  domain_name       = "*.${var.domainname}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

#
# Check record in Route53: AWS will use this to look if you are the owner of 
# the domain that the certificate is requested for.
#

resource "aws_route53_record" "certificate_check_record" {
    zone_id  = data.aws_route53_zone.my_zone.zone_id
    name     = aws_acm_certificate.certificate.domain_validation_options[0].resource_record_name
    type     = aws_acm_certificate.certificate.domain_validation_options[0].resource_record_type
    records  = [aws_acm_certificate.certificate.domain_validation_options[0].resource_record_value]
    ttl      = "300"
}

##################################################################################
# OUTPUT
##################################################################################

