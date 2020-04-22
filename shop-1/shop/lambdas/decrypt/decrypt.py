import json
import boto3
import os
import base64

from botocore.exceptions import ClientError

# check_event_structure
# ---------------------
# This function processes input from SNS. We use a limited amount of data from that, but
# we do expect the event data to have a certain structure. When, for example, a simple
# test is done from within the Lambda gui, then the function will fail with a key error.
# We want a more gracefull way of dealing with this error.
# 
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
# We could check all of that, but this will lead to a nested if with about 7 checks (which
# makes the code not readable).
#
# When we wouldn't check, then the program will abort with an error and the function will
# crash.
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

  # Base assumption: correct event structure.
  succeeded = True

  # Check for Records (common error #1, see above):
  if ('Records' in event):
       
    # Skip a lot of checks, and continue with checking the body
    # when the function crashes on the json.loads(..), then you most probably tried to test
    # a function from the GUI and didn't use an SNS json template to help you.
    #
    try:
      body = json.loads(event["Records"][0]["Sns"]["Message"])["body"]
      print("body: "+str(body))
                  
      # Check if the element "shop_id" is present in the "body":
      if ('shop_id' in body):
                      
        # Check if the element "content_base64" is present in the "body":
        if ('content_base64' in body):
                        
          # Great: this is a valid message. Don't do anything
          print("Valid event structure")
                      
        else:
          print("ERROR in event structure: no content_base_64 in body")
          succeeded = False

      else:
        print("ERROR in event structure: no shop_id in body")
        succeeded = False
                  
    except ClientError as e:
      print("ERROR in event structure: no valid json in body, " +str(e))
      succeeded = False
        
  else:
    print("ERROR in event structure: no element Records in event - use SNS type of json to test accept or decrypt functions")
    succeeded = False
    
  return {"succeeded": succeeded}

# get_shop_id_and_content_base64(event)
# ----------------------------------
# This function extracts the fields that we are interested in: shop_id and content_base64. 
# All other fields are ignored.
#

def get_shop_id_and_content_base64(event):

  message = json.loads(event["Records"][0]["Sns"]["Message"])
  body = json.loads(message["body"])
  
  shop_id = body["shop_id"]
  content_base64 = bytearray(body["content_base64"], "utf-8")

  return {"shop_id": shop_id, "content_base64": content_base64}

# decrypt
# -------
# Decrypt the message, using a key that contains the shop_id. The prefix comes from the environment variable key_prefix, which is filled
# by Terraform. Please read ../vagrant/faq.pdf what to do when you want to change the prefix of the key.

def decrypt(shop_id, encrypted_content):
  try:
    kms        = boto3.client('kms')
    key_prefix = os.environ['key_prefix']
    key        = 'alias/' + key_prefix + shop_id

    response = kms.decrypt(
      CiphertextBlob = encrypted_content,
      KeyId = key,
      EncryptionAlgorithm="RSAES_OAEP_SHA_256")

    decrypted_content = response["Plaintext"].decode("utf-8")

    succeeded = True

  except ClientError as e:
    print("ERROR:" + shop_id + " - " + str(encrypted_content) + " - " + str(e))

    succeeded = False
    decrypted_content = ""

  return {"succeeded": succeeded, "decrypted_content": decrypted_content}

# send_to_to_process_sns_topic
# ----------------------------
# Send the decrypted content to the to_process SNS topic.
# The AWS Resource Number (ARN) is in the environment variables (this is set by Terraform).

def send_to_to_process_sns_topic(shop_id, decrypted_content):

  try: 

    # Initialize the SNS module and get the topic arn. 
    # These are placed in the environment variables of the accept function by the Terraform script
    #

    sns = boto3.client('sns')
    sns_process_topic_arn = os.environ['to_process_topic_arn']

    # Publish the shop id and the decrypted content to the SNS topic
    #
    data = { "shop_id": shop_id, "decrypted_content": decrypted_content}
    message = json.dumps(data)

    print ("Message to to_process: " + message)

    sns.publish(
      TopicArn = sns_process_topic_arn,
      Message = json.dumps(data)
    )

    succeeded = True

  except ClientError as e:

    # Exception handling: send the error to CloudWatch
    #

    print("ERROR: "+str(e))

    succeeded = False

  return { "succeeded": succeeded }

# Main function
# -------------
# Check if the event is valid 
# If so,
# - get the elements
# - decrypt the contents
# - send it to the to_process SNS topic

def lambda_handler(event, context):

  print ("BEGIN: event: " + json.dumps(event))

  # Initialize decrypted_content and shop_id. We need to do this, because these variables are set within
  # an if block and (also) used outside that if block

  decrypted_content = ""
  shop_id           = ""

  # There is a lot of information in the event parameter, but we are only interested in the shop id and content_base64 values
  # (Other lambda functions that are connected to the same SNS topic might use more parameters)
  #
  # Check that the elements that we DO need, are there
  #
  response          = check_event_structure(event)
  succeeded         = response["succeeded"]
  
  if (succeeded):
    
    # Get the shop id and the encrypted data from the event data
    #
    
    response          = get_shop_id_and_content_base64(event)
    shop_id           = response["shop_id"]
    content_base64    = response["content_base64"]
  
    # We needed to base64 encode the content, to make it possible to send it via json to the cloud environment

    encrypted_content = base64.standard_b64decode(content_base64)

    # Decrypt the content, using the shop id as part of the key name
    #
    response          = decrypt(shop_id, encrypted_content)
    decrypted_content = response["decrypted_content"]

    # When this succeeded, send the content to the SNS topic to process the data.
    #
    if (response["succeeded"]):

      response = send_to_to_process_sns_topic(shop_id, decrypted_content)

  print("DONE: shop_id: " + shop_id + \
            ", succeeded: " + str(response["succeeded"]) + \
            ", event: " + json.dumps(event) + \
            ", decrypted_content: " + json.dumps(decrypted_content) + \
            ", context.get_remaining_time_in_millis(): " + str(context.get_remaining_time_in_millis()) + \
            ", context.memory_limit_in_mb: " + str(context.memory_limit_in_mb))

  # This is a function which is placed after an SNS topic. It doesn't make sense to return content
  #
  return


