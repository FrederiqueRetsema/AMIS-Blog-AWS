#/usr/bin/bash
#
# init-all.sh
# -----------
# 

# Configure AWS CLI
# 
if (! test -d ~/.aws)
then
    echo "Access key/secret access key: Copy/paste your access key and secret access key to the next two questions."
    echo "                              If you don't have (secret) access keys yet, read the README.md file in the vagrant directory"
    echo "Default region              : When you don't know what region to use, use eu-central-1"
    echo "Default output format       : Just press enter"
    echo "" 

    aws configure
    if (test $? -ne 0)
    then
      echo "AWS CLI failed (configure)"
      exit 1
    fi

fi

# Get the CICD repo
#
if (! test -d ~/AMIS-unpublished)
then
    git clone https://github.com/FrederiqueRetsema/AMIS-unpublished
    if (test $? -ne 0)
    then
      echo "GIT failed (clone)"
      exit 1
    fi

    cd AMIS-unpublished
    git config --global user.name "Frederique Retsema"
    git config --global user.email "fretsema@fretsema.nl"
fi

# Configure tfvars
# - if doesn't exist, copy it from the repository and fill in access key and secret access key (from ~/.aws/credentials),
#   the region (from ~/.aws/config) and the account number (from the AWS CLI: aws sts get-caller-identity)
# - don't use 's/your_secret_key/'$aws_secret_key' : the secret key might contain slash-es (/) that will confuse sed

if (! test -f ~/terraform.tfvars)
then
  cp ~/AMIS-unpublished/shop-1/init-infra/terraform-template.tfvars ~/terraform.tfvars

  aws_access_key=`grep aws_access_key_id ~/.aws/credentials | awk -F" " '{print $3}'`
  aws_secret_key=`grep aws_secret_access_key ~/.aws/credentials | awk -F" " '{print $3}'`

  sed -i '/aws_access_key/c aws_access_key         = "'${aws_access_key}'"' ~/terraform.tfvars
  sed -i '/aws_secret_key/c aws_secret_key         = "'${aws_secret_key}'"' ~/terraform.tfvars

  # region is in ~/.aws/config, in the format region = eu-west-1
  region=`grep region ~/.aws/config | awk -F " " '{print $3}'`
  sed -i '/aws_region/c aws_region             = "'${region}'"' ~/terraform.tfvars

fi

# Ask for the domain name that is owned (if any)
#

echo "You can choose now to use a public domain in Route53 to see the whole example, or to use the example without"
echo "public domain. The example without public domain will work with domain names from Amazon AWS, like"
echo "https://5pcn5scuq5.execute-api.eu-west-1.amazonaws.com/prod/shop"
echo ""
echo "When you do have a public domain in Route53, you can also use that domain, the URL will then become something"
echo "like https://amis.retsema.eu/shop (when you would own retsema.eu, that is)"
echo "" 
echo "Do you have a public domain in Route53 AND do you want the example shop application to use this domain?"
echo "Only yes will use the public domain"
read use_public_domain

use_public_domain=`echo ${use_public_domain} | tr '[:lower:]' '[:upper:]'`

if (test "${use_public_domain}" == "YES")
then

  echo "Which domain do you own?"
  read domainname

  # Change the domain name in the tfvars file
  sed -i '/domainname/c domainname             = "'$domainname'"' ~/terraform.tfvars

  # Look if the domain already has a star certificate
  # 
  certificate=`aws acm list-certificates | grep "*.${domainname}"`

  if (test "${certificate}" == "")
  then
    echo "This domain doesn't have a star certificate yet, let's create one..."

    cd ~/AMIS-unpublished/shop-1/init-cert
    ./init-cert.sh
    if (test $? -ne 0)
    then
      echo Creating certificate failed
      exit 1
    fi

  else
    echo "This domain already has a star certificate"
  fi

  # A public domain is used, change tfvars file: set use_public_domain to 1
  # BTW: the $use_public_domain variable in this script is YES or <something else>,
  #      the use_public_domain variable in the tfvars file (and terraform scripts)
  #      is a numeric variable which is 0 (don't create objects) or 1 (create objects)

  sed -i '/use_public_domain/c use_public_domain        = 1' ~/terraform.tfvars

