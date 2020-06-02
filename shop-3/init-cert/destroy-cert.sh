# destroy-cert.sh
# ---------------
# Used to destroy the terraform environment. 

# WARNINGS: 
# ---------
# First destroy the tests, shop and init-infra objects before destroying the 
# certificate.
# 
# Be aware, that using init-cert.sh and destroy-cert.sh a lot, might lead into
# errors in AWS: you are allowed to request 20 certificates per year. 
# 
# See the README.md file in this directory for more information

function terraform_destroy {

  ../../../terraform destroy --var-file=../../../terraform.tfvars -auto-approve
  if (test $? -eq 1)
  then
      echo "Destroy of infra failed"
      exit 1
  fi

}

# Main program
# ============

terraform_destroy
