# init-infra

These scripts are used to initialize the shop example for the blogs about the shop in AWS. See the root
directory of this repository to see a pdf of the blog, or go to https://technology.amis.nl to search for it.

When you want to initialize an environment yourself and if you are new to the combination of Terraform and 
AWS, it might be easyer to go to the vagrant directory and use vagrant to set up the environment for you. 
You will find more information in the README.md file in the vagrant directory and can ignore the rest of 
the README.md you are reading now.

## Before initialization

Before using these scripts, download Terraform version 0.12.24 and unzip the downloadfile. Put the
terraform.exe file in the same directory as you used the git clone command: the scripts use the relative
directory ../.. for this (you might want to change the batch scripts if this is different in your 
environment).The server where these scripts are used must also have the AWS CLI, Python3 and boto3 installed.

The scripts in ../init-cert, this directory and the ../shop directory all use the same access key of a user 
that is able to create, change and delete IAM users, groups, policies. The user also needs to be able 
to create or delete certificates and DNS-records in Route53 (but only if you have your own public domain
and only if you want to use this domain for this example).  It also needs permission to create/delete KMS 
keys, DynamoDB tables/records, the API gateway, Lambda functions, SNS topics. If you need help in creating 
the access key and secret access key, then please read ../vagrant/README.md. 

Copy terraforms-template.tfvars to ../../terraform.tfvars and change the content: add the access key and the
secret access key of an administrative user to this file, change other parameters if you want to and run
the `init-infra.sh` script.

__WARNING__: you need a star certificate if you use a public domain name. For example, when you use 
retsema.eu as domain name, you need a certificate *.retsema.eu . Terraform can create this for you, but it 
is not part of the scripts in this directory.

To help you, you can request this certificate by using the `init-cert.sh` script in the directory 
../init-cert

## List of parameters in ../../terraform.tfvars
Please mind, that if you use the init-all.sh script, then many of these defaults are changed automatically.

``` terraform.tfvars
aws_access_key         = "your access key"        (administrator user)
aws_secret_key         = "your secret access key" (administrator user)
aws_region             = "eu-west-1"              (region for the SIG: pipelines and shops are build in this region)

use_public_domain      = 1                        (do you use your own public domain (1) - or not (0)). 
domainname             = "retsema.eu"             (domain name that is used for the SIG, this should be an external domain name that 
                                                   exists on the public internet).

name_prefix            = "AMIS"                   (prefix for all objects: users, groups, policies, SNS topics, Lambda functions, etc)
key_prefix             = "KeyL-"                  (when something goes wrong with destroying the environment, then the keys are 
                                                   destroyed but the aliases are not disconnected. When you try to create a new key 
                                                   with the same label (f.e. KeyI-AMIS1) then this will fail, even when the key is 
                                                   marked for deletion. See the faq in ../vagrant/faq.pdf how to fix this)
```

## Changes for AWS CLI

The AWS CLI is not used in the scripts. We do need the ~/.aws/config and ~/.aws/credentials file. Please 
install the AWS CLI (yum install aws-cli -y) and use `aws configure` to add AWS access key, secret access key,
default region (which should be the region you use to look at the shop example) to your environment.

## Shell scripts

The following shell scripts exist:

### `init-infra.sh`

This script will use terraform-init.tf to create all relevant objects:
- IAM: policies, roles. There are (three) different roles and policies for the accept, the decrypt and the process Lambda function.
- KMS: one key per shop. The prefix of this key is defined in the ../../terraform.tfvars file. The number of two possible shops (AMIS1 and AMIS2) are hard coded in the scripts.
- DynamoDB: there is one DynamoDB table for all the shops.

After using `init-infra.sh`, you are ready to use `init-shop.sh` (in the ../shop directory) to create shop objects.

### `destroy-infra.sh`

When you want to stop, use the `destroy-shop.sh` (in the ../shop directory) to delete the shop objects.\
When all shop objects are destroyed, you can use `terraform destroy` in this directory to destroy all infra objects. \
When you also want to destroy certificate, use `destroy-cert.sh` (in the init-cert directory) to delete the certificate and the check DNS entry. Please read the README.md file in that directory before executing the `destroy-cert.sh` script.

### `clean-infra-dir.sh`

When all objects are destroyed using the destroy-infra.sh script, you might want to delete the specific
Terraform directories and files. Use this script only when you are certain that there are no objects left in AWS 
that are created by Terraform. The clean script will NOT delete the tfvars files in the ../.. directory, you might 
want to clean this up yourself.

In general, you will not need this script as a user of this repository. It can be handy if you made changes and
want to have a quick look in the directory which files you changed (and which ones should still be changed). If
you just follow the blogs, don't use the clean scripts.

