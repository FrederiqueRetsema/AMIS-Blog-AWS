# destroy.sh
# ----------

../../../terraform destroy --var-file=../../../terraform.tfvars -auto-approve
if (test $? -ne 0)
then
    echo Destroy failed
    exit 1
fi
