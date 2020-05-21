import json
import copy
import boto3
import os
import base64
import time

from botocore.exceptions import ClientError

# FUNCTION NAME is the function name of the object under test (with AMIS_ prefix). 
# It is used to read or change the settings of this function (for creating an error 
# by changing the SNS ARN to a non existing ARN).

NAME_PREFIX   = os.environ["name_prefix"]
NAME          = "unittest_object_under_test_update_db"
FUNCTION_NAME = NAME_PREFIX + "_" + NAME
TABLE_NAME    = NAME_PREFIX + "-" + "unittest-shops"

# get_function_configuration
# --------------------------

def get_function_configuration():
  
  lambdaclient = boto3.client('lambda')
  response     = lambdaclient.get_function_configuration(
    FunctionName = FUNCTION_NAME
  )
  print("DEBUG: Response of lambdaclient.get_function_configuration: "+json.dumps(response))

  return {"function_configuration" : response }

# update_function_configuration
# -----------------------------

def update_function_configuration(environment):

  lambdaclient = boto3.client('lambda')
  response     = lambdaclient.update_function_configuration(
    FunctionName = FUNCTION_NAME,
    Environment  = environment
  )
  print("DEBUG: Response of lambdaclient.update_function_configuration: "+json.dumps(response))

  return

# update_environment_variables
# ----------------------------
# Environment variables of the Lambda function that is tested

def update_environment_variables(response, environment_variables):
  
  environment_new              = copy.deepcopy(response["Environment"])
  environment_new["Variables"] = environment_variables

  update_function_configuration(environment_new)

  return 

# invoke_lambda
# -------------
# Invoke lambda function and check response with what is expected print statements 
# can be used for debugging or to look at the lead time of the invoke function. To 
# keep the logs clean, I commented out most of them.

def invoke_lambda(test_id, event, expected_status_code, checkstring):

  lambdaclient = boto3.client('lambda')

  response = lambdaclient.invoke(
    FunctionName   = FUNCTION_NAME,
    InvocationType = "RequestResponse",
    LogType        = "Tail",
    Payload        = bytearray(json.dumps(event),'utf-8')
  )
  print("DEBUG: Response of lambdaclient.invoke: "+str(response))

  log_result        = str(base64.b64decode(response["LogResult"]))
  pos_in_log_result = log_result.find(checkstring)
  status_code       = response["StatusCode"]
  print("DEBUG: log: " + log_result)

  if (status_code == expected_status_code):
    print("DEBUG: " + test_id + ": Statuscode = "+str(status_code))
  else:
    print("ERROR: " + test_id + ": Statuscode = "+str(status_code)+", expected: "+str(expected_status_code))

  if ("Payload" in response):
    print("DEBUG: " + test_id + ": Payload = " + response["Payload"].read().decode('utf-8'))

  succeeded = (pos_in_log_result >= 0)
  
  return { "succeeded" : succeeded }

# invoke_lambda_and_check_error
# -----------------------------
# Same as before, check payload of error instead of logs

def invoke_lambda_and_check_error(test_id, event, expected_status_code, checkstring):
  
  pos_in_payload = 0
  lambdaclient   = boto3.client('lambda')

  response = lambdaclient.invoke(
    FunctionName   = FUNCTION_NAME,
    InvocationType = "RequestResponse",
    LogType        = "Tail",
    Payload        = bytearray(json.dumps(event),'utf-8')
  )
  print("DEBUG: Response of lambdaclient.invoke: "+str(response))

  log_result  = str(base64.b64decode(response["LogResult"]))
  status_code = response["StatusCode"]
  print("DEBUG: log: " + str(log_result))

  if (status_code == expected_status_code):
    print("DEBUG: " + test_id + ": Statuscode = "+str(status_code))
  else:
    print("ERROR: " + test_id + ": Statuscode = "+str(status_code)+", expected: "+str(expected_status_code))

  if ("Payload" in response):
    payload        = response["Payload"].read().decode('utf-8')
    pos_in_payload = payload.find(checkstring)
    print("DEBUG: " + test_id + ": Payload = " + response["Payload"].read().decode('utf-8'))

  succeeded = (pos_in_payload >= 0)
  
  return { "succeeded" : succeeded }

# get_valid_sns_event
# -------------------
# Used the text from a previous message (sent via shop-2/client/encrypt_and_send). This shouldn't be a problem because none 
# of the other parameters is checked.
  
