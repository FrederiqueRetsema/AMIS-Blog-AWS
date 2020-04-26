# init-cert.sh
# ------------
# Used to initialise the certificate

# WARNING: Be aware, that using init-cert.sh and destroy-cert.sh a lot, might lead into
# errors in AWS: you are allowed to request 20 certificates per year. 
#
# See also the README.md file in this directory.

../../../terraform init --var-file=../../../terraform.tfvars
if (test $? -ne 0)
then
    print "Init of certificate failed"
    exit 1
fi

../../../terraform plan --var-file=../../../terraform.tfvars --out terraform.tfplans
if (test $? -ne 0)
then
    print "Plan of certificate failed"
    exit 1
fi

../../../terraform apply "terraform.tfplans"
if (test $? -ne 0)
then
    print "Apply of certificate failed"
    exit 1
fi


