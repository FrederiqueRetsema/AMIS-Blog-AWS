# destroy-cert.sh
# ---------------
# Used to destroy the terraform environment. 

# WARNING: 
# --------
# Be aware, that using init-cert.sh and destroy-cert.sh a lot, might lead into
# errors in AWS: you are allowed to request 20 certificates per year. 
# 
# See the README.md file in this directory for more information

../../../terraform destroy --var-file=../../../terraform.tfvars -auto-approve
if (test $? -ne 0)
then
    print "Destroy of certificate failed"
    exit 1
fi

