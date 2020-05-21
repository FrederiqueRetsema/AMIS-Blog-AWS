#####################################################################
#                                                                   #
#          DON'T START THIS LAMBDA FUNCTION VIA THE GUI !           #
#          ==============================================           #
#                                                                   #
#          The parameters you give will also be sent to             #
#          the to_decrypt topic. That might lead to                 #
#          unexpected errors in the decrypt function or             #
#          unexpected crashes of the unittest Lambda                #
#          functions.                                               #
#                                                                   #
#          Use the smoketest Lambda function (or encrypt_and_send   #
#          in the client directory on the VM) instead...            #
#                                                                   #
#####################################################################

import json
import boto3
import os

# Main function
# =============

def lambda_handler(event, context):

  from botocore.exceptions import ClientError

  try: 

    print("DEBUG: BEGIN: event: "+json.dumps(event))

    sns                   = boto3.client('sns')
    sns_decrypt_topic_arn = os.environ['to_shop_decrypt_topic_arn']

    message               = json.dumps(event)

    print ("INFO: Message to to_shop_decrypt: " + message)

    response = sns.publish(
      TopicArn = sns_decrypt_topic_arn,
      Message = message
    )
    print ("DEBUG: Response of sns.publish: "+json.dumps(response))

    statusCode    = 200
    returnMessage = "OK"

  except ClientError as e:

    print("ERROR: "+str(e))

    # Mind, that the client will also get a 500 eror when there is something wrong in the API gateway. 
    # In that case, the text is "Internal server error"
    #
    # To be able to make the difference, send a specific application text back to the client

    statusCode    = 500
    returnMessage = "NotOK: retry later, admins: see cloudwatch logs for error"

  print("DEBUG: DONE: statusCode: " + str(statusCode) + \
            ", returnMessage: \"" + returnMessage + "\"" + \
            ", event:"+json.dumps(event))

  return { "statusCode": statusCode, 
           "headers"   : { "Content-Type" : "application/json" },
           "body"      : json.dumps(returnMessage) }

