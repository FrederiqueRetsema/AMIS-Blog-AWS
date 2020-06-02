import json
import copy
import boto3
import os
import base64
import time

from datetime            import datetime, timedelta
from botocore.exceptions import ClientError

# search
# ------
# (see also: https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search )

def search(attribute, value, list):
    return [element for element in list if element[attribute] == value]

# int_from_string_with_optional_dot
# ---------------------------------

def int_from_string_with_optional_dot(string_with_optional_dot):

  pos_dot = string_with_optional_dot.find('.')

  if (pos_dot > 0):
    string_to_convert_to_int = string_with_optional_dot[0:pos_dot]
  else:
    string_to_convert_to_int = string_with_optional_dot

  int_value = int(string_to_convert_to_int)

  return { "int_value" : int_value }

# stats_cloudwatch
# ----------------
# I used this information to get the log entries from Cloudwatch:
# https://stackoverflow.com/questions/59240107/how-to-query-cloudwatch-logs-using-boto3-in-python

def stats_cloudwatch(name_prefix, log_group):

  logs = boto3.client('logs')

  # Get all REPORT lines, and from that, get the values of timestamp, duration, billed_duration, memory_size, max_memory_used. Sort on timestamp (to get first/last timestamp more easy)

  query = "FIELDS @timestamp, @message | "          + \
          "PARSE @message \"* *\" as type, rest | " + \
          "FILTER type = \"REPORT\" | "             + \
          "SORT @timestamp, @message | "            + \
          "PARSE @message \"REPORT RequestId: *	Duration: * ms	Billed Duration: * ms	Memory Size: * MB	Max Memory Used: *\" as request_id, duration, billed_duration, memory_size, max_memory_used |" + \
          "DISPLAY @timestamp, duration, billed_duration, memory_size, max_memory_used" 

  print("DEBUG: query = "+query)
  print("DEBUG: log_group = "+log_group)

  start_time=int((datetime.today() - timedelta(hours=2)).timestamp())   

  start_query_response = logs.start_query(
    logGroupName=log_group,
    startTime=start_time,   
    endTime=int(datetime.now().timestamp()),
    queryString=query,
  )
  print("DEBUG: Response of logs.start_query: "+json.dumps(start_query_response))

  query_id = start_query_response['queryId']
  response = None

  while ((response == None) or (response['status'] == 'Running')):
    print('DEBUG: Waiting for query to complete ...')
    time.sleep(1)

    response = logs.get_query_results(
        queryId=query_id
    )
    print("DEBUG: Response of logs.get_query_results: "+json.dumps(response))

  print("DEBUG: response after while: "+str(response))

  first_timestamp       = "n/a"
  last_timestamp        = "n/a"
  number_of_records     = 0

  min_duration          = 99999
  max_duration          = -1
  total_duration        = 0
  total_billed_duration = 0
  limit_value_duration  = int(os.environ["limit_value_duration"])
  under_limit_duration  = 0
  over_limit_duration   = 0

  min_mem               = 99999
  max_mem               = -1
  total_mem             = 0
  limit_value_diff_mem  = int(os.environ["limit_value_diff_mem"])
  under_limit_diff_mem  = 0
  over_limit_diff_mem   = 0
  current_memory_config = 0     # This is the "slider" in the Lambda function
  
  for line in response["results"]: 

    # General statistics
    # ------------------

    number_of_records += 1
    timestamp_record  = search("field", "@timestamp", line)
    timestamp         = timestamp_record[0]["value"]

    # Results of the query are ordered by timestamp

    if (first_timestamp == "n/a"):
      first_timestamp = timestamp
    else:
      last_timestamp = timestamp

    # Duration 
    # --------
    # Duration is the time it really took to execute the Lambda function

    # What we want to know, is how often AWS starts a new instance of an
    # object. We assume that when the number of milliseconds is lower than
    # the limit, this means that no new instance is started. When the number
    # of milliseconds is higher than this limit, we assume a new instance 
    # is started.

    duration_key_value_list = search("field", "duration", line)
    duration                = duration_key_value_list[0]["value"]
    response                = int_from_string_with_optional_dot(duration)
    int_duration            = response["int_value"]

    total_duration += int_duration
    
    if int_duration < min_duration:
      min_duration  = int_duration
    
    if int_duration > max_duration:
      max_duration  = int_duration
      
    if int_duration < limit_value_duration:
      under_limit_duration += 1
    else:
      over_limit_duration  += 1

    # Billed duration
    # ---------------
    # This is the duration rounded up to 100 ms. 
    
    # We are interested in the total amount of billed milliseconds, 
    # to be able to compare it to the total of used milliseconds.
      
    billed_duration_key_value_list = search("field", "billed_duration", line)
    billed_duration                = billed_duration_key_value_list[0]["value"]
    int_billed_duration            = int(billed_duration)
    
    total_billed_duration += int_billed_duration

    # Memory size
    # -----------
    # Memory size is this the memory size that we asked for,
    # it has the same value as the "slider" in the Lambda gui: 
    # this number will be the same in all the records.
    
    # We will compare the actual size that the Lambda used
    # (in "max_memory_used", which is a confusing name)
    # with this value. When these values are almost the same
    # we want to know this.

    memory_size_key_value_list = search("field", "memory_size", line)
    memory_size                = memory_size_key_value_list[0]["value"]
    int_memory_size            = int(memory_size)

    current_memory_config      = int_memory_size

    # Max memory used
    # ---------------
    # Max memory used is the amount of memory we really used.
    # We will get back something like 123 MB. Strip the MB by 
    # stripping off the space (and everything behind it). 
    
    max_memory_used_key_value_list = search("field", "max_memory_used", line)
    max_memory_used                = max_memory_used_key_value_list[0]["value"]
    pos_space                      = max_memory_used.find(' ')
    max_memory_used                = max_memory_used[0:pos_space]
    int_max_memory_used            = int(max_memory_used)

    if int_max_memory_used < min_mem:
      min_mem = int_max_memory_used
    
    if int_max_memory_used > max_mem:
      max_mem = int_max_memory_used

    total_mem = total_mem + int_max_memory_used

    # Diff_mem
    # --------
    # Diff mem is the difference between the amount of memory that is
    # currently configured (int_memory_size) and the amount of memory that
    # the Lambda function really needed (int_max_memory_used)
    
    # When the diff is higher than the limit value, this is good.
    # That means that we have some slack before the Lambda function
    # will stop working because of out-of-memory errors

    # When the diff is lower, and when this happens a lot, you
    # might want to consider to configure more memory for the 
    # lambda function that is checked.
    
    diff_mem = int_memory_size - int_max_memory_used

    if diff_mem < limit_value_diff_mem:
      under_limit_diff_mem += 1
    else:
      over_limit_diff_mem += 1

  # Send the results to CloudWatch
  # ------------------------------

  print("INFO: Log group            : " + log_group)      
  print("INFO: first_timestamp      : " + first_timestamp)
  print("INFO: last_timestamp       : " + last_timestamp)
  print("INFO: number_of_records    :"  + str(number_of_records))

  print("INFO: ")

  print("INFO: min_duration         :"  + str(min_duration))
  print("INFO: max_duration         :"  + str(max_duration))
  print("INFO: total_duration       :"  + str(total_duration))
  print("INFO: avg_duration         :"  + format(total_duration / number_of_records,".2f")) 
  print("INFO: total_billed_duration:"  + str(total_billed_duration))
  print("INFO: avg_billed_duration  :"  + format(total_billed_duration / number_of_records,".2f"))
  print("INFO: limit_value_duration :"  + str(limit_value_duration))
  print("INFO: under_limit_duration :"  + str(under_limit_duration))
  print("INFO: over_limit_duration  :"  + str(over_limit_duration))

  print("INFO: ")
  
  print("INFO: min_memory used      :"  + str(min_mem))
  print("INFO: max_memory used      :"  + str(max_mem))
  print("INFO: avg_memory used      :"  + format(total_mem / number_of_records,".2f")) 
  print("INFO: configured memory    :"  + str(current_memory_config))
  print("INFO: limit_value_diff_mem :"  + str(limit_value_diff_mem))
  print("INFO: under_limit_diff_mem :"  + str(under_limit_diff_mem))
  print("INFO: over_limit_diff_mem  :"  + str(over_limit_diff_mem))

  print("INFO: ")

  return

# Main function
# -------------
# Event is not relevant. The accept function is pretty simple. There are just two test situations:
#
# - Check the good situation:     status_code = 200, function_error = "OK" 
# - Check the an error situation

def lambda_handler(event, context):

  print("DEBUG: BEGIN: event: "+json.dumps(event))
  name_prefix = os.environ['name_prefix']

  response = stats_cloudwatch(name_prefix, "/aws/lambda/"+name_prefix+"_shop_accept")
  response = stats_cloudwatch(name_prefix, "/aws/lambda/"+name_prefix+"_shop_decrypt")
  response = stats_cloudwatch(name_prefix, "/aws/lambda/"+name_prefix+"_shop_update_db")
    
  print("DEBUG: DONE: event: " + json.dumps(event))


