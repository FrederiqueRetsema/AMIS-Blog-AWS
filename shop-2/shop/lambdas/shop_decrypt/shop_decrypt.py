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

# check_event_structure
# ---------------------
# We use the following structure:
#
# { 
#  "Records": [           <-- exactly 1 record (will not be checked by this fuction, 
#                             second and more records are ignored: SNS will not send 
#                             more than one record: see https://aws.amazon.com/sns/faqs/ 
#                             section Reliability)
#       "Sns" : {
#                  "Message" : "{
#                       ...mind that Message is a string, containing json...
#                                  "body" : "{"shop_id": "[...]", "content_base_64" : "[...]"}"
#                                             ...mind that body is a string, containing json...
#       }
#    ]
# }
#
# There are two common errors:
# 1) An operator will test a Lambda function (either accept or decrypt) with test json
#    that isn't simmulation SNS. In that case, the json will not contain the "Records" key.
# 2) The client will send data to the API that is not meant for this program, in this case
#    it doesn't contain the keys shop_id or content_base_64. 
#
# So: let's check for these two situations and accept that the function crashes in all
#     other situations.

def check_event_structure(event):

  succeeded = True

  if ('Records' in event):
       
    try:

      body = json.loads(event["Records"][0]["Sns"]["Message"])["body"]
      print("DEBUG: body: "+str(body))
                  
      if ('shop_id' in body):
                      
        if ('content_base64' in body):
                        
          print("DEBUG: Valid event structure")
                      
        else:

          print("ERROR: in check_event_structure: no content_base64 in body")
          succeeded = False

      else:

        print("ERROR: in check_event_structure: no shop_id in body")
        succeeded = False
                  
    except ClientError as e:

      print("ERROR: in check_event_structure: no valid json in body, " +str(e))
      succeeded = False
        
  else:

    print("ERROR: in check_event_structure: no element Records in event - use SNS type of json to test accept or decrypt functions")
    succeeded = False
    
  return {"succeeded": succeeded}

# get_shop_id_and_content_base64
# ------------------------------

def get_shop_id_and_content_base64(event):

  message = json.loads(event["Records"][0]["Sns"]["Message"])
  body    = json.loads(message["body"])
  
  shop_id        = body["shop_id"]
  content_base64 = bytearray(body["content_base64"], "utf-8")

  return {"shop_id": shop_id, "content_base64": content_base64}

# decrypt
# -------

def decrypt(shop_id, encrypted_content):

  try:

    kms        = boto3.client('kms')
    key_prefix = os.environ['key_prefix']
    key        = 'alias/' + key_prefix + shop_id

    response = kms.decrypt(
      CiphertextBlob      = encrypted_content,
      KeyId               = key,
      EncryptionAlgorithm = "RSAES_OAEP_SHA_256")
    print("DEBUG: Response of kms.decrypt: "+str(response))

    succeeded         = True
    decrypted_content = response["Plaintext"].decode("utf-8")

  except ClientError as e:

    print("ERROR: " + shop_id + " - " + str(encrypted_content) + " - " + str(e))

    succeeded         = False
    decrypted_content = ""

  return {"succeeded": succeeded, "decrypted_content": decrypted_content}

# send_to_to_shop_update_db
# -------------------------

def send_to_to_shop_update_db(shop_id, decrypted_content):

  try: 

    sns                   = boto3.client('sns')
    sns_process_topic_arn = os.environ['to_shop_update_db_topic_arn']

    data = { "shop_id": shop_id, "decrypted_content": decrypted_content}
    message = json.dumps(data)

    print ("INFO: Message to to_shop_update_db: " + message)

    response = sns.publish(
      TopicArn = sns_process_topic_arn,
      Message = json.dumps(data)
    )

    print("DEBUG: Response of sns.publish: "+json.dumps(response))
    succeeded = True

  except ClientError as e:

    print("ERROR: "+str(e))
    succeeded = False

  return { "succeeded": succeeded }

# Main function
# =============

def lambda_handler(event, context):

  print ("DEBUG: BEGIN: event: " + json.dumps(event))

  decrypted_content     = ""
  shop_id               = ""

  response              = check_event_structure(event)
  valid_event_structure = response["succeeded"]
  
  if (valid_event_structure):
    
    response          = get_shop_id_and_content_base64(event)
    shop_id           = response["shop_id"]
    content_base64    = response["content_base64"]
  
    encrypted_content = base64.standard_b64decode(content_base64)

    response          = decrypt(shop_id, encrypted_content)
    decrypted_content = response["decrypted_content"]

    if (response["succeeded"]):

      response = send_to_to_shop_update_db(shop_id, decrypted_content)

  print("DEBUG: DONE: shop_id: " + shop_id + \
            ", succeeded: " + str(response["succeeded"]) + \
            ", event: " + json.dumps(event) + \
            ", decrypted_content: " + json.dumps(decrypted_content))

  return

