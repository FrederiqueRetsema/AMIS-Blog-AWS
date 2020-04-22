# addDynamoDBRecords.py
# ---------------------
#
# It would be better to do this in the terraform file, but there is an error in terraform that adding new records will give
# an error. When this is fixed, this script will be deleted and will become part of the terraform_infra.tf config file.
#
# This script is called by init-infra.sh. Advice: don't start it manually, use init-infra.sh for that. 
#

import sys
import boto3

# get_parameters
# --------------
# Get the parameters and give an error if there are no three parameters
# 

def get_parameters():

  if (len(sys.argv) != 2):
      print ("Add the name_prefix as an argument, f.e. ./addDynamoDBRecords.py AMIS")
      print ("This will add the records for 2 shops (AMIS1 and AMIS2) to the database")
      sys.exit(1)

  name_prefix            = sys.argv[1]

  return {"name_prefix": name_prefix}

# add_records
# -----------
# Add three records for two shops to the database
#

def add_records(prefix):

  for userNumber in range(2):
    dynamodb = boto3.client("dynamodb")
    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(userNumber+1)},
          'record_type'       : {'S': 's-00098'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '250 g Butter'},
          'selling_price'     : {'N': '2.45'}})

    
    dynamodb.put_item(
      TableName = name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(userNumber+1)},
          'record_type'       : {'S': 's-12345'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '1 kg Chees'},
          'selling_price'     : {'N': '12.15'}})
    
    dynamodb.put_item(
      TableName = name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(userNumber+1)},
          'record_type'       : {'S': 's-91279'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '10 Eggs'},
          'selling_price'     : {'N': '1.99'}})

  return

# Main program
# ------------

# Get parameters

response        = get_parameters()
name_prefix     = response["name_prefix"]

# Add records

add_records(name_prefix)