def get_valid_sns_event(shop_id, sales_content):

  event = {
    "Records": [ 
        {
            "EventSource"          : "aws:sns",
            "EventVersion"         : "1.0",
            "EventSubscriptionArn" : "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db:4ff63cfa-8fec-4c14-a4ec-a65de1c2a885",
            "Sns": {
                "Type"              : "Notification",
                "MessageId"         : "7132f127-4f4d-516b-9452-a6000bfe0aed",
                "TopicArn"          : "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db",
                "Subject"           : "null",
                "Message"           : json.dumps({"shop_id": shop_id, "decrypted_content": json.dumps({"sales": sales_content })}),
                "Timestamp"         : "2020-05-02T09:50:43.421Z",
                "SignatureVersion"  : "1",
                "Signature"         : "YFm3a/fisT9b80QF92xZekEiEGXIcYchyHQAanAjr2h/nTNhthjF8LYJRz6TI1ui2pRO/8PNEtj3xf37m7dC0cGULg4hmNgZfdt1NaSeBLpPZsZzSb1S2ijawO6S6IdtVqcZkwkjNAvBVw4Zetba2J9hti2Fv8oNJbILs2WyxqQsNIriR3xGbDajNV3gBvAU/XobQSyIA8aGhrnSxrXp9S7lKrJYBr6liBYbA+rAHAkiN6ZLEAbXkTk2Wz4kiSkPB7Cd2LZGLbchQmuC3+W1BlGRZ6H3ouvh8pDwf5BjQ6qMTGQ33LkSVEWzPjiJTiv0lA26HGDd8yoYWU6F/OHWNw==",
                "SigningCertUrl"    : "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem",
                "UnsubscribeUrl"    : "https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db:4ff63cfa-8fec-4c14-a4ec-a65de1c2a885",
                "MessageAttributes" : {}
            }
        }
    ]
  }
  return { "event" : event }

# get_sns_event_without_shop_id
# -----------------------------
# Used the text from a previous message (sent via ./encrypt_and_send) and use it in this testset. 
# 
  
def get_sns_event_without_shop_id(sales_content):

  event = {
    "Records": [ 
        {
            "EventSource"          : "aws:sns",
            "EventVersion"         : "1.0",
            "EventSubscriptionArn" : "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db:4ff63cfa-8fec-4c14-a4ec-a65de1c2a885",
            "Sns": {
                "Type"              : "Notification",
                "MessageId"         : "7132f127-4f4d-516b-9452-a6000bfe0aed",
                "TopicArn"          : "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db",
                "Subject"           : "null",
                "Message"           : json.dumps({"decrypted_content": json.dumps({"sales": sales_content })}),
                "Timestamp"         : "2020-05-02T09:50:43.421Z",
                "SignatureVersion"  : "1",
                "Signature"         : "YFm3a/fisT9b80QF92xZekEiEGXIcYchyHQAanAjr2h/nTNhthjF8LYJRz6TI1ui2pRO/8PNEtj3xf37m7dC0cGULg4hmNgZfdt1NaSeBLpPZsZzSb1S2ijawO6S6IdtVqcZkwkjNAvBVw4Zetba2J9hti2Fv8oNJbILs2WyxqQsNIriR3xGbDajNV3gBvAU/XobQSyIA8aGhrnSxrXp9S7lKrJYBr6liBYbA+rAHAkiN6ZLEAbXkTk2Wz4kiSkPB7Cd2LZGLbchQmuC3+W1BlGRZ6H3ouvh8pDwf5BjQ6qMTGQ33LkSVEWzPjiJTiv0lA26HGDd8yoYWU6F/OHWNw==",
                "SigningCertUrl"    : "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem",
                "UnsubscribeUrl"    : "https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_update_db:4ff63cfa-8fec-4c14-a4ec-a65de1c2a885",
                "MessageAttributes" : {}
            }
        }
    ]
  }
  return { "event" : event }

# set_record
# ----------

