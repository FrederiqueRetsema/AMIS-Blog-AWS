# cleanup-tests-dir.sh
# ====================
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

# Main program
# ============

remove_files
remove_terraform_directory

remove_zip_from_directory lambdas/unittest_test_accept
remove_zip_from_directory lambdas/unittest_test_decrypt
remove_zip_from_directory lambdas/unittest_test_update_db
remove_zip_from_directory lambdas/unittest_support_send_logs_from_unittest_support_echo
remove_zip_from_directory lambdas/unittest_support_echo
remove_zip_from_directory lambdas/perftest_get_stats

