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

from botocore.exceptions import ClientError

# get_fields_shop_id_and_decrypted_content
# ----------------------------------------

def get_fields_shop_id_and_decrypted_content(event):

  message = json.loads(event["Records"][0]["Sns"]["Message"])
  print("DEBUG: Message: "+json.dumps(message))

  shop_id           = message["shop_id"]
  decrypted_content = json.loads(message["decrypted_content"])

  print("DEBUG: decrypted_content: "+ json.dumps(decrypted_content))

  return {"shop_id": shop_id, "decrypted_content": decrypted_content}

# get_record_type
# ---------------
# Add leading zeroes to the item_no if necessary

def get_record_type(item_no):

  item_no     = int(item_no)
  record_type = "s-{:05d}".format(item_no)

  return {"record_type" : record_type } 

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
      print("DEBUG: Response of dynamodb.update_item: " + json.dumps(response))
    
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

  response          = get_fields_shop_id_and_decrypted_content(event)
  shop_id           = response["shop_id"]
  decrypted_content = response["decrypted_content"]

  response          = update_dynamodb(shop_id, decrypted_content["sales"])
  succeeded         = response["succeeded"]

  print("DEBUG: DONE: event: " + json.dumps(event) + \
            ", shop_id: " + shop_id + \
            ", succeeded: " + str(succeeded) + \
            ", context.get_remaining_time_in_millis(): " + str(context.get_remaining_time_in_millis()) + \
            ", context.memory_limit_in_mb: " + str(context.memory_limit_in_mb))

