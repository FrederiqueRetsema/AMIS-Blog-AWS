import json
import boto3
import time
import os
import uuid

PREFIX_CURRENT_FILE      = 'uploads/' 
PREFIX_DESTINATION       = 'accepted/'
TIMEOUT_IN_SECONDS       = os.environ["TIMEOUT_IN_SECONDS"]
ARN_DELETE_FILE_FUNCTION = os.environ["ARN_DELETE_FILE_FUNCTION"]
ACCOUNT_ID               = os.environ["ACCOUNT_ID"]
REGION                   = os.environ["REGION"]

# copy_file
# ---------
def copy_file(bucket, from_filename, version_id, to_filename):
    print("INFO: Copy from:" + bucket + '/' + from_filename + ' to bucket: ' + bucket + ', file: '+ to_filename)
    s3 = boto3.client('s3')
    response = s3.copy_object(
        CopySource = {
            'Bucket': bucket,
            'Key': from_filename,
            'VersionId': version_id
        },
        Bucket     = bucket,
        Key        = to_filename
    )
    print("INFO: Response of S3 copy_object: " + str(response))

# check_for_multiple_versions
# ===========================
def get_first_version_id(bucket, filename):

    s3 = boto3.client('s3')
    response = s3.list_object_versions(
        Bucket = bucket,
        Prefix = filename
    )
    print("INFO: Response of S3 list_object_versions: " + str(response))

    versions = response["Versions"]
    return_value = versions[len(versions)-1]["VersionId"]

    return return_value

# get_cron_time_for_event
# -----------------------
# Normal result for cron_time: cron(25 20 25 12 ? 2020)   
#                              which is 25 December 2020, 20:25 on whatever working day (Monday - Sunday)
def get_cron_time_for_event(number_of_seconds):

    time_after_x_seconds = time.time() + (number_of_seconds) 
    start_time_event     = time.gmtime(time_after_x_seconds)
    cron_time = "cron(" + str(start_time_event.tm_min) + " " + str(start_time_event.tm_hour) + " " + str(start_time_event.tm_mday) + " " +  str(start_time_event.tm_mon) + " ? " + str(start_time_event.tm_year)+")"

    print("INFO: cron_time: " + cron_time)

    return cron_time

# create_event_rule
# -----------------
def create_event_rule(event_rule_name, cron_time):

    events = boto3.client('events')
    response = events.put_rule(
        Name               = event_rule_name,  
        ScheduleExpression = cron_time,
        State              = 'ENABLED')
    print("INFO: Response of events put_rule: " + str(response))

    return

# create_event_target
# -------------------
def create_event_target(event_rule_name, bucket, filename, version_id, arn):

    events = boto3.client('events')
    response = events.put_targets(
        Rule    = event_rule_name,
        Targets = [{
                'Arn': arn,
                'Id' : event_rule_name,
                'Input': '{"event_rule_name": "' + event_rule_name + '", ' + \
                         ' "bucket":"' + bucket + '",' +\
                         ' "filename": "' + filename + '",' + \
                         ' "version_id": "' + version_id + '"' + \
                         '}'
            }]
    )
    print("INFO: Response of events put_targets: " + str(response))

    return

# add_delete_timer
# ================
def add_delete_timer(filename, bucket, full_filename, version_id, timeout_in_seconds):

    # Cron time is in minutes. Add 60 seconds to the timeout to prevent the timer from going off too early

    event_rule_name = "Delete-"+filename
    cron_time       = get_cron_time_for_event(timeout_in_seconds + 60)
    arn             = ARN_DELETE_FILE_FUNCTION

    try:
      create_event_rule(event_rule_name, cron_time)
      create_event_target(event_rule_name, bucket, full_filename, version_id, arn)

      print("INFO: Add of event " + event_rule_name + " succesful")      
    except Exception as e:
      print("INFO: Add of event rule or target unsuccesful, eventrule = " + event_rule_name)
      print(e)

    return

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

def remove_delete_timer(filename):

    event_rule_name = "Delete-" + filename

    try:
      remove_event_target(event_rule_name)
      remove_event_rule(event_rule_name)

      print("INFO: Remove of event target " + event_rule_name + " succesful")
      
    except Exception as e:
      print("INFO: Remove of target or rule unsuccesful, eventrule " + event_rule_name + " might not exist?")
      print(e)

    return

# Main function
# =============
def lambda_handler(event, context):

    print("INFO: event: " + json.dumps(event))

    # make it possible for X-Ray to connect this Lambda function to the AWS resources that are called from this function
    from aws_xray_sdk.core import patch
    patch(['botocore'])

    for record in event["Records"]:

        bucket        = record["s3"]["bucket"]["name"]
        from_filename = record["s3"]["object"]["key"]
        version_id    = record["s3"]["object"]["versionId"]
        filename      = from_filename[len(PREFIX_CURRENT_FILE):]
        to_filename   = PREFIX_DESTINATION + filename

        # No try/except here: when something goes wrong, the Lambda function will fail
        # this will be shown in a metric 

        first_version_id = get_first_version_id(bucket, from_filename)
        if (version_id == first_version_id):
            print("INFO: First version")

            add_delete_timer(filename, bucket, from_filename, version_id, int(TIMEOUT_IN_SECONDS))
            copy_file(bucket, from_filename, version_id, to_filename)
        else:
            print("INFO: Later uploaded version")

            try:
                remove_delete_timer(filename)
            except Exception as e:
                print(e)
                # Ignore: might be deleted because this might be the third, fourth etc file that is uploaded 

            raise Exception("Not the first version")

    return 
