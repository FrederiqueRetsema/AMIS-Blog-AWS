#/usr/bin/bash
#
# destroy-all.sh
# --------------
# 

# get the domain name from the tfvars file:
# - first, get the line with nameprefix from terraform.tfvars
# - the line is: domainname = "this-is-the-domainname". So: when we use space as delimiter, the part behind the "=" sign is the third parameter
# - Now we have "this-is-the-domainname", but we have to get rid of the double quotes. This can be done, to see the double quote as the delimiter.
#   The line starts with the delimiter, so $1 = empty, and $2 = this-is-the-domainname. The delimiter itself is stripped from the result. 

domainname=`grep domainname ~/terraform.tfvars | awk -F" " '{print $3}' | awk -F"\"" '{print $2}'`

# Destroy the shop first...
# 

cd ~/AMIS-unpublished/shop-1/shop
./destroy-shop.sh
if (test $? -ne 0)
then
  echo Destroy of shop failed
  exit 1
fi


# Then destroy the infra...
#

cd ~/AMIS-unpublished/shop-1/init-infra
./destroy-infra.sh
if (test $? -ne 0)
then
  echo Destroy of infrastructure failed
  exit 1
fi


# Then destroy the certificate (if necessary)
# 

certificate=`aws acm list-certificates | grep "*.${domainname}"`

if (test "${certificate}" == "")
then
    echo "Certificate is already deleted"
else

    echo "======================================================================================================================================"
    echo "Did you install the certificate via the script (/home/vagrant/init-all.sh) AND do you want to delete the certificate?"
    echo "(please mind that you shouldn't do this too often because of the AWS limits on the number of certificates you are allowed to request per year - this defaults to 20)"
    echo ""
    echo "Only yes will destroy the certificate"

    # Read the anser and convert it to upper case
    #

    read answer
    answer=`echo $answer | tr '[:lower:]' '[:upper:]'`

    # Only YES will lead to destruction 
    #
    if (test "${answer^^}" == "YES")
    then
        cd ~/AMIS-unpublished/shop-1/init-cert
        ./destroy-cert.sh
        if (test $? -ne 0)
        then
          echo Destroy of certificate failed
          exit 1
        fi

    else
        echo "Didn't destroy the certificate"
    fi
    
fi

echo "Done"
