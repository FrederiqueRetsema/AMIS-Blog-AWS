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
NAME          = "unittest_object_under_test_decrypt"
FUNCTION_NAME = NAME_PREFIX + "_" + NAME

# search_for_elements_with_attribute_is_value_in_list
# ---------------------------------------------------
# (see also: https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search ) 

def search_for_elements_with_attribute_is_value_in_list(attribute, test_id, checklist):
    return [element for element in checklist if element[attribute] == test_id]

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

def update_environment_variables(response, environment_variables):
  
  environment_new              = copy.deepcopy(response["Environment"])
  environment_new["Variables"] = environment_variables

  update_function_configuration(environment_new)

  return 

# invoke_lambda
# -------------

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
    print("DEBUG: " + test_id + ": Statuscode = " + str(status_code))
  else:
    print("ERROR: " + test_id + ": Statuscode = " + str(status_code)+", expected: "+str(expected_status_code))

  if ("Payload" in response):
    print("DEBUG: " + test_id + ": Payload    = " + response["Payload"].read().decode('utf-8'))

  succeed = (pos_in_log_result >= 0)
  
  return { "succeeded" : succeed }

# get_message_id
# --------------
# These are unit tests, decrypt doesn't do anything except for passing it on. So just give it a name...

def get_message_id():
  
  message_id = "unittest_decrypt"

  return { "message_id" : message_id }

# encrypt_text
# ------------

def encrypt_text(shop_id, text):
  
  key_prefix = os.environ['key_prefix']
  key_alias  = 'alias/' + key_prefix + shop_id

  kms      = boto3.client('kms')
  response = kms.encrypt(
     KeyId=key_alias, 
     Plaintext=text, 
     EncryptionAlgorithm='RSAES_OAEP_SHA_256'
  )
  print("DEBUG: Response of kms.encrypt: "+str(response))

  encrypted_content = response["CiphertextBlob"]
  content_base64    = base64.standard_b64encode(encrypted_content).decode("utf-8")

  return { "content_base64" : content_base64 }
  
# get_valid_sns_event
# -------------------
# I used the text from a previous message (sent via shop-2/client/encrypt_and_send.py) and use it in this testset. This 
# shouldn't be a problem because none of the parameters is checked.

