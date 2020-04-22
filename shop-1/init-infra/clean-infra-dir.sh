# cleanup-init-infra-dir.sh
# -------------------------
# This script can be used after the (succesful) destroy, to delete unnecessary files and directories.
# In this way, it is more clear which files are relevant for source control - and which ones are not.
#
# Using this script when there are still objects in AWS is dangerous: terraform (and therefore: the 
# destroy scripts) cannot destroy them for you. Use this script with caution, in general you will not
# need it as a user of this repository.

# Files:

rm -f *.tfplans
rm -f *.tfstate
rm -f *.backup
rm -f *.txt

# Directories:

rm -fr .terraform

