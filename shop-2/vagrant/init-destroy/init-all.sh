#/usr/bin/bash
#
# init-all.sh
# -----------
# 

BLOG_REPO_NAME="AMIS-Blog-AWS"
BLOG_DIR="shop-2"
TEMPFILE_OUTPUT_INIT_SHOP="/tmp/output_init_shop.txt"

# ask_YES_NO_question
# -------------------
# Ask the user a yes/no question and convert the answer to uppercase 
 
function ask_YES_NO_question {

  read answer

  local answer=`echo ${answer} | tr '[:lower:]' '[:upper:]'`
  echo $answer

}

# wait_x_seconds
# --------------

function wait_x_seconds {

  seconds=$1

  echo "Please wait ${seconds} seconds for AWS to deploy the previous objects..."
  while (test $seconds -gt 0)
  do
      echo "${seconds} seconds to wait..."
      sleep 10
      let seconds=seconds-10
  done

}

# convert_to_lowercase
# --------------------

function convert_to_lowercase {

    variable=$1

    result=`echo $variable | tr '[:upper:]' '[:lower:]'`
    echo $result
    
}

# enroll_init_cert
# ----------------

function enroll_init_cert {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/init-cert
  ./init-cert.sh
  if (test $? -ne 0)
  then
    echo Creating certificate failed
    exit 1
  fi

}

# enroll_init_infra
# -----------------

function enroll_init_infra {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/init-infra
  ./init-infra.sh
  if (test $? -ne 0)
  then
    echo Creating infrastructure objects failed
    exit 1
  fi

}

# enroll_init_shop
# ----------------
# Output is teed to be able to get the invoke url for the final remark under this script
# (to get this URL, the function get_invoke_url is used - when we would use the function 
# enroll_init_shop to return the URL then the output from terraform isn't visible for the 
# end user)

function enroll_init_shop {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/shop
  ./init-shop.sh | tee ${TEMPFILE_OUTPUT_INIT_SHOP}
  if (test $? -ne 0)
  then
    echo Creating shop objects failed
    exit 1
  fi

}

# get_invoke_url 
# --------------
# invoke_url is also used in output from apply, on moments that it isn't clear what the 
# invoke_url will be. We need the invoke_url with the https prefix.

function get_invoke_url {

  invoke_url=`cat ${TEMPFILE_OUTPUT_INIT_SHOP} | grep invoke_url | grep https | awk -F "=" '{print $2}' | tr -d [:space:]`
  echo $invoke_url

}

# enroll_tests
# ------------

function enroll_tests {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/tests
  ./init-tests.sh 
  if (test $? -ne 0)
  then
    echo Creating test objects failed
    exit 1
  fi

}

# configure_aws_cli_if_needed
# ---------------------------

function configure_aws_cli_if_needed {

  if (! test -d ~/.aws)
  then

    echo "Access key/secret access key: Copy/paste your access key and secret access key to the next two questions."
    echo "                              If you don't have (secret) access keys yet, read the README.md file in the vagrant directory"
    echo "Default region              : When you don't know what region to use, use eu-central-1 (Frankfurt)"
    echo "Default output format       : Just press enter"
    echo "" 

    aws configure
    if (test $? -ne 0)
    then
      echo "AWS CLI failed (configure)"
      exit 1
    fi

  fi

}

# download_blog_repo_if_needed
# ----------------------------

function download_blog_repo_if_needed {

  if (! test -d ~/${BLOG_REPO_NAME})
  then

    git clone https://github.com/FrederiqueRetsema/${BLOG_REPO_NAME}
    if (test $? -ne 0)
    then
      echo "GIT failed (clone)"
      exit 1
    fi

  fi

}

# configure_tfvars_if_needed
# --------------------------
# don't use 's/your_secret_key/'$aws_secret_key' : the secret key might contain slash-es (/) that will confuse sed

function configure_tfvars_if_needed {

  if (! test -f ~/terraform.tfvars)
  then

    cp ~/${BLOG_REPO_NAME}/${BLOG_DIR}/init-infra/terraform-template.tfvars ~/terraform.tfvars

    # Credentials file is in the format aws_access_key_id = key (including spaces)

    aws_access_key=`grep aws_access_key_id ~/.aws/credentials | awk -F" " '{print $3}'`
    aws_secret_key=`grep aws_secret_access_key ~/.aws/credentials | awk -F" " '{print $3}'`

    sed -i '/aws_access_key/c aws_access_key            = "'${aws_access_key}'"' ~/terraform.tfvars
    sed -i '/aws_secret_key/c aws_secret_key            = "'${aws_secret_key}'"' ~/terraform.tfvars

    # region is in the format region = eu-west-1 (including spaces)
 
    region=`grep region ~/.aws/config | awk -F " " '{print $3}'`
    sed -i '/aws_region/c aws_region                = "'${region}'"' ~/terraform.tfvars

    # aws sts get-caller-identity returns json. json is in the format "key" : "value". 

    accountid=`aws sts get-caller-identity| grep Account | awk -F"\"" '{print $4}'`
    sed -i 's/your_account_number/'$accountid'/' ~/terraform.tfvars

  fi

}

