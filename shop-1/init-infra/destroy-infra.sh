# destroy-infra.sh
# ----------------
# Will use terraform to destroy the infrastructure
#
# WARNING:
# --------
# Destroy the shop FIRST, before you destroy the infrastructure!
#
# If you use the vagrant environment, use /home/vagrant/destroy-all.sh
# (which will call this script in the right way)

../../../terraform destroy --var-file=../../../terraform.tfvars -auto-approve
if (test $? -eq 1)
then
    echo "Destroy of infra failed"
    exit 1
fi
