import json
import boto3
import os

DYNAMODB_TABLE      = os.environ['DYNAMODB_TABLE']

PREFIX_CURRENT_FILE = 'uploads/' 
PREFIX_DESTINATION  = 'accepted/'

# delete_filename_from_dynamodb_table
# -----------------------------------
def delete_filename_from_dynamodb_table(dynamodb_table, full_filename):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.delete_item(
        TableName = dynamodb_table,
        Key = {'FullFilename': {
            'S': full_filename
           },
        },
        ConditionExpression = 'attribute_exists(FullFilename)'
    )
    print("INFO: Response from DynamoDB delete_item: " + json.dumps(response))

# copy_file
# ---------
def copy_file(bucket, from_filename, to_filename):
    print("INFO: Copy from:" + bucket + '/' + from_filename + ' to bucket: ' + bucket + ', file: '+ to_filename)

    s3 = boto3.client('s3')
    response = s3.copy_object(
        CopySource = {
            'Bucket': bucket,
            'Key': from_filename
        },
        Bucket     = bucket,
        Key        = to_filename
    )
    print("INFO: Response from S3 copy_object: " + str(response))

# delete_file
# -----------
def delete_file(bucket, filename):
    s3 = boto3.client('s3')
    response = s3.delete_object(
        Bucket = bucket,
        Key = filename
    )
    print("INFO: Response from S3 delete_object: " + json.dumps(response))

# Main function
# =============
def lambda_handler(event, context):

    print("INFO: Content of event: " + json.dumps(event))

    # make it possible for X-Ray to connect this Lambda function to the AWS resources that are called from this function
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    for record in event["Records"]:

        bucket        = record["s3"]["bucket"]["name"]
        from_filename = record["s3"]["object"]["key"]
        filename      = from_filename[len(PREFIX_CURRENT_FILE):]
        to_filename   = PREFIX_DESTINATION + filename

        # No try/except here: when something goes wrong, the Lambda function will fail
        # this will be shown in a metric 

        delete_filename_from_dynamodb_table(DYNAMODB_TABLE, from_filename)
        copy_file(bucket, from_filename, to_filename)
        delete_file(bucket, from_filename)
      
    return 
