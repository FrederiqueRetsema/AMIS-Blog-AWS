#####################################################################
#                                                                   #
#          DON'T START THIS LAMBDA FUNCTION VIA THE GUI !           #
#          ==============================================           #
#                                                                   #
#          Use the smoketest Lambda function (or encrypt_and_send   #
#          in the client directory on the VM) instead...            #
#                                                                   #
#####################################################################

import json
import boto3
import os
import base64
import datetime

from botocore.exceptions import ClientError
from aws_xray_sdk.core   import patch

# get_fields_from_event
# ---------------------

def get_fields_from_event(event):

  message = json.loads(event["Records"][0]["Sns"]["Message"])
  print("DEBUG: Message: "+json.dumps(message))

  shop_id           = message["shop_id"]
  message_id        = message["message_id"]
  decrypted_content = json.loads(message["decrypted_content"])

  print("DEBUG: decrypted_content: "+ json.dumps(decrypted_content))

  return {"shop_id": shop_id, "message_id": message_id, "decrypted_content": decrypted_content}

# get_record_type
# ---------------
# Add leading zeroes to the item_no if necessary

def get_record_type(item_no):

  item_no     = int(item_no)
  record_type = "s-{:05d}".format(item_no)

  return {"record_type" : record_type } 

# get_date_from_message_id
# ------------------------

def get_date_from_message_id(message_id):

  pos  = message_id.find("-")
  date = message_id[pos+1:]

  return { "date": date }

# get_current_date
# ----------------

def get_current_date():

  date_object = datetime.date.today()

  year  = date_object.year
  month = date_object.month
  day   = date_object.day

  format_string = "{year:04}{month:02}{day:02}"
  current_date  = format_string.format(year = year, month = month, day = day)

  return { "current_date": current_date }

# get_time_to_live
# ----------------

def get_time_to_live():

  date_object = datetime.date.today()

  year  = date_object.year
  month = date_object.month
  day   = date_object.day

  hour  = 23
  min   = 59

  datetime_object = datetime.datetime(year, month, day, hour, min)
  epoch_time      = (datetime_object - datetime.datetime(1970,1,1)).total_seconds()
  time_to_live    = int(epoch_time)

  return { "time_to_live": time_to_live }

# message_is_sent_today
# ---------------------

def message_is_sent_today(message_id):

  response             = get_date_from_message_id(message_id)
  date_from_message_id = response["date"]

  print("DEBUG: date_from_message_id: " + date_from_message_id)

  response      = get_current_date()
  current_date  = response["current_date"]

  print("DEBUG: current_date: " + current_date)

  is_sent_today = (date_from_message_id == current_date)
  
  return { "is_sent_today": is_sent_today }

# is_double_record
# ----------------

def is_double_record(shop_id, message_id):

  name_prefix   = os.environ['name_prefix']
  double_record = False

  response      = get_time_to_live()
  time_to_live  = str(response["time_to_live"])

  try:
    print("DEBUG: put_item to shops-message-ids for shop = " + shop_id + " - message_id = " + message_id + " - time_to_live = " + time_to_live)
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.put_item (
      TableName = name_prefix + "-shops-message-ids",
      Item      = {
          'shop_id'      : { "S" : shop_id      },
          'message_id'   : { "S" : message_id   },
          'time_to_live' : { "N" : time_to_live }
        },
      ConditionExpression = "attribute_not_exists(message_id)"
    ) 
    print("DEBUG: response of put_item (shops-message-ids): "+json.dumps(response))

    double_record = False

  except ClientError as e:
    print("ERROR: " + shop_id + " - " + str(e))
    double_record = True

  return { "double_record" : double_record } 

# update_dynamodb
# ---------------

def update_dynamodb(shop_id, sales):

  try:

    name_prefix = os.environ['name_prefix']
    
    for sales_item in sales:

      item_no        = sales_item["item_no"]

      response       = get_record_type(item_no)
      record_type    = response["record_type"]

      gross_number   = sales_item["gross_number"]
      gross_turnover = sales_item["gross_turnover"]
    
      if (((float(gross_number) > 0 ) and (float(gross_turnover) < 0)) or
          ((float(gross_number) < 0 ) and (float(gross_turnover) > 0))):
        print("ERROR: we gave products away -and- money, or we got products back -and- realised positive turnover for that: shop_id = "+str(shop_id)+", item_no = "+str(item_no)+", gross_number = " + str(gross_number)+ ", gross_turnover = " + str(gross_turnover))
        break
    
      print("INFO: Update fields based on sales: shop_id: " + shop_id + " - record_type: " + record_type + " - gross_number: " + str(gross_number) + " - gross_turnover: " + str(gross_turnover))
     
      dynamodb = boto3.client('dynamodb')
      response = dynamodb.update_item (
          TableName = name_prefix + "-shops",
          Key       = {
                         'shop_id'     : { "S" : shop_id     },
                         'record_type' : { "S" : record_type }
          },
          UpdateExpression = "set gross_number   = gross_number   + :gross_number," +\
                                " gross_turnover = gross_turnover + :gross_turnover," +\
                                " stock          = stock          - :gross_number",
          ExpressionAttributeValues = {
                                ':gross_number'  : { "N" : gross_number   },
                                ':gross_turnover': { "N" : gross_turnover }
            },
          ReturnValues = "UPDATED_NEW"
        ) 
      print("DEBUG: Response of dynamodb.update_item (shops): " + json.dumps(response))
    
      if (float(response["Attributes"]["stock"]["N"]) < 0):
        print("WARNING: stock is negative for item_no = "+str(item_no))
    
    succeeded = True
    
  except ClientError as e:
    print("ERROR: " + shop_id + " - " + str(e))
    succeeded = False

  return {"succeeded": succeeded}

# Main function
# =============

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  # Used for X-Ray
  patch(['botocore'])

  succeeded         = False

  response          = get_fields_from_event(event)
  shop_id           = response["shop_id"]
  message_id        = response["message_id"]
  decrypted_content = response["decrypted_content"]

  response          = message_is_sent_today(message_id)
  is_sent_today     = response["is_sent_today"]

  if (is_sent_today == True):

    response          = is_double_record(shop_id, message_id)
    double_record     = response["double_record"]

    if (double_record == False):
      response          = update_dynamodb(shop_id, decrypted_content["sales"])
      succeeded         = response["succeeded"]
    else:
      print("WARNING: message sent twice: " + json.dumps(event))
      succeeded         = False

  else:
    print("WARNING: message not sent today or incorrect message_id: " + json.dumps(event))

  print("DEBUG: DONE: event: " + json.dumps(event) + \
            ", shop_id: " + shop_id + \
            ", succeeded: " + str(succeeded) + \
            ", context.get_remaining_time_in_millis(): " + str(context.get_remaining_time_in_millis()) + \
            ", context.memory_limit_in_mb: " + str(context.memory_limit_in_mb))

