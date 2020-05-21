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

NAME_PREFIX        = os.environ["name_prefix"]
NAME               = "unittest_object_under_test_accept"
FUNCTION_NAME      = NAME_PREFIX + "_" + NAME

# search_for_elements_with_attribute_is_value_in_list
# ---------------------------------------------------
# (see also: https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search ) 

def search_for_elements_with_attribute_is_value_in_list(attribute, value, list):
    return [element for element in list if element[attribute] == value]

# get_function_configuration
# --------------------------

def get_function_configuration():
  
  lambdaclient = boto3.client("lambda")
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

def update_environment_variables(function_configuration, environment_variables):
  
  environment_new              = copy.deepcopy(function_configuration["Environment"])
  environment_new["Variables"] = environment_variables

  update_function_configuration(environment_new)

  return 

# invoke_lambda
# -------------

def invoke_lambda(test_id, event, expected_status_code, checkstring):

  lambdaclient = boto3.client('lambda')

  response     = lambdaclient.invoke(
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
    print("DEBUG: "+test_id+": Statuscode = " + str(status_code))
  else:
    print("ERROR: "+test_id+": Statuscode = " + str(status_code) + ", expected: " + str(expected_status_code))

  if ("Payload" in response):
    print("DEBUG: "+test_id+": Payload    = " + response["Payload"].read().decode('utf-8'))

  succeed = (pos_in_log_result >= 0)
  
  return { "succeeded" : succeed }
  
# get_test_id_from_body
# ---------------------
def get_test_id_from_body(body_string):

  body    = json.loads(body_string)
  message = json.loads(body["Records"][0]["Sns"]["Message"]) 
  test_id = message["test_id"]

  return { "test_id" : test_id }

# check_SNS_topic
# ---------------
# We can check what is sent to the SNS topic, because there is an echo function behind the
# SNS topic which will send all the information to cloudwatch. The logs of that echo function 
# are sent to the SQS queue cloudwatch_messages_echo by the Lambda function 
# unittest_support_send_logs_support_echo. The queue is filled by a CloudWatch log filter, 
# next to real time (in my environment: about 10 seconds between invocation of the first 
# "good" Lambda function and getting back the results)
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
        QueueUrl        = sqs_queue_url,
        WaitTimeSeconds = 5
      )
    print("DEBUG: Response of sqs.receive_message: "+json.dumps(response))     

    if ("Messages" in response):
      print("DEBUG: Found message on the queue")
      wait_for_first_message = False
      
      for sqs_message in response["Messages"]:

        response = get_test_id_from_body(sqs_message["Body"])
        test_id  = response["test_id"]

        search_result = search_for_elements_with_attribute_is_value_in_list("test_id", test_id, checklist)
        if (search_result != []):

          if (search_result[0]["will_be_sent_to_SNS"] == True):
            print("DEBUG: "+test_id+" is sent to SNS, which was expected")
            ok += 1
          else:
            print("ERROR: "+test_id+" is sent to SNS, this was not expected")
            errors+=1
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
  print("INFO: Tests that have not been sent to SNS, and were not expected to be sent to SNS (correct): "+json.dumps(non_expected_tests_left))
  for element in non_expected_tests_left:
    ok += 1
    
  return { "ok": ok, "errors": errors }


# testcase_accept_correct
# -----------------------
# Good situation: pas a JSON string and get a 200 code and OK back

def testcase_accept_correct():

  test_id              = "testcase_accept_correct"
  test_record          = { "test_id" : test_id }
  expected_status_code = 200
  check_text           = 'returnMessage: "OK"'
  will_be_sent_to_SNS  = True

  response    = invoke_lambda(test_id, test_record, expected_status_code, check_text)
  succeeded   = response["succeeded"]

  return { "succeeded": succeeded, "will_be_sent_to_SNS" : will_be_sent_to_SNS }

# testcase_accept_error
# ---------------------
# It is hard to test an error situation, as the error will come back from AWS. 
# The only way to test this, is to pass an incorrect parameter to the SNS function. 
# This is done by changing the environment variable from the 
# unittest_object_under_test_accept function and let it point to a non-existing 
# SNS topic.

def testcase_accept_error():

  response                   = get_function_configuration()
  function_configuration_org = response["function_configuration"]

  environment_variables_org                              = function_configuration_org["Environment"]["Variables"]
  environment_variables_new                              = copy.deepcopy(environment_variables_org)
  environment_variables_new["to_shop_decrypt_topic_arn"] = "non-existing-" + environment_variables_new["to_shop_decrypt_topic_arn"]

  update_environment_variables(function_configuration_org, environment_variables_new)

  # We need to wait for 5 seconds before we call the function to force AWS to use the version of the 
  # function that we updated (not the version that is still in memory, including the old content of
  # the environment variable)

  time.sleep(5)

  test_id              = "testcase_accept_error"
  test_record          = { "test_id" : test_id }
  expected_status_code = 200
  check_text           = "NotOK: retry later, admins: see cloudwatch logs for error"
  will_be_sent_to_SNS  = False

  response    = invoke_lambda(test_id, test_record, expected_status_code, check_text)
  succeeded   = response["succeeded"]
  
  update_environment_variables(function_configuration_org, environment_variables_org)

  return { "succeeded" : succeeded, "will_be_sent_to_SNS" : will_be_sent_to_SNS }

# Main function
# -------------
# Content of the event parameter will be ignored. 

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  ok        = 0
  errors    = 0
  checklist = []

  testcase_list = [testcase_accept_correct,
                   testcase_accept_error]
                   
  for testcase in testcase_list:

    response            = testcase()
    testcase_succeeded  = response["succeeded"]
    will_be_sent_to_SNS = response["will_be_sent_to_SNS"]

    if (testcase_succeeded):
      print("INFO: "+testcase.__name__+" succeeded")
      ok += 1
    else:
      print("ERROR: in testcase "+testcase.__name__)
      errors += 1

    checklist += [{ "test_id" : testcase.__name__, "will_be_sent_to_SNS" : will_be_sent_to_SNS }]

  response = check_SNS_topic(checklist)
  ok      += response["ok"]
  errors  += response["errors"]
    
  print("INFO: OK: "+str(ok)+", Errors: "+str(errors))

  print("DEBUG: DONE: event: " + json.dumps(event))

