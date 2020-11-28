import json

# import requests


def lambda_handler(event, context):
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    # Do whatever with the boto3 library and it will connect those services with this Lambda function

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
