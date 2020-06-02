# init-infra.sh
# =============

# terraform_init
# --------------

function terraform_init {

  ../../../terraform init --var-file=../../../terraform.tfvars
  if (test $? -ne 0)
  then
    echo "Init of infra failed"
    exit 1
  fi

}

# terraform_plan
# --------------

function terraform_plan {

  ../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
  if (test $? -ne 0)
  then
    echo "Plan of infra failed"
    exit 1
  fi

}

# terraform_apply
# ---------------

function terraform_apply {

  ../../../terraform apply "terraform.tfplans"
  if (test $? -ne 0)
  then
    echo "Apply of infra failed"
    exit 1
  fi

}

# get_name_prefix
# ---------------
# format in tfvars file is name_prefix             = "AMIS" (including spaces)

function get_name_prefix {

  name_prefix=`grep name_prefix ../../../terraform.tfvars | awk -F"\"" '{print $2}'`
  echo $name_prefix

}

# get_use_test_objects
# --------------------
# format in tfvars file is use_test_objects        = 1 (including spaces)

function get_use_test_objects {

  use_test_objects=`grep use_test_objects ../../../terraform.tfvars | awk -F"=" '{print $2}' | tr -d " "`
  echo $use_test_objects

}

# add_records_to_database
# -----------------------

function add_records_to_database {

  name_prefix=$(get_name_prefix)
  use_test_objects=$(get_use_test_objects)

  python3 addDynamoDBRecords.py ${name_prefix}

  if (test "${use_test_objects}" == "1")
  then
    python3 addDynamoDBRecordsUnittest.py ${name_prefix}
  fi

}

# Main program
# ============

terraform_init
terraform_plan
terraform_apply

add_records_to_database

