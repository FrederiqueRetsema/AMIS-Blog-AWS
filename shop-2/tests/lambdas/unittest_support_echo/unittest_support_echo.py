#####################################################################
#                                                                   #
#          DON'T START THIS LAMBDA FUNCTION VIA THE GUI !           #
#          ==============================================           #
#                                                                   #
#          The parameters you give will also be put in the          #
#          log files, and therefore be sent to the unittest_test    #
#          functions. This might lead to crashes of these unit      #
#          tests (key errors).                                      #
#                                                                   #
#          Use the unittest_test_accept/decrypt Lambda functions    #
#          instead...                                               #
#                                                                   #
#####################################################################

import json
import boto3
import os

# Main function
# -------------
def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))

  print("DEBUG: DONE: event: "+json.dumps(event))

  return 



