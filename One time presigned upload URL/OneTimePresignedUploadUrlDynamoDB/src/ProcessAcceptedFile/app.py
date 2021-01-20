import json
import boto3

def lambda_handler(event, context):
    print(json.dumps(event))

    # For future use: when you add calls to other AWS sources, this will be added to the X-Ray graph automatically.
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    for record in event["Records"]:

        bucket        = record["s3"]["bucket"]["name"]
        full_filename = record["s3"]["object"]["key"]

        # Do something with the object, f.e. print it's filename ;-)
        # You should see this message just once per (unique) uploaded filename.
        print("INFO: Bucket: " + bucket + ", full_filename: " + full_filename)

    return {
        "statusCode": 200        
    }
