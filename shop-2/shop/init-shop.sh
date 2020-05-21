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

# in_directory_zip_with_requests_library
# --------------------------------------
# I used the following sites to create this:
#
# https://unix.stackexchange.com/questions/153862/remove-all-files-directories-except-for-one-file
# https://linuxacademy.com/cp/courses/lesson/course/1905/lesson/4

function in_directory_zip_with_requests_library {

  directory=$1
  name=$2

  cd $directory
  ls | grep -v "${name}.py" | xargs rm -fr

  mkdir venv
  python3 -m venv ./venv

  source venv/bin/activate
  pip install --upgrade pip
  pip install requests -t .
  pip freeze > requirements.txt
  pip install -r requirements.txt -t .
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

# Main function
# =============

in_directory_zip                       "lambdas/shop_accept"    "shop_accept"
in_directory_zip                       "lambdas/shop_decrypt"   "shop_decrypt"
in_directory_zip                       "lambdas/shop_update_db" "shop_update_db"

in_directory_zip_with_requests_library "lambdas/smoketest_test" "smoketest_test"
in_directory_zip_with_requests_library "lambdas/perftest_test"  "perftest_test"

terraform_init
terraform_plan
terraform_apply

