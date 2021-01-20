import json
import random
import time
import string
import boto3
import os

BUCKET_NAME             = os.environ['BUCKET_NAME']
BUCKET_PREFIX           = os.environ['BUCKET_PREFIX']   # without first /, with trailing /, f.e: uploads/ Leave it empty for no prefix.
TIMEOUT_IN_SECONDS      = os.environ['TIMEOUT_IN_SECONDS']

FILENAME_PREFIX         = "UploadFilename"
RANDOM_CHARACTER_LENGTH = 6

# create_filename
# ---------------
# Output filename has format: prefix/filename-YYYYmmdd_hhmmss-RaNdOm
def create_filename(bucket_prefix):
    date_time_string = time.strftime("%Y%m%d_%H%M%S")

    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(RANDOM_CHARACTER_LENGTH))

    return bucket_prefix + FILENAME_PREFIX + "-" + date_time_string + '-' + random_string

# get_presigned_url
# -----------------
def get_presigned_url(bucket_name, filename, timeout):
    s3 = boto3.client('s3')
    response = s3.generate_presigned_post(bucket_name, filename, Fields=None, Conditions=None, ExpiresIn=timeout)

    print("INFO: Response of S3 generate_presigned_post: "+json.dumps(response))

    return response

# MAIN FUNCTION
# =============
def lambda_handler(event, context):

    print("INFO: event: " + json.dumps(event))
    output_url = ""

    # make it possible for X-Ray to connect this Lambda function to the AWS resources that are called from this function
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    try:
      filename = create_filename(BUCKET_PREFIX)
      output_url = get_presigned_url(BUCKET_NAME, filename, int(TIMEOUT_IN_SECONDS))

    except Exception as e:
      print(e)
      raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "url": output_url
        }),
    }
