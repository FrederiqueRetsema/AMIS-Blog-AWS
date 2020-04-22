# init-shop

These scripts are used to initialize the settings per shop. See the AMIS-Blog-AWS/shop-1 directory
for a pdf of the blog or go to https://technology.amis.nl and search for it.

Advise: use Vagrant and the `init-all.sh` script in the home directory of the vagrant user to 
deploy the objects. It saves you a lot of trouble! You don't have to read the rest of this file 
if you use vagrant. See ../vagrant/README.md for more information.

## Before initialization

Before using these scripts, download Terraform version 0.12.24 and unzip the downloadfile. Put the 
terraform.exe file in the root of the directory that this directory is in (or change the batch scripts).
The server where these scripts are used must also have the AWS CLI, Python3 and boto3 installed. 

See ../init-infra/README.md for permissions that are used by the terraform scripts. You will also find
a list of parameters in ../../../terraform.tfvars and their descriptions.

## Shell scripts

The following shell scripts exist:

### init-infra.sh

This script will use terraform-init.tf to create all relevant objects:
- CertificateManagement: a certificate will be used for the domain (but only if you use a public domain). Please mind, that creating a certificate can take some minutes. When the process hasn't finished yet, creating shop items with init-shop.sh might fail.
- Route53: a DNS record with the shop_id will be added to the domain (also only when you use a public domain)
- API gateway: a new API gateway will be added to AWS
- Lambda functions: three Lambda functions will be added to AWS
- SNS topics: two SNS topics will be added to AWS

### destroy-infra.sh

When you want to stop, use the `destroy-shop.sh` (in this directory) to delete the shop objects that have been created by `init-shop.sh` \ 
After that, use the `destroy-infra.sh` script (in the directory ../init-infra) to destroy the infra objects \
If you want to destroy the certificate (that has been created by Terraform), then you can use the `destroy-cert.sh` script in the ../init-cert directory to do so. Please read ../init-cert/README.md before you do.

### clean-infra-dir.sh

When all objects are destroyed using the destroy-infra.sh script, you might want to delete the specific
Terraform directories and files. This script will NOT delete the tfvars files in the ../.. directory,
you might want to clean this up yourself.

In general, you will not need this script as a user of this repository. It can be handy if you made changes and
want to have a quick look in the directory which files you changed (and which ones should still be changed). If
you just follow the blogs, don't use the clean scripts.

