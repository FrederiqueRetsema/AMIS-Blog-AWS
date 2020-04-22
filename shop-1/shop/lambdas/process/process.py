import json
import boto3
import os
import base64

from botocore.exceptions import ClientError

# get_shop_id_and_decrypt_content
# -------------------------------
# The only two fields in the content that are relevant to this function are the shop_id and
# the decrypted content.
#
# Please mind, that this function will crash when the event structure is incorrect. This 
# might be caused by using the Test functionality in the Lambda GUI.
#

def get_shop_id_and_decrypted_content(event):

  message = json.loads(event["Records"][0]["Sns"]["Message"])
  print("Message: "+json.dumps(message))

  shop_id = message["shop_id"]
  decrypted_content = json.loads(message["decrypted_content"])

  return {"shop_id": shop_id, "decrypted_content": decrypted_content}

# update_dynamodb
# ---------------
# In the decrypted content there can be multiple sales (for one customer). 
#
# The record_type = 's-' + item number. This is done, to make it possible to use this table
# for multiple purposes, for example also to store general information per shop (such a 
# record might have the record_type "info", and fields like address, place, telephone number, 
# etc. It isn't added here to keep it simple.
# 
# Updates are done using atomic updates. That means that other processes cannot change this
# record on the same time as we are changing it and that, if multiple functions try to change
# the same record, other processes will have to wait until we are ready (vv). 
# 
# We use a dynamic prefix (can be found in the environment variables, will be put there by
# the Terraform script)
def update_dynamodb(shop_id, sales):
  try:

    name_prefix = os.environ['name_prefix']
    
    for sales_item in sales:
      
      # Construct recordtype by add leading zeroes if necessary
      item_no        = int(sales_item["item_no"])
      record_type    = "s-{:05d}".format(item_no)
      gross_number   = sales_item["gross_number"]
      gross_turnover = sales_item["gross_turnover"]
    
      print("Update fields based on sales: shop_id: " + shop_id + " - record_type: " + record_type + " - gross_number: " + str(gross_number) + " - gross_turnover: " + str(gross_turnover))
     
      dynamodb = boto3.client('dynamodb')
      response = dynamodb.update_item (
          TableName = name_prefix + "-shops",
          Key = {
            'shop_id': {"S":shop_id},
            'record_type' : {"S":record_type}
          },
          UpdateExpression = "set gross_number = gross_number + :gross_number, gross_turnover = gross_turnover + :gross_turnover, stock = stock - :gross_number",
          ExpressionAttributeValues = {
              ':gross_number'  : {"N":gross_number},
              ':gross_turnover': {"N":gross_turnover}
            },
          ReturnValues = "UPDATED_NEW"
        ) 
    print("Response: " + json.dumps(response))
    
    succeeded = True
    
  except ClientError as e:
    succeeded = False
    print("ERROR:" + shop_id + " - " + json.dumps(e))

  return {"succeeded": succeeded}

# Main function
# -------------
# We will not check the event, we just assume that this program is ONLY called by the decrypt function. 
# The following steps will be taken:
# - get the shop_id and the decrypted_content from the message
# - update the dynamodb table

def lambda_handler(event, context):

  print("BEGIN: event: "+json.dumps(event))

  response          = get_shop_id_and_decrypted_content(event)
  shop_id           = response["shop_id"]
  decrypted_content = response["decrypted_content"]

  print("decrypted_content: "+ json.dumps(decrypted_content))

  # Update the DynamoDB table
  response  = update_dynamodb(shop_id, decrypted_content["sales"])
  succeeded = response["succeeded"]

  print("DONE: event: " + json.dumps(event) + \
            ", shop_id: " + shop_id + \
            ", succeeded: " + json.dumps(response["succeeded"]) + \
            ", context.get_remaining_time_in_millis(): " + str(context.get_remaining_time_in_millis()) + \
            ", context.memory_limit_in_mb: " + str(context.memory_limit_in_mb))

