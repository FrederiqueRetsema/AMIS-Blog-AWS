import json
import boto3
import os
import socket
import elasticache_auto_discovery
from pymemcache.client.hash import HashClient

MEMCACHED_ENDPOINT  = os.environ['MEMCACHED_ENDPOINT']

PREFIX_CURRENT_FILE = 'uploads/' 
PREFIX_DESTINATION  = 'accepted/'

# delete_filename_from_memcached
# ------------------------------
def delete_filename_from_memcached(memcached_endpoint, full_filename):

    # See also: https://docs.aws.amazon.com/lambda/latest/dg/services-elasticache-tutorial.html

    elasticache_config_endpoint = memcached_endpoint

    nodes = elasticache_auto_discovery.discover(elasticache_config_endpoint)
    nodes = map(lambda x: (x[1], int(x[2])), nodes)

    memcache_client = HashClient(nodes)

    result = memcache_client.get(full_filename)
    print("INFO: Result from memcache_client get: " + str(result))

    if (str(result) != "None"):
      result = memcache_client.delete(full_filename)
      print("INFO: Result from memcache_client delete: " + str(result))
    else:
      raise Exception("Not the first version")
 

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
    print("INFO: Response from s3 copy_object" + str(response))

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

    print("INFO: Event: " + json.dumps(event))

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

        delete_filename_from_memcached(MEMCACHED_ENDPOINT, from_filename)
        copy_file(bucket, from_filename, to_filename)
        delete_file(bucket, from_filename)
      
    return 
