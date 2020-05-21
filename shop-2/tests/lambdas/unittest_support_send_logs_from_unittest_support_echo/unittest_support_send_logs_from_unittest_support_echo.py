#####################################################################
#                                                                   #
#          DON'T START THIS LAMBDA FUNCTION VIA THE GUI !           #
#          ==============================================           #
#                                                                   #
#          The parameters you give will also be send to the SQS     #
#          queue, and the unittest_test_accept/decrypt will read    #
#          these messages. This might lead to crashes of these unit #
#          tests (key errors).                                      #
#                                                                   #
#          Use the unittest_test_accept/decrypt Lambda functions    #
#          instead...                                               #
#                                                                   #
#####################################################################

import json
import boto3
import os
import base64
import gzip

from botocore.exceptions import ClientError

# Main function
# =============
# Cloudwatch log lines are filtered by DEBUG: BEGIN: event: (so: any other line will not
# be send to this function)
#
# We trim the DEBUG: BEGIN: event: part from the event and send the rest (as json) to the
# SQS queue. This makes the processing on the other side of the queue easyer.

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  try:

    # Log streams are base64 encoded and gzipped. There might be multiple log messages in 
    # one event
     
    # See also:    
    # https://stackoverflow.com/questions/50295838/cloudwatch-logs-stream-to-lambda-python

    decoded_base64 = base64.b64decode(event["awslogs"]["data"])
    message_body = json.loads(gzip.decompress(decoded_base64))

    sqs           = boto3.client("sqs")
    sqs_queue_url = os.environ['sqs_queue_url']

    for log_event in message_body["logEvents"]:

      # Cut off DEBUG: BEGIN: event:, the rest of the line is the message_body to be send
      # to the other side of the SQS queue (6 = length of "event:")
      
      message_body = log_event["message"]
      pos_event    = message_body.find("event:")
      message_body = message_body[pos_event + 6:]

      print("send_message: "+json.dumps(message_body))
      response = sqs.send_message(
        QueueUrl    = sqs_queue_url,
        MessageBody = message_body
      )
      print("DEBUG: Response of sqs.send_message: "+json.dumps(response))
      
    # Succesful
      
  except ClientError as e:
    print("ERROR: "+str(e))
  
  print("DEBUG: DONE: event: " + json.dumps(event))

