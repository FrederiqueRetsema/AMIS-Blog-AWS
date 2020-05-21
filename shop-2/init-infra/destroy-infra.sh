# destroy-infra.sh
# ================

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