# info_use_public_domain_in_AWS
# -----------------------------

function info_use_public_route53_domain {

  echo "You can choose now to use a public DNS domain in Route53 to see the whole example, or to use the example without"
  echo "public route53 domain. The example without public route53 domain will work with domain names from Amazon AWS, like"
  echo "https://5pcn5scuq5.execute-api.eu-west-1.amazonaws.com/prod/shop"
  echo ""
  echo "When you do have a public domain in Route53, you can also use that domain, the URL will then become something"
  echo "like https://amis.retsema.eu/shop (when you would own retsema.eu, that is)"
  echo "" 
  echo "Do you have a public DNS domain in Route53 AND do you want the example shop application to use this domain?"
  echo "Type yes to use your public route53 domain:"

}

# ask_use_public_route53_domain
# -----------------------------

function ask_use_public_route53_domain {
  
  local use_public_route53_domain=$(ask_YES_NO_question)
  echo $use_public_route53_domain

}

# info_domainname
# ---------------

function info_domainname {

  echo "Which domain do you own?"

}

# ask_domainname 
# --------------

function ask_domainname {

  read domainname
  echo $domainname

}

# configure_domain
# ----------------

function configure_domain {

  domainname=$1

  sed -i '/domainname/c domainname                = "'$domainname'"' ~/terraform.tfvars

  certificate=`aws acm list-certificates | grep "*.${domainname}"`

  if (test "${certificate}" == "")
  then
    echo "This domain doesn't have a star certificate yet, let's create one..."
    enroll_init_cert
  else
    echo "This domain already has a star certificate"
  fi

}

# configure_tfvars_use_public_route53_domain
# ------------------------------------------

function configure_tfvars_use_public_route53_domain {

  value=$1
  sed -i "/use_public_route53_domain/c use_public_route53_domain = ${value}" ~/terraform.tfvars

}

# info_use_test_objects 
# ---------------------

function info_use_test_objects {

  echo ""
  echo "Do you want to have test objects in your deployment?"
  echo "Type yes to create test objects:"

}

# ask_use_test_objects 
# --------------------

function ask_use_test_objects {

  use_test_objects=$(ask_YES_NO_question)
  echo $use_test_objects

}

# configure_tfvars_use_test_objects
# ---------------------------------

function configure_tfvars_use_test_objects {

  value=$1
  sed -i "/use_test_objects/c use_test_objects          = ${value}" ~/terraform.tfvars

}

# get_name_prefix
# ---------------
# name_prefix in the tfvars file is in the format name_prefix = "this-is-the-nameprefix".

function get_name_prefix {

    name_prefix=`grep name_prefix ~/terraform.tfvars | awk -F"\"" '{print $2}'`
    echo $name_prefix

}

# print_results_all
# -----------------

function print_results_AWS_url {

  invoke_url=$1
  name_prefix=$(get_name_prefix)
  shop_id="${name_prefix}1"

  echo "Done!"
  echo ""
  echo "Try for yourself: use the following commands to see if the rollout was successful:"
  echo "cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/client"
  echo "./encrypt_and_send.py ${shop_id} ${invoke_url}"
  echo ""

}

# print_results_use_public_domain_in_AWS 
# --------------------------------------

function print_results_use_public_domain_in_AWS  {

  name_prefix=$(get_name_prefix)
  name_prefix_lower=$(convert_to_lowercase ${name_prefix})
  shop_id=${name_prefix}1

  invoke_url_domain=${name_prefix_lower}.${domainname}/shop

  echo "or"
  echo "" 
  echo "cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/client"
  echo "./encrypt_and_send.py ${shop_id} https://${invoke_url_domain}"
  echo ""

}

# 
# Main program
# ============
#

configure_aws_cli_if_needed
download_blog_repo_if_needed
configure_tfvars_if_needed

info_use_public_route53_domain
use_public_route53_domain=$(ask_use_public_route53_domain)

if (test "${use_public_domain_in_AWS}" == "YES")
then

  info_domain_name
  domainname=$(ask_domain_name)
  configure_domain ${domainname}
  configure_tfvars_use_public_route53_domain 1

else

  domainname=""
  configure_tfvars_use_public_route53_domain 0

fi

info_use_test_objects
use_test_objects=$(ask_use_test_objects)

if (test "${use_test_objects}" == "YES")
then
  configure_tfvars_use_test_objects 1
else
  configure_tfvars_use_test_objects 0
fi

enroll_init_infra
wait_x_seconds 170

enroll_init_shop
invoke_url=$(get_invoke_url)

if (test "${use_test_objects}" == "YES")
then

  wait_x_seconds 170
  enroll_tests

fi

print_results_AWS_url ${invoke_url}

if (test "${use_public_route53_domain}" == "YES")
then
  print_results_use_public_route53_domain
fi

