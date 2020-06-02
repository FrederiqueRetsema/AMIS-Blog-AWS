# init-shop.sh
# ============

# in_directory_zip
# ----------------

function in_directory_zip {

  directory=$1
  name=$2

  cd $directory
  zip "${name}.zip" "${name}.py"
  cd ../..
}

# in_directory_zip_with_library
# -----------------------------
# I used the following sites to create this:
#
# https://unix.stackexchange.com/questions/153862/remove-all-files-directories-except-for-one-file
# https://linuxacademy.com/cp/courses/lesson/course/1905/lesson/4

function in_directory_zip_with_library {

  directory=$1
  name=$2
  library=$3

  cd $directory
  ls | grep -v "${name}.py" | xargs rm -fr

  mkdir venv
  python3 -m venv ./venv

  source venv/bin/activate
  pip install --upgrade pip
  pip install ${library} -t .
  deactivate

  rm -r venv

  zip -r "${name}.zip" *
  cd ../..

}

# terraform_init
# --------------

function terraform_init {

  ../../../terraform init --var-file=../../../terraform.tfvars
  if (test $? -ne 0)
  then
    echo Init failed
    exit 1
  fi

}

# terraform_plan
# --------------

function terraform_plan {

  ../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
  if (test $? -ne 0)
  then
    echo Plan failed
    exit 1
  fi

}

# terraform_apply 
# ---------------

function terraform_apply {

  ../../../terraform apply "terraform.tfplans"
  if (test $? -ne 0)
  then
    echo Apply failed
    exit 1
  fi

}

# get_name_prefix
# ---------------
# format: name_prefix = "abcde"

function get_name_prefix {

  name_prefix=`grep name_prefix ../../../terraform.tfvars | awk -F"\"" '{print $2}'` 
  echo ${name_prefix}

}

# activate_xray
# -------------
# activation of xray in Lambda functions cannot be done in terraform yet. Activation of X-Ray in the API Gateway is 
# done in the terraform configuration file.

function activate_xray {

  name_prefix=$(get_name_prefix)
  echo "name_prefix = ->${name_prefix}<-"
  aws lambda update-function-configuration --function-name ${name_prefix}_shop_accept    --tracing-config Mode=Active
  aws lambda update-function-configuration --function-name ${name_prefix}_shop_decrypt   --tracing-config Mode=Active
  aws lambda update-function-configuration --function-name ${name_prefix}_shop_update_db --tracing-config Mode=Active

}


# Main function
# =============

in_directory_zip_with_library "lambdas/shop_accept"    "shop_accept"    "aws-xray-sdk"
in_directory_zip_with_library "lambdas/shop_decrypt"   "shop_decrypt"   "aws-xray-sdk"
in_directory_zip_with_library "lambdas/shop_update_db" "shop_update_db" "aws-xray-sdk"

in_directory_zip_with_library "lambdas/smoketest_test" "smoketest_test" "requests"
in_directory_zip_with_library "lambdas/perftest_test"  "perftest_test"  "requests"

terraform_init
terraform_plan
terraform_apply
activate_xray

