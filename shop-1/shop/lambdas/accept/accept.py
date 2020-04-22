import json
import boto3
import os

# Main function
# -------------
def lambda_handler(event, context):

  from botocore.exceptions import ClientError

  try: 

    # Log content of the data that we received from the API Gateway
    # The output is send to CloudWatch
    #

    print("BEGIN: event:"+json.dumps(event))

    # Initialize the SNS module and get the topic arn. 
    # These are placed in the environment variables of the accept function by the Terraform script
    #

    sns = boto3.client('sns')
    sns_decrypt_topic_arn = os.environ['to_decrypt_topic_arn']

    # Publish all the incomming data to the SNS topic
    #
    message = json.dumps(event)

    print ("Message to to_decrypt: " + message)

    sns.publish(
      TopicArn = sns_decrypt_topic_arn,
      Message = message
    )

    # This succeeded, so inform the client that all went well
    # (when there are errors in decrypting the message or dealing with the data, the client will NOT be informed by the status code)
    #

    statusCode = 200
    returnMessage = "OK"

  except ClientError as e:

    # Exception handling: send the error to CloudWatch
    #

    print("ERROR: "+str(e))

    # Inform the client that there is an internal server error. 
    # Mind, that the client will also get a 500 eror when there is something wrong in the API gateway. 
    # In that case, the text is "Internal server error"
    #
    # To be able to make the difference, send a specific application text back to the client
    #

    statusCode = 500
    returnMessage = "NotOK: retry later, admins: see cloudwatch logs for error"

  # To make it possible to debug faster, put anything in one line. Also show some meta data that is in the context
  # 

  print("DONE: statusCode: " + str(statusCode) + \
            ", returnMessage: \"" + returnMessage + "\"" + \
            ", event:"+json.dumps(event) + \
            ", context.get_remaining_time_in_millis(): " + str(context.get_remaining_time_in_millis()) + \
            ", context.memory_limit_in_mb: " + str(context.memory_limit_in_mb) + \
            ", context.log_group_name: " + context.log_group_name + \
            ", context.log_stream_name: "+context.log_stream_name)

  return { "statusCode": statusCode, 
           "headers" : { "Content-Type" : "application/json" },
           "body": json.dumps(returnMessage) }