def get_valid_sns_event(shop_id, message_id, content_base64):
  event = {
      "Records": [ 
         { 
             "EventSource": "aws:sns", 
             "EventVersion": "1.0", 
             "EventSubscriptionArn": "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_decrypt:d5edbb87-2ca6-4942-8977-056f07f5061d", 
             "Sns": { 
                 "Type": "Notification",
                 "MessageId": "1965b2a8-6dfe-5de8-ab45-e58b19b63b4e", 
                 "TopicArn": "arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_decrypt",
                 "Subject": "null",
                 "Message": "{\"resource\": \"/shop\", \"path\": \"/shop\", \"httpMethod\": \"POST\", \"headers\": {\"Accept\": \"*/*\", \"Accept-Encoding\": \"gzip, deflate\", \"Host\": \"o9330wv5vl.execute-api.eu-west-1.amazonaws.com\", \"User-Agent\": \"python-requests/2.23.0\", \"X-Amzn-Trace-Id\": \"Root=1-5ea97206-e83cbcdbcf616c8681882743\", \"X-Forwarded-For\": \"86.88.108.53\", \"X-Forwarded-Port\": \"443\", \"X-Forwarded-Proto\": \"https\"}, \"multiValueHeaders\": {\"Accept\": [\"*/*\"], \"Accept-Encoding\": [\"gzip, deflate\"], \"Host\": [\"o9330wv5vl.execute-api.eu-west-1.amazonaws.com\"], \"User-Agent\": [\"python-requests/2.23.0\"], \"X-Amzn-Trace-Id\": [\"Root=1-5ea97206-e83cbcdbcf616c8681882743\"], \"X-Forwarded-For\": [\"86.88.108.53\"], \"X-Forwarded-Port\": [\"443\"], \"X-Forwarded-Proto\": [\"https\"]}, \"queryStringParameters\": null, \"multiValueQueryStringParameters\": null, \"pathParameters\": null, \"stageVariables\": null, \"requestContext\": {\"resourceId\": \"84sjgf\", \"resourcePath\": \"/shop\", \"httpMethod\": \"POST\", \"extendedRequestId\": \"Lv7BEHlojoEFV0Q=\", \"requestTime\": \"29/Apr/2020:12:24:38 +0000\", \"path\": \"/prod/shop\", \"accountId\": \"300577164517\", \"protocol\": \"HTTP/1.1\", \"stage\": \"prod\", \"domainPrefix\": \"o9330wv5vl\", \"requestTimeEpoch\": 1588163078706, \"requestId\": \"cf7540c5-afba-49d8-b133-317a6884711e\", \"identity\": {\"cognitoIdentityPoolId\": null, \"accountId\": null, \"cognitoIdentityId\": null, \"caller\": null, \"sourceIp\": \"86.88.108.53\", \"principalOrgId\": null, \"accessKey\": null, \"cognitoAuthenticationType\": null, \"cognitoAuthenticationProvider\": null, \"userArn\": null, \"userAgent\": \"python-requests/2.23.0\", \"user\": null}, \"domainName\": \"o9330wv5vl.execute-api.eu-west-1.amazonaws.com\", \"apiId\": \"o9330wv5vl\"}, \"body\": \"{\\\"shop_id\\\": \\\"" + shop_id + "\\\", \\\"message_id\\\": \\\"" + message_id + "\\\", \\\"content_base64\\\": \\\"" + content_base64 + "\\\"}\", \"isBase64Encoded\": false}",
                 "Timestamp": "2020-04-29T12:24:40.008Z",
                 "SignatureVersion": "1", 
                 "Signature": "Ud4xxGJN2ahESHUC7oP0+fSWvzblay5QzJp5SXpuUOjwRaw3qiy+RvTHLqK5I0kO0OjgO75Z1rCZM1eSHFxGJecYnvClNgm/7mgIm3SuZQf3saOMJs/9zbIudF+gxhw7hd/0FghEdEt77GgE+VerSMSJczBUcyVVJcXx+OCn72QcWjHmdacb7CA1FpGKZsUnCjtcZudvX8cKaJiOty1JRI609tvp0HB3M7HDA7hj60wZBVNa8vnAf/jZZ+nhPBLZmkzR9gOvYAuFTIHn+cd1ymIw3jlOIwZAQNOftnuVitBWQNkarKes4AFMqPZ22I9unmBBSOf5wKlk267itfjdMQ==",
                 "SigningCertUrl": "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem", 
                 "UnsubscribeUrl": "https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-1:300577164517:AMIS_to_shop_decrypt:d5edbb87-2ca6-4942-8977-056f07f5061d",
                 "MessageAttributes": {}
             }
          } 
       ] 
     }

  return { "event" : event }

# get_test_id_from_body
# ---------------------

def get_test_id_from_body(body_string): 

  body              = json.loads(body_string)
  message           = json.loads(body["Records"][0]["Sns"]["Message"]) 
  decrypted_content = json.loads(message["decrypted_content"])
  test_id           = decrypted_content["test_id"]

  return { "test_id" : test_id }

# check_SNS_topic
# ---------------
# We can check what is sent to the SNS topic, because there is an echo function behind
# the SNS topic which will send all the information to CloudWatch. The logs of that 
# echo function are sent to the SQS queue cloudwatch_messages_echo by the Lambda function 
# unittest_support_send_logs_support_echo. The queue is filled by a CloudWatch log filter,
# next to real time (in my environment: about 10 seconds between invocation of the first
# "good" Lambda function and getting back the results).
#
# We'll wait for 3 x 5 seconds after the last message was comming (this is still 
# less than the 4 minutes we had to wait for the non-next-to-realtime CloudWatch 
# query to finish). When there are no results at all, this unittest_test function will be
# aborted by AWS when the timeout time is reached.

