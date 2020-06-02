#/usr/bin/bash
#
# destroy-all.sh
# --------------
# 

BLOG_REPO_NAME="AMIS-Blog-AWS"
BLOG_DIR="shop-3"

# ask_yes_no_question
# -------------------
# Ask the user a yes/no question and convert the answer to uppercase
 
function ask_yes_no_question {

  read answer
  answer=`echo ${answer} | tr '[:lower:]' '[:upper:]'`

  echo $answer
}

# destroy_tests_if_needed
# -----------------------
# The line is: use_test_objects = 0 (or 1). The 0 (or 1) is $3 in this line.

function destroy_tests_if_needed {

  use_test_objects=`grep use_test_objects ~/terraform.tfvars | awk -F" " '{print $3}'`
  if (test "${use_test_objects}" == "1")
  then
    cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/tests
    ./destroy-tests.sh
    if (test $? -ne 0)
    then
      echo Destroy of shop failed
      exit 1
    fi 
  fi

}

# destroy_shop
# ------------

function destroy_shop {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/shop
  ./destroy-shop.sh
  if (test $? -ne 0)
  then
    echo Destroy of shop failed
    exit 1
  fi 

}

# destroy_infra
# -------------

function destroy_infra {

  cd ~/${BLOG_REPO_NAME}/${BLOG_DIR}/init-infra
  ./destroy-infra.sh
  if (test $? -ne 0)
  then
    echo Destroy of infrastructure failed
    exit 1
  fi

}

# destroy_cert
# ------------

function destroy_cert {
        cd ~/AMIS-unpublished/shop-2/init-cert
        ./destroy-cert.sh
        if (test $? -ne 0)
        then
          echo Destroy of certificate failed
          exit 1
        fi

}

# info_destroy_cert
# -----------------

function info_destroy_cert {

  echo "======================================================================================================================================"
  echo "Did you install the certificate via the script (/home/vagrant/init-all.sh) AND do you want to delete the certificate?"
  echo "(please mind that you shouldn't do this too often because of the AWS limits on the number of certificates you are allowed to request per year - this defaults to 20)"
  echo ""
  echo "Only yes will destroy the certificate"

}

# destroy_cert_if_needed
# ----------------------
# Format: domainname = "this-is-the-domainname". So: " as delimiter means that $2 = the domainname

function destroy_cert_if_needed {

  domainname=`grep domainname ~/terraform.tfvars | awk -F"\"" '{print $2}'`
  certificate=`aws acm list-certificates | grep "*.${domainname}"`

  if (test "${certificate}" == "")
  then
      echo "Certificate is already deleted"
  else

    info_destroy_cert

    # Read the anser and convert it to upper case
    #

    destroy_cert_objects=$(ask_yes_no_question)

    # Only YES will lead to destruction 
    #
    if (test "${destroy_cert_objects}" == "YES")
    then
        destroy_cert
    else
        echo "Didn't destroy the certificate"
    fi
    
  fi

}

# Main program
# ============
#

destroy_tests_if_needed
destroy_shop
destroy_infra
destroy_cert_if_needed

