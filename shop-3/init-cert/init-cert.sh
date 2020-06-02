# init-cert.sh
# ------------
# Used to initialise the certificate

# WARNING: Be aware, that using init-cert.sh and destroy-cert.sh a lot, might lead into
# errors in AWS: you are allowed to request 20 certificates per year. 
#
# See also the README.md file in this directory.

# terraform_init
# --------------

function terraform_init {

  ../../../terraform init --var-file=../../../terraform.tfvars
  if (test $? -ne 0)
  then
    echo "Init of cert failed"
    exit 1
  fi

}

# terraform_plan
# --------------

function terraform_plan {

  ../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
  if (test $? -ne 0)
  then
    echo "Plan of cert failed"
    exit 1
  fi

}

# terraform_apply
# ---------------

function terraform_apply {

  ../../../terraform apply "terraform.tfplans"
  if (test $? -ne 0)
  then
    echo "Apply of cert failed"
    exit 1
  fi

}

# Main program
# ============

terraform_init
terraform_plan
terraform_apply