def check_SNS_topic(checklist):

  sqs                       = boto3.client("sqs")
  sqs_queue_url             = os.environ['sqs_queue_url']

  wait_for_first_message    = True
  max_reads_after_first_msg = 3

  no_reads_after_first_msg  = 0
  ok                        = 0
  errors                    = 0
  
  while ((wait_for_first_message) or (no_reads_after_first_msg < max_reads_after_first_msg)):

    response = sqs.receive_message(
        QueueUrl            = sqs_queue_url,
        WaitTimeSeconds     = 5,
        MaxNumberOfMessages = 10
      )
    print("DEBUG: Response of sqs.receive_message: "+json.dumps(response))     

    if ("Messages" in response):
      print("DEBUG: Found message(s) on the queue")
      wait_for_first_message = False
      
      for sqs_message in response["Messages"]:

        response = get_test_id_from_body(sqs_message["Body"])
        test_id  = response["test_id"]

        search_result = search_for_elements_with_attribute_is_value_in_list("test_id", test_id, checklist)
        if (search_result != []):

          if search_result[0]["will_be_sent_to_SNS"]:
            print("DEBUG: "+test_id+" is sent to SNS, which was expected")
            ok += 1
          else:
            print("ERROR: "+test_id+" is sent to SNS, this was not expected")
            errors += 1

          checklist.remove(search_result[0])

        response = sqs.delete_message(
          QueueUrl      = sqs_queue_url,
          ReceiptHandle = sqs_message["ReceiptHandle"]
          )
        print("DEBUG: Response of sqs.delete_message: "+json.dumps(response))
    else:
      print("DEBUG: No messages on the queue")
      if (wait_for_first_message == False):
        no_reads_after_first_msg += 1
    
  expected_tests_left = search_for_elements_with_attribute_is_value_in_list("will_be_sent_to_SNS", True, checklist)
  print("INFO: Tests that have not been sent to SNS, but were expected to be sent (these are errors): "+json.dumps(expected_tests_left))
  for element in expected_tests_left:
    errors += 1

  non_expected_tests_left = search_for_elements_with_attribute_is_value_in_list("will_be_sent_to_SNS", False, checklist)
  print("INFO: Tests that have not been in the logs, and we didn't expect them to show up (correct): "+json.dumps(non_expected_tests_left))
  for element in non_expected_tests_left:
    ok += 1
    
  return { "ok": ok, "errors": errors }

# testcase_decrypt_correct_AMIS1
# ------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# and get a 200 code and OK back
#
# The checklist is used to check the cloudwatch results of the lambda function that is 
# behind the SNS function. When we expect this testcase to be send to that Lambda 
# function, set expected to True, otherwise set it to False.

def testcase_decrypt_correct_AMIS1():

  test_id              = "testcase_decrypt_correct_AMIS1"
  shop_id              = "AMIS1"
  expected_status_code = 200
  check_text           = "succeeded: True"
  will_be_sent_to_SNS  = True

  to_be_encrypted      = json.dumps({"test_id" : test_id })
  response             = encrypt_text(shop_id, to_be_encrypted)
  content_base64       = response["content_base64"]

  response             = get_message_id()
  message_id           = response["message_id"]
  
  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]

  return { "succeeded": succeeded, "will_be_sent_to_SNS" : will_be_sent_to_SNS }

# testcase_decrypt_correct_AMIS2
# ------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# and get a 200 code and OK back