def set_record(shop_id, record_type, gross_number, gross_turnover, stock):

  try:

    dynamodb = boto3.client('dynamodb')
    response = dynamodb.update_item (
      TableName = TABLE_NAME,
      Key       = {
        'shop_id'     : { "S": shop_id },
        'record_type' : { "S": record_type }
      },
      UpdateExpression = "set gross_number = :gross_number, gross_turnover = :gross_turnover, stock = :stock",
          ExpressionAttributeValues = {
              ':gross_number'   : {"N":gross_number},
              ':gross_turnover' : {"N":gross_turnover},
              ':stock'          : {"N":stock}
            },
      ReturnValues = "UPDATED_NEW"
    ) 
    print("DEBUG: Response of dynamodb.update_item: "+json.dumps(response))
    succeeded = True
    
  except ClientError as e:
    print("ERROR:" + shop_id + " - " + str(e))
    succeeded = False

  return {"succeeded": succeeded}

# get_record
# ----------
# Gets the values of a specific record

def get_record(shop_id, record_type):

  item      = {}
  succeeded = False

  try:

    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item (
      TableName = TABLE_NAME,
      Key       = {
        'shop_id'     : { "S": shop_id },
        'record_type' : { "S": record_type }
      },
      AttributesToGet = ["gross_number", "gross_turnover", "stock"],
      ConsistentRead  = True
    ) 
    print("DEBUG: Response of dynamodb.get_item: "+json.dumps(response))

    if ("Item" in response):
      item      = response["Item"]
      succeeded = True
    
  except ClientError as e:
    print("ERROR:" + shop_id + " - " + str(e))
    succeeded = False

  return {"succeeded": succeeded, "item": item}

# check_item 
# ----------

def check_item(item, expected_gross_number, expected_gross_turnover, expected_stock):

  succeeded          = True
  new_stock          = item["stock"]["N"]
  new_gross_number   = item["gross_number"]["N"]
  new_gross_turnover = item["gross_turnover"]["N"]

  if (new_gross_number != expected_gross_number):
    print("ERROR: Current value gross_number: " + new_gross_number + ", expected: " + expected_gross_number)
    succeeded = False

  if (new_gross_turnover != expected_gross_turnover):
    print("ERROR: Current value gross_turnover: " + new_gross_turnover + ", expected: " + expected_gross_turnover)
    succeeded = False

  if (new_stock != expected_stock):
    print("ERROR: Current value stock: " + new_stock + ", expected: " + expected_stock)
    succeeded = False

  return { "succeeded" : succeeded }

# get_and_check_item
# ------------------

def get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock):

  response  = get_record(shop_id, record_type) 
  succeeded = response["succeeded"]

  if (succeeded):
    item      = response["item"]
    response  = check_item(item, expected_gross_number, expected_gross_turnover, expected_stock)  
    succeeded = response["succeeded"]

  return { "succeeded": succeeded }

# testcase_update_db_correct_updating_new_item
# --------------------------------------------

def testcase_update_db_correct_updating_new_item():

  test_id                 = "testcase_update_db_correct_updating_new_item"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "0"
  initial_gross_turnover  = "0"
  initial_stock           = "100000"

  sales_item_no           = '00001'
  sales_gross_number      = '5'
  sales_gross_turnover    = '5'

  expected_status_code    = 200
  check_text              = "succeeded: True"

  expected_gross_number   = "5"
  expected_gross_turnover = "5" 
  expected_stock          = "99995"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
    succeeded = response["succeeded"]
    
  return { "succeeded" : succeeded }  
  
# testcase_update_db_correct_sold_twice
# -------------------------------------

def testcase_update_db_correct_sold_twice():

  test_id                 = "testcase_update_db_correct_sold_twice"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "0"
  initial_gross_turnover  = "0"
  initial_stock           = "100000"

  sales_item_no           = '00005'
  sales_gross_number      = '1'
  sales_gross_turnover    = '60.01'

  expected_status_code    = 200
  check_text              = "succeeded: True"

  expected_gross_number   = "2"
  expected_gross_turnover = "120.02" 
  expected_stock          = "99998"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = invoke_lambda(test_id, event, expected_status_code, check_text)
    succeeded = response["succeeded"]

    if (succeeded):
      response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
      succeeded = response["succeeded"]

  return {"succeeded" : succeeded}  

# testcase_update_db_correct_multiple_items_sold_in_one_message
# -------------------------------------------------------------

