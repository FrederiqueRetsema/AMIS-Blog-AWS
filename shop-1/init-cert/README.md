# AMIS-Blog-AWS/shop-1/init-cert

These scripts are used to request or destroy the certificate that is used. See the blog(s) in the directory
above this one for more information.

When you want to use these scripts in your own AWS environment, please use the vagrant directory in this
repository: this will save you a lot of manual configuration. When you use vagrant, you don't need to 
read the rest of this information: all the actions will be done for you.

## Before initialization

Before using these scripts, download Terraform version 0.12.24 and unzip the downloadfile. Put the
terraform.exe file one level higher than the gitlab directory. Relative to this path, this is in ../../.. 
(change the shell scripts if this is different in your environment). The server where these scripts are used 
must also have the AWS CLI, Python3 and boto3 installed (though the scripts in this specific directory only 
use Terraform).

The scripts use the access keys of a user that is able to create and delete a certificate in the CertificateManager 
and is able to add or delete a DNS-record in your Route53 domain.

Copy terraforms-template.tfvars from ../init-infra to ../../../terraform.tfvars and change the content: add the 
access key and the secret access key of (preferably) an administrator to this file.

## List of parameters in ../../../terraform.tfvars

The init-cert scripts use the same terraform.tfvars file as the files in the init-infra directory. See the 
README.md file in init-infra for more information about these parameters.

The terraform_cert.tf script will use just a few parameters. See the first lines in this file to see which
parameters are used and which ones are not used.

## Shell scripts

The following shell scripts exist:

### `init-cert.sh`

This script will use terraform-init.tf to create all relevant objects:
- CertificateManagement: a certificate will be created for the domain. Please mind, that creating a certificate can take some minutes. When the certificate isn't checked yet (by AWS), creating shop items with `init-shop.sh` might fail.
- Route53: to be able to check if the domain that you request a certificate for really belongs to you, AWS asks you to add a CNAME record in the DNS. This is done automatically by this Terraform script (assuming you use Route53)

After using `init-cert.sh`, you are ready to use `init-infra.sh` (in the init-infra directory) to create the other 
infra objects and, after that, use `init-shop.sh` (in the shop directory) to create shop objects.

### `destroy-cert.sh`

When you want to stop, use the `destroy-shop.sh` (in the shop directory) to delete the shop objects.\
When all shop objects are destroyed, you can use destroy-infra.sh to use `terraform destroy` to destroy all infra objects. \
When all infra objects are destroyed, you can use destroy-cert.sh to use `terraform destroy` to destroy the certificate 
and the Route53 objects. See the warning in the README.md file of the vagrant directory about creating and deleting 
certificate too often, you might want to keep the star certificate for later use.

### `clean-cert-dir.sh`

When all objects are destroyed using the destroy-infra.sh script, you might want to delete the specific
Terraform directories and files. This script will NOT delete the tfvars files in the ../../.. directory,
you might want to clean this up yourself after all objects are deleted.

