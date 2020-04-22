# init-shop.sh
# ------------
# See for assumptions and parameters the README.md file in this directory
# 

# Zip the Lambda functions (Terraform doesn't accept inline specification of a Lambda function)
# Please note, that when you change the Python scripts, Terraform will not notice differences.
# the quickest way to deal with this is to use the destroy-shop.sh script and directory after 
# that, this init-shop.sh again:
#
# ./destroy-shop.sh; ./init-shop.sh
#

cd lambdas/accept
zip accept.zip accept.py
cd ../..

cd lambdas/decrypt
zip decrypt.zip decrypt.py
cd ../..

cd lambdas/process
zip process.zip process.py
cd ../..

# Use terraform to deploy the shop. 
# 
../../../terraform init --var-file=../../../terraform.tfvars
if (test $? -ne 0)
then
  echo Init failed
  exit 1
fi

../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
if (test $? -ne 0)
then
  echo Plan failed
  exit 1
fi

../../../terraform apply "terraform.tfplans"
if (test $? -ne 0)
then
  echo Apply failed
  exit 1
fi