def testcase_update_db_correct_multiple_items_sold_in_one_message():

  test_id                   = "testcase_update_db_correct_multiple_items_sold_in_one_message"
  shop_id                   = 'AMIS1'

  initial_gross_number      = "0"
  initial_gross_turnover    = "0"
  initial_stock             = "100000"

  sales_item_no_1           = '00011'
  sales_gross_number_1      = '1'
  sales_gross_turnover_1    = '1'

  sales_item_no_2           = '00012'
  sales_gross_number_2      = '2'
  sales_gross_turnover_2    = '4'

  sales_item_no_3           = '00013'
  sales_gross_number_3      = '3'
  sales_gross_turnover_3    = '9'

  sales_item_no_4           = '00014'
  sales_gross_number_4      = '4'
  sales_gross_turnover_4    = '16'

  expected_status_code      = 200
  check_text                = "succeeded: True"

  expected_gross_number_1   = "1"
  expected_gross_turnover_1 = "1" 
  expected_stock_1          = "99999"
  
  expected_gross_number_2   = "2"
  expected_gross_turnover_2 = "4"
  expected_stock_2          = "99998"

  expected_gross_number_3   = "3"
  expected_gross_turnover_3 = "9" 
  expected_stock_3          = "99997"

  expected_gross_number_4   = "4"
  expected_gross_turnover_4 = "16" 
  expected_stock_4          = "99996"

  record_type_1             = 's-'+str(sales_item_no_1)
  record_type_2             = 's-'+str(sales_item_no_2)
  record_type_3             = 's-'+str(sales_item_no_3)
  record_type_4             = 's-'+str(sales_item_no_4)
  
  set_record(shop_id, record_type_1, initial_gross_number, initial_gross_turnover, initial_stock)
  set_record(shop_id, record_type_2, initial_gross_number, initial_gross_turnover, initial_stock)
  set_record(shop_id, record_type_3, initial_gross_number, initial_gross_turnover, initial_stock)
  set_record(shop_id, record_type_4, initial_gross_number, initial_gross_turnover, initial_stock)

  response = get_valid_sns_event(shop_id, [{"item_no": sales_item_no_1, "gross_number": sales_gross_number_1, "gross_turnover": sales_gross_turnover_1},
                                           {"item_no": sales_item_no_2, "gross_number": sales_gross_number_2, "gross_turnover": sales_gross_turnover_2},
                                           {"item_no": sales_item_no_3, "gross_number": sales_gross_number_3, "gross_turnover": sales_gross_turnover_3},
                                           {"item_no": sales_item_no_4, "gross_number": sales_gross_number_4, "gross_turnover": sales_gross_turnover_4}])
  event    = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_and_check_item(shop_id, record_type_1, expected_gross_number_1, expected_gross_turnover_1, expected_stock_1) 
    succeeded = response["succeeded"]

    if (succeeded == True):
      response  = get_and_check_item(shop_id, record_type_2, expected_gross_number_2, expected_gross_turnover_2, expected_stock_2) 
      succeeded = response["succeeded"]

      if (succeeded == True):
        response  = get_and_check_item(shop_id, record_type_3, expected_gross_number_3, expected_gross_turnover_3, expected_stock_3) 
        succeeded = response["succeeded"]

        if (succeeded == True):
          response  = get_and_check_item(shop_id, record_type_4, expected_gross_number_4, expected_gross_turnover_4, expected_stock_4) 
          succeeded = response["succeeded"]

  return {"succeeded" : succeeded }  
  
# testcase_update_db_correct_minimum_values
# -----------------------------------------

def testcase_update_db_correct_minimum_values():

  test_id                 = "testcase_update_db_correct_minimum_values"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "0"
  initial_gross_turnover  = "0"
  initial_stock           = "100000"

  sales_item_no           = '00000'
  sales_gross_number      = '1'
  sales_gross_turnover    = '0.01'

  expected_status_code    = 200
  check_text              = "succeeded: True"

  expected_gross_number   = "1"
  expected_gross_turnover = "0.01" 
  expected_stock          = "99999"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
    succeeded = response["succeeded"]

  return {"succeeded" : succeeded}  

# testcase_update_db_correct_maximum_values
# -----------------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# and get a 200 code and OK back

