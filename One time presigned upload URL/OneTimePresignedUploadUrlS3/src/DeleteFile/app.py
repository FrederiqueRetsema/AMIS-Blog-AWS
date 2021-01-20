import json
import boto3

# delete_file
# -----------
def delete_file(bucket, filename, version_id):
    s3 = boto3.client('s3')
    response = s3.delete_object(
        Bucket = bucket,
        Key = filename,
        VersionId = version_id
    )
    print("INFO: Response of S3 delete_object: " + json.dumps(response))

# remove_event_target
# -------------------
def remove_event_target(event_rule_name):

    events = boto3.client('events')
    response = events.remove_targets(
        Rule=event_rule_name,
        Ids=[event_rule_name]
    )
    print("INFO: Response of events remove_targets: " + str(response))

    return

# remove_event_rule
# -----------------
def remove_event_rule(event_rule_name):

    events = boto3.client('events')
    response = events.delete_rule(
        Name = event_rule_name
    )
    print("INFO: Response of events delete_rule: " + str(response))

    return

# remove_delete_timer
# -------------------
def remove_delete_timer(event_rule_name):

    try:
      remove_event_target(event_rule_name)
      remove_event_rule(event_rule_name)

      print("INFO: Remove of event target " + event_rule_name + " succesful")
      
    except Exception as e:
      print("INFO: Remove of target or rule unsuccesful, eventrule " + event_rule_name + " might not exist?")
      print(e)
    return


def lambda_handler(event, context):
    print("INFO: event: " + json.dumps(event))

    # For future use: when you add calls to other AWS sources, this will be added to the X-Ray graph automatically.
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    event_rule_name = event["event_rule_name"]
    bucket          = event["bucket"]
    filename        = event["filename"]
    version_id      = event["version_id"]

    delete_file(bucket, filename, version_id)
    remove_delete_timer(event_rule_name)

    return {
        "statusCode": 200        
    }