def testcase_decrypt_correct_AMIS2():

  test_id              = "testcase_decrypt_correct_AMIS2"
  shop_id              = "AMIS2"
  expected_status_code = 200
  check_text           = "succeeded: True"
  will_be_sent_to_SNS  = True
  
  to_be_encrypted      = json.dumps({"test_id" : test_id })
  response             = encrypt_text(shop_id, to_be_encrypted)
  content_base64       = response["content_base64"]

  response             = get_message_id()
  message_id           = response["message_id"]
  
  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]

  return { "succeeded": succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_correct_message_id_in_is_message_id_out
# --------------------------------------------------------
# Good situation: pass an event that looks like the events the function normally gets
# and get a 200 code and OK back

def testcase_decrypt_correct_message_id_in_is_message_id_out():

  test_id              = "testcase_decrypt_correct_message_id_in_is_message_id_out"
  shop_id              = "AMIS2"
  expected_status_code = 200
  will_be_sent_to_SNS  = True
  
  to_be_encrypted      = json.dumps({"test_id" : test_id })
  response             = encrypt_text(shop_id, to_be_encrypted)
  content_base64       = response["content_base64"]

  message_id           = test_id
  check_text           = message_id
  
  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]

  return { "succeeded": succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_no_Records_in_event
# ------------------------------------------
# Send an event without "Records" in the event. This may happen when someone uses the
# Test button on the Lambda GUI screen to test the function, instead of using an SNS
# formatted test event. 

def testcase_decrypt_error_no_Records_in_event():
  
  test_id              = "testcase_decrypt_error_no_Records_in_event"
  expected_status_code = 200
  check_text           = "ERROR: in check_event_structure: no element Records in event - use SNS type of json to test accept or decrypt functions"
  will_be_sent_to_SNS  = False

  event                = {"test_id": test_id}

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_no_Records_0_Sns_Message_Body_in_event
# -------------------------------------------------------------

def testcase_decrypt_error_no_Records_0_Sns_Message_body_in_event():
  
  test_id              = "testcase_decrypt_error_no_Records_0_Sns_Message_body_in_event"
  expected_status_code = 200
  check_text           = "KeyError"
  will_be_sent_to_SNS  = False

  event                = {"Records": [{"test_id" : test_id}]}

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_no_shop_id_in_body
# -----------------------------------------

def testcase_decrypt_error_no_shop_id_in_body():
  
  test_id              = "testcase_decrypt_error_no_shop_id_in_body"
  expected_status_code = 200
  check_text           = "ERROR: in check_event_structure: no shop_id in body"
  will_be_sent_to_SNS  = False

  event                = {"Records": [{"Sns" : {"Message": json.dumps({"body": {"no_shop_id":"True", "message_id": "present", "content_base64" : "present"}})}}]}

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_no_message_id_in_body
# -------------------------------------------

def testcase_decrypt_error_no_message_id_in_body():
  
  test_id              = "testcase_decrypt_error_no_message_id_in_body"
  expected_status_code = 200
  check_text           = "ERROR: in check_event_structure: no message_id in body"
  will_be_sent_to_SNS  = False

  event                = {"Records": [{"Sns" : {"Message": json.dumps({"body": {"shop_id":"AMIS1", "no_message_id": "True", "no_content_base64" : "True"}})}}]}

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_no_content64_in_body
# -------------------------------------------

def testcase_decrypt_error_no_content_base64_in_body():
  
  test_id              = "testcase_decrypt_error_no_shop_id_in_body"
  expected_status_code = 200
  check_text           = "ERROR: in check_event_structure: no content_base64 in body"
  will_be_sent_to_SNS  = False

  event                = {"Records": [{"Sns" : {"Message": json.dumps({"body": {"shop_id":"AMIS1", "message_id": "present", "no_content_base64" : "True"}})}}]}

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_bogus_in_content_base64
# ----------------------------------------------

def testcase_decrypt_error_bogus_in_content_base64():
  
  test_id              = "testcase_decrypt_error_bogus_in_content_base64"
  shop_id              = "AMIS1"
  expected_status_code = 200
  check_text           = "Error: Invalid base64-encoded string:"
  will_be_sent_to_SNS  = False

  content_base64       = "bogus"

  response             = get_message_id()
  message_id           = response["message_id"]

  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_base64_bogus_in_content_base64
# -----------------------------------------------------

def testcase_decrypt_error_base64_bogus_in_content_base64():
  
  test_id              = "testcase_decrypt_error_base64_bogus_in_content_base64"
  shop_id              = "AMIS1"
  expected_status_code = 200
  check_text           = "An error occurred (InvalidCiphertextException) when calling the Decrypt operation"
  will_be_sent_to_SNS  = False

  content_base64       = base64.standard_b64encode(b"bogus").decode("utf-8")

  response             = get_message_id()
  message_id           = response["message_id"]

  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_bogus_in_shop_id
# ---------------------------------
# Send a correct json event to the Lambda function, an existing key is used to
# encrypt the message, but in the shop_id is bogus (leading to a non existent
# key in the decrypt function)

def testcase_decrypt_error_bogus_in_shop_id():
  
  test_id              = "testcase_decrypt_error_bogus_in_shop_id"
  shop_id              = "AMIS1"
  expected_status_code = 200
  check_text           = "An error occurred (NotFoundException) when calling the Decrypt operation"
  will_be_sent_to_SNS  = False

  to_be_encrypted      = json.dumps({"test_id" : test_id })
  response             = encrypt_text(shop_id, to_be_encrypted)
  content_base64       = response["content_base64"]

  response             = get_message_id()
  message_id           = response["message_id"]
  
  shop_id              = "bogus"
  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_key_swap
# -------------------------------
# Send a correct json event to the Lambda function, a correct key is used, but
# it is a different key than is expected based on the shop_id in the message

def testcase_decrypt_error_key_swap():
  
  test_id              = "testcase_decrypt_error_key_swap"
  shop_id              = "AMIS1"
  expected_status_code = 200
  check_text           = "An error occurred (InvalidCiphertextException) when calling the Decrypt operation"
  will_be_sent_to_SNS  = False

  to_be_encrypted      = json.dumps({"test_id" : test_id })
  response             = encrypt_text(shop_id, to_be_encrypted)
  content_base64       = response["content_base64"]

  response             = get_message_id()
  message_id           = response["message_id"]
  
  shop_id              = "AMIS2"
  response             = get_valid_sns_event(shop_id, message_id, content_base64)
  event                = response["event"]

  response             = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded            = response["succeeded"]
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# testcase_decrypt_error_incorrect_SNS_topic
# ------------------------------------------

def testcase_decrypt_error_incorrect_SNS_topic():

  test_id                    = "testcase_decrypt_error_incorrect_SNS_topic"
  shop_id                    = "AMIS1"
  expected_status_code       = 200
  check_text                 = "An error occurred (InvalidParameter) when calling the Publish operation"
  will_be_sent_to_SNS        = False

  to_be_encrypted            = json.dumps({"test_id" : test_id })
  response                   = encrypt_text(shop_id, to_be_encrypted)
  content_base64             = response["content_base64"]

  response                   = get_message_id()
  message_id                 = response["message_id"]
  
  response                   = get_valid_sns_event(shop_id, message_id, content_base64)
  event                      = response["event"]

  response                                                 = get_function_configuration()
  function_configuration_org                               = response["function_configuration"]
  environment_variables_org                                = function_configuration_org["Environment"]["Variables"]

  environment_variables_new                                = copy.deepcopy(environment_variables_org)
  environment_variables_new["to_shop_update_db_topic_arn"] = "non-existing-"+environment_variables_new["to_shop_update_db_topic_arn"]
  update_environment_variables(function_configuration_org, environment_variables_new)

  # We need to wait for 5 seconds before we call the function to force AWS to use the version of the 
  # function that we updated (not the version that is still in memory, including the old content of
  # the environment variable)

  time.sleep(5)

  response                   = invoke_lambda(test_id, event, expected_status_code, check_text)
  succeeded                  = response["succeeded"]

  update_environment_variables(function_configuration_org, environment_variables_org)
  
  return { "succeeded" : succeeded, "will_be_sent_to_SNS": will_be_sent_to_SNS }

# Main function
# -------------
# Content of the event parameter will be ignored.

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  ok        = 0
  errors    = 0
  checklist = []

  testcase_list = [testcase_decrypt_correct_AMIS1,
                   testcase_decrypt_correct_AMIS2,
                   testcase_decrypt_correct_message_id_in_is_message_id_out,
                   testcase_decrypt_error_no_Records_in_event,
                   testcase_decrypt_error_no_Records_0_Sns_Message_body_in_event,
                   testcase_decrypt_error_no_shop_id_in_body,
                   testcase_decrypt_error_no_message_id_in_body,
                   testcase_decrypt_error_no_content_base64_in_body,
                   testcase_decrypt_error_bogus_in_content_base64,
                   testcase_decrypt_error_base64_bogus_in_content_base64,
                   testcase_decrypt_error_bogus_in_shop_id,
                   testcase_decrypt_error_key_swap,
                   testcase_decrypt_error_incorrect_SNS_topic
                  ]

  for testcase in testcase_list:

    response            = testcase()
    process_testcase    = response["succeeded"]
    will_be_sent_to_SNS = response["will_be_sent_to_SNS"]

    if (process_testcase):
      print("INFO: " + testcase.__name__ + " succeeded")
      ok += 1
    else:
      print("ERROR: in " + testcase.__name__)
      errors += 1
      
    checklist += [{ "test_id": testcase.__name__, "will_be_sent_to_SNS": will_be_sent_to_SNS }]
  
  response = check_SNS_topic(checklist)
  ok      += response["ok"]
  errors  += response["errors"]
    
  print("INFO: OK: "+str(ok)+", Errors: "+str(errors))

  print("DEBUG: DONE: event: " + json.dumps(event))