def testcase_update_db_correct_maximum_values():

  test_id                 = "testcase_update_db_correct_maximum_values"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "900000"
  initial_gross_turnover  = "900000000"
  initial_stock           = "100000"

  sales_item_no           = '99999'
  sales_gross_number      = '99999'
  sales_gross_turnover    = '99999999.99'

  expected_status_code    = 200
  check_text              = "succeeded: True"

  expected_gross_number   = "999999"
  expected_gross_turnover = "999999999.99" 
  expected_stock          = "1"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
    succeeded = response["succeeded"]
    
  return {"succeeded" : succeeded}  

# testcase_update_db_correct_negative_stock
# -----------------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# Negative stock can arrise when the administration isn't correct. We should get a 
# warning when this happens

def testcase_update_db_correct_negative_stock():

  test_id                 = "testcase_update_db_correct_negative_stock"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "0"
  initial_gross_turnover  = "0"
  initial_stock           = "100000"

  sales_item_no           = '00021'
  sales_gross_number      = '100001'
  sales_gross_turnover    = '100001'

  expected_status_code    = 200
  check_text              = "WARNING: stock is negative for item_no = 00021"

  expected_gross_number   = "100001"
  expected_gross_turnover = "100001"
  expected_stock          = "-1"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
    succeeded = response["succeeded"]
    
  return {"succeeded" : succeeded}  

# testcase_update_db_correct_customer_returned_goods
# --------------------------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# When customers return goods, both the gross_number and the gross_turnover will be negative.

def testcase_update_db_correct_customer_returned_goods():

  test_id                 = "testcase_update_db_correct_customer_returned_goods"
  shop_id                 = 'AMIS1'

  initial_gross_number    = "0"
  initial_gross_turnover  = "0"
  initial_stock           = "100000"

  sales_item_no           = '00025'
  sales_gross_number      = '-1'
  sales_gross_turnover    = '-5'

  expected_status_code    = 200
  check_text              = "succeeded: True"

  expected_gross_number   = "-1"
  expected_gross_turnover = "-5"
  expected_stock          = "100001"
  
  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  set_record(shop_id, record_type, initial_gross_number, initial_gross_turnover, initial_stock)

  response  = get_valid_sns_event(shop_id, sales_list)
  event     = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded):
    response  = get_and_check_item(shop_id, record_type, expected_gross_number, expected_gross_turnover, expected_stock) 
    succeeded = response["succeeded"]
    
  return {"succeeded" : succeeded}  

# testcase_update_db_error_event_without_shop_id
# ----------------------------------------------
# Error situation: pass an event that doesn't have the correct format

