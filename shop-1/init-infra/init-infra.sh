# init-infra.sh
# -------------
# Initializes the infrastructure. 
#
# Assumptions: 
# - It is possible to use this script multiple times. It will see which objects are there - and 
#   which objects are not.
# - When you re-start this script and the objects are already there, the content of the DynamoDB 
#   table will be re-initialized
# - this script will NOT create a certificate. Go to the ../init-cert directory and use init-cert.sh 
#   for that.
# 

# Determine some information from the terraform.tfvars file. Example for prefix:
#
# prefix: grep prefix ../../../terraform.tfvars
#           -> will get you
#              nameprefix             = "AMIS"
#         awk -F "\"" will set the seperator to double quote. So in the
#         previous example, $2 will be AMIS. 
#

name_prefix=`grep name_prefix ../../../terraform.tfvars | awk -F"\"" '{print $2}'`
echo "name_prefix            = ${name_prefix}"

# Use terraform to deploy the infrastructure

../../../terraform init --var-file=../../../terraform.tfvars
if (test $? -ne 0)
then
  echo "Init of infra failed"
  exit 1
fi

../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
if (test $? -ne 0)
then
  echo "Plan of infra failed"
  exit 1
fi

../../../terraform apply "terraform.tfplans"
if (test $? -ne 0)
then
  echo "Apply of infra failed"
  exit 1
fi

# 
# Add records to the DynamoDB database
#

python3 addDynamoDBRecords.py ${name_prefix} 

