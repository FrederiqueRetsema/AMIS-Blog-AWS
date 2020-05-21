#!/usr/bin/python3

# addDynamoDBRecords.py
# ---------------------
#
# It would be better to do this in the terraform file, but there is an error in terraform that adding new records will give
# an error. When this is fixed, this script will be deleted and will become part of the terraform_infra.tf config file.
#
# See also: https://github.com/terraform-providers/terraform-provider-aws/issues/12545 and 
# https://github.com/FrederiqueRetsema/TerraformDynamoDBIssue
#
# This script is called by init-infra.sh. Don't start it manually, use init-infra.sh for that. 

import sys
import boto3

# get_parameters
# --------------

def get_parameters():

  if (len(sys.argv) != 2):
      print ("Add the name_prefix and name_postfix as an argument, f.e. ./addDynamoDBRecords.py AMIS")
      print ("This will add the records for 2 shops (AMIS1 and AMIS2) to the database")
      sys.exit(1)

  name_prefix            = sys.argv[1]

  return {"name_prefix": name_prefix}

# add_records
# -----------

def add_records(name_prefix):

  dynamodb = boto3.client("dynamodb")
  for shop_no in range(2):

    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(shop_no+1)},
          'record_type'       : {'S': 's-00098'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '250 g Butter'},
          'selling_price'     : {'N': '2.45'}})
    
    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(shop_no+1)},
          'record_type'       : {'S': 's-12345'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '1 kg Chees'},
          'selling_price'     : {'N': '12.15'}})
    
    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(shop_no+1)},
          'record_type'       : {'S': 's-81279'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': '10 Eggs'},
          'selling_price'     : {'N': '1.99'}})

    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(shop_no+1)},
          'record_type'       : {'S': 's-90001'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': 'Test object smoke- and performancetests (1)'},
          'selling_price'     : {'N': '1'}})

    dynamodb.put_item(
      TableName= name_prefix + '-shops',
      Item={
          'shop_id'           : {'S': name_prefix + str(shop_no+1)},
          'record_type'       : {'S': 's-90002'},
          'stock'             : {'N': '100000'},
          'gross_turnover'    : {'N': '0'},
          'gross_number'      : {'N': '0'},
          'item_description'  : {'S': 'Test object smoke- and performancetests (2)'},
          'selling_price'     : {'N': '2'}})

  return

# Main program
# ============

response        = get_parameters()
name_prefix     = response["name_prefix"]

add_records(name_prefix)