def testcase_update_db_error_event_without_shop_id():

  test_id                 = "testcase_update_db_error_event_without_shop_id"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20001'
  sales_gross_number      = '1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "KeyError"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_sns_event_without_shop_id(sales_list)
  event                   = response["event"]

  response  = invoke_lambda_and_check_error(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  return {"succeeded" : succeeded}  

# testcase_update_db_error_incorrect_table_name
# ---------------------------------------------
# It is hard to test an error situation in the call to update the DynamoDB table, as the error will come back from AWS. 
# The only way to test this, is to pass an incorrect parameter to the DynamoDB function. 
# This is done by changing the environment variable from the unittest_object_under_test_update_db function 
# and let it point to a non-existing table.

def testcase_update_db_error_incorrect_table_name():

  test_id                 = "testcase_update_db_error_incorrect_table_name"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20005'
  sales_gross_number      = '1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ResourceNotFoundException"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response                   = get_function_configuration()
  function_configuration_org = response["function_configuration"]
  environment_variables_org  = function_configuration_org["Environment"]["Variables"]

  environment_variables_new                = copy.deepcopy(environment_variables_org)
  environment_variables_new["name_prefix"] = "non-existing-"+environment_variables_new["name_prefix"]
  update_environment_variables(function_configuration_org, environment_variables_new)

  # We need to wait for 5 seconds before we call the function to force AWS to use the version of the 
  # function that we updated (not the version that is still in memory, including the old content of 
  # the environment variable)

  time.sleep(5)

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  update_environment_variables(function_configuration_org, environment_variables_org)

  return {"succeeded" : succeeded}  
  
# testcase_update_db_error_incorrect_shop_id
# ------------------------------------------

def testcase_update_db_error_incorrect_shop_id():

  test_id                 = "testcase_update_db_error_incorrect_shop_id"
  shop_id                 = 'UnknownShop'

  sales_item_no           = '20010'
  sales_gross_number      = '1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ValidationException"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_incorrect_item_id
# ------------------------------------------
# Send an item_id that isn't in our table

def testcase_update_db_error_incorrect_item_id():

  test_id                 = "testcase_update_db_error_incorrect_item_id"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20015'
  sales_gross_number      = '1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ValidationException"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_alpha_item_id
# --------------------------------------

def testcase_update_db_error_alpha_item_id():

  test_id                 = "testcase_update_db_error_alpha_item_id"
  shop_id                 = 'AMIS1'

  sales_item_no           = '2@@20'
  sales_gross_number      = '1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ValueError"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_alpha_gross_number
# -------------------------------------------

def testcase_update_db_error_alpha_gross_number():

  test_id                 = "testcase_update_db_error_alpha_gross_number"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20025'
  sales_gross_number      = 'x'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ValueError"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_alpha_gross_turnover
# ---------------------------------------------

def testcase_update_db_error_alpha_gross_turnover():

  test_id                 = "testcase_update_db_error_alpha_gross_turnover"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20030'
  sales_gross_number      = '1'
  sales_gross_turnover    = 'y'

  expected_status_code    = 200
  check_text              = "ValueError"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_negative_gross_number
# ----------------------------------------------
# (this means, that we got a product from the customer, and let the customer pay for it)

def testcase_update_db_error_negative_gross_number():

  test_id                 = "testcase_update_db_error_negative_gross_number"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20035'
  sales_gross_number      = '-1'
  sales_gross_turnover    = '1'

  expected_status_code    = 200
  check_text              = "ERROR: we gave products away -and- money, or we got products back -and- realised positive turnover for that: shop_id = AMIS1, item_no = 20035, gross_number = -1, gross_turnover = 1"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# testcase_update_db_error_negative_gross_turnover
# ------------------------------------------------
# (this means, that we gave a product away to the customer, and also gave the customer money)

def testcase_update_db_error_negative_gross_turnover():

  test_id                 = "testcase_update_db_error_negative_gross_turnover"
  shop_id                 = 'AMIS1'

  sales_item_no           = '20040'
  sales_gross_number      = '1'
  sales_gross_turnover    = '-1'

  expected_status_code    = 200
  check_text              = "ERROR: we gave products away -and- money, or we got products back -and- realised positive turnover for that: shop_id = AMIS1, item_no = 20040, gross_number = 1, gross_turnover = -1"

  record_type             = 's-'+str(sales_item_no)
  sales_list              = [{"item_no": sales_item_no, "gross_number": sales_gross_number, "gross_turnover": sales_gross_turnover}]
  
  response                = get_valid_sns_event(shop_id, sales_list)
  event                   = response["event"]

  response  = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded = response["succeeded"]

  if (succeeded == True):
    response  = get_record(shop_id, record_type) 
    succeeded = (response["succeeded"] == False)

  return {"succeeded" : succeeded}  

# Main function
# =============
# Event is not relevant. 

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  ok          = 0
  errors      = 0
  checklist   = []
  
  name_prefix = os.environ['name_prefix']

  testcase_list = [testcase_update_db_correct_updating_new_item,
                   testcase_update_db_correct_sold_twice,
                   testcase_update_db_correct_multiple_items_sold_in_one_message,
                   testcase_update_db_correct_minimum_values,
                   testcase_update_db_correct_maximum_values,
                   testcase_update_db_correct_negative_stock,
                   testcase_update_db_correct_customer_returned_goods,
                   testcase_update_db_error_event_without_shop_id,
                   testcase_update_db_error_incorrect_table_name,
                   testcase_update_db_error_incorrect_shop_id,
                   testcase_update_db_error_incorrect_item_id,
                   testcase_update_db_error_alpha_item_id,
                   testcase_update_db_error_alpha_gross_number,
                   testcase_update_db_error_alpha_gross_turnover,
                   testcase_update_db_error_negative_gross_number,
                   testcase_update_db_error_negative_gross_turnover]
                   
  for testcase in testcase_list:
    response           = testcase()
    update_db_testcase = response["succeeded"]

    if (update_db_testcase):
      print("INFO: " + testcase.__name__ + " succeeded")
      ok += 1
    else:
      print("ERROR: in " + testcase.__name__)
      errors += 1

  print("INFO: OK: "+str(ok)+", Errors: "+str(errors))

  print("DEBUG: DONE: event: " + json.dumps(event))

