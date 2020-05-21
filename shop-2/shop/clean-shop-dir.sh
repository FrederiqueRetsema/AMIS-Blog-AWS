# cleanup-shop-dir.sh
# ===================
# This script can be used after the (succesful) destroy, to delete unnecessary files and directories.
# In this way, it is more clear which files are relevant - and which ones are not.
#
# Using this script when there are still objects in AWS is dangerous: terraform (and therefore: the 
# destroy scripts) cannot destroy them for you. Use this script with caution, in general you will not
# need it as a user of this repository.

# remove_files
# ------------

function remove_files {

  rm -f *.tfplans
  rm -f *.tfstate
  rm -f *.backup

}

# remove_terraform_directory
# --------------------------

function remove_terraform_directory {

  rm -fr .terraform

}

# remove_zip_from_directory
# -------------------------

function remove_zip_from_directory {

  directory=$1
  cd $1

  rm -f *zip
  cd ../..
  
}

# remove_all_from_directory_except_codefile
# -----------------------------------------

function remove_all_from_directory_except_codefile {

  directory=$1
  codefile=$2

  cd ${directory}
  ls | grep -v ${codefile} | xargs rm -fr
  cd ../..

}

# Main program
# ============

remove_files
remove_terraform_directory

remove_zip_from_directory lambdas/shop_accept
remove_zip_from_directory lambdas/shop_decrypt
remove_zip_from_directory lambdas/shop_update_db

remove_all_from_directory_except_codefile lambdas/smoketest_test smoketest_test.py
remove_all_from_directory_except_codefile lambdas/perftest_test  perftest_test.py

