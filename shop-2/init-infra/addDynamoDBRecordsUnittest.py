#!/usr/bin/python3

# addDynamoDBRecordsUnittest.py
# -----------------------------
# See also the comments in addDynamoDBRecords.py
#
# This script is called by init-infra.sh. Don't start it manually, use init-infra.sh for that. 

import sys
import boto3

# get_parameters
# --------------

def get_parameters():

  if (len(sys.argv) != 2):
      print ("Add the name_prefix and name_postfix as an argument, f.e. ./addDynamoDBRecordsUnittest.py AMIS")
      print ("It will add records to the AMIS-unittest-shops table")
      sys.exit(1)

  name_prefix            = sys.argv[1]

  return {"name_prefix": name_prefix}

# add_records
# -----------

def add_records(name_prefix):

  dynamodb = boto3.client("dynamodb")

  # Records with record_type starting with s-0 are for correct situations

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00000'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_minimum_values'},
      'selling_price'     : {'N': '0.01'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00001'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_updating_new_item'},
      'selling_price'     : {'N': '1'}})
    
  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00005'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_sold_twice'},
      'selling_price'     : {'N': '60.01'}})
    
  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00011'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_multiple_items_sold_in_one_message'},
      'selling_price'     : {'N': '1'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00012'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_multiple_items_sold_in_one_message'},
      'selling_price'     : {'N': '2'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00013'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_multiple_items_sold_in_one_message'},
      'selling_price'     : {'N': '3'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00014'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_multiple_items_sold_in_one_message'},
      'selling_price'     : {'N': '4'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00021'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_negative_stock'},
      'selling_price'     : {'N': '1'}})

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-00025'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_customer_returned_goods'},
      'selling_price'     : {'N': '5'}})

  # There shouldn't be records with record_type that start with s-2

  # This record with record_type s-9 is for testing maximum values (from our shop perspective)

  dynamodb.put_item(
    TableName= name_prefix + '-unittest-shops',
    Item={
      'shop_id'           : {'S': name_prefix + "1"},
      'record_type'       : {'S': 's-99999'},
      'stock'             : {'N': '100000'},
      'gross_turnover'    : {'N': '0'},
      'gross_number'      : {'N': '0'},
      'item_description'  : {'S': 'update_db_correct_maximum_values'},
      'selling_price'     : {'N': '1000.01'}})

  return

# Main program
# ============

response        = get_parameters()
name_prefix     = response["name_prefix"]

add_records(name_prefix)

