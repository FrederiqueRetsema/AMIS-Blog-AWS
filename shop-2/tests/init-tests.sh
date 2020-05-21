# init-tests.sh
# =============

# in_directory_zip
# ----------------

function in_directory_zip {

  directory=$1
  name=$2

  cd $directory
  zip "${name}.zip" "${name}.py"
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

# Main program
# ============

in_directory_zip "lambdas/unittest_test_accept"                                  "unittest_test_accept"
in_directory_zip "lambdas/unittest_test_decrypt"                                 "unittest_test_decrypt"
in_directory_zip "lambdas/unittest_test_update_db"                               "unittest_test_update_db"

in_directory_zip "lambdas/unittest_support_echo"                                 "unittest_support_echo"
in_directory_zip "lambdas/unittest_support_send_logs_from_unittest_support_echo" "unittest_support_send_logs_from_unittest_support_echo"

in_directory_zip "lambdas/perftest_get_stats"                                    "perftest_get_stats"

terraform_init
terraform_plan
terraform_apply