else

  # No public domain is used, change tfvars file: set use_public_domain to 0
  # BTW: the $use_public_domain variable in this script is YES or <something else>,
  #      the use_public_domain variable in the tfvars file (and terraform scripts)
  #      is a numeric variable which is 0 (don't create objects) or 1 (create objects)

  sed -i '/use_public_domain/c use_public_domain        = 0' ~/terraform.tfvars

fi

# Init the rest of the environment
#

cd ~/AMIS-unpublished/shop-1/init-infra
./init-infra.sh
if (test $? -ne 0)
then
  echo Creating infrastructure failed
  exit 1
fi

# Init the shop
#
# sleep 5 is needed, because the new credentials needs time to be distributed to all AWS machines. 
# When we go too fase, we will get verification errors
#
# It is teed to /tmp, to be able to get the URL (for people who don't own a public domain in Route53)

sleep 5
cd ~/AMIS-unpublished/shop-1/shop
./init-shop.sh | tee /tmp/output_init_shop.txt
if (test $? -ne 0)
then
  echo Creating shop objects failed
  exit 1
fi

# To know which URL people should use, we need the name_prefix, both in upper case and in lower case.
# We also need to have the offset number. That contains a space, we will use it as lowest number after removing the space.

# name_prefix:
# - first, get the line with name_prefix from terraform.tfvars
# - the line is: name_prefix = "this-is-the-nameprefix". So: when we use double quote as delimiter, the part between the double quotes is the second parameter
#   and, because the double quote is the delimiter, the last double quote is also stripped from the result
# 
# name_prefix_lower: we need lower case for DNS names. tr '[:upper:]' '[:lower:]' will translate all uppercase characters to lowercase.
#
# offset_number_of_users: this is a numeric value (in the var file). We use the = as seperator instead of quotes.
# because the Python script will treat it as a string, we can strip the leading spaces to use it in the DNS name.
# The DNS-name will be (f.e.) https://amis1.retsema.eu , so <https://><prefix><first number><dot><your domainname>

name_prefix=`grep name_prefix ~/terraform.tfvars | awk -F"\"" '{print $2}'`
name_prefix_lower=`echo $name_prefix | tr '[:upper:]' '[:lower:]'`

# We got the output from terraform apply. When the URL is known, the output is invoke_url = <URL including /shop>. 
# So: grep on invoke_url. When we use = as a delimiter, then this is the second part of this string.
# After getting the right part, trim the spaces.

invoke_url=`cat /tmp/output_init_shop.txt  | grep invoke_url | grep https | awk -F "=" '{print $2}' | tr -d [:space:]`

if (test "${use_public_domain}" == "YES")
then
  invoke_url_domain=${name_prefix_lower}.${domainname}/shop
fi

# 
# Wait for 60 seconds to prevent 500 error
# To make the waiting less annoying, I'll give messages every 10 seconds...
#
echo ""
echo "Please wait 60 seconds for AWS to deploy the permissions in the API gateway/Lambda."
waitingtime=60
while (test $waitingtime -gt 0)
do
    echo "${waitingtime} seconds to wait..."
    sleep 10
    let waitingtime=waitingtime-10
done

# 
# Print the results
#

echo "Done!"
echo ""
echo "Try for yourself: use the following commands to see if the rollout was successful:"
echo "cd ~/AMIS-Blog-AWS/shop-1/client"
echo "./encrypt_and_send.py ${name_prefix}1 ${invoke_url}"

if (test "${use_public_domain}" == "YES")
then
  echo ""
  echo "or"
  echo "" 
  echo "cd ~/AMIS-Blog-AWS/shop-1/client"
  echo "./encrypt_and_send.py ${name_prefix}1 https://${invoke_url_domain}"
fi
echo "" 
