#!/usr/bin/python3
#
# upload_with_delay.py
# ====================
# Will first get the upload url, the filename etc. and then, after a delay, upload the file to S3. 
# 

import sys
import time
import requests

# get_parameters
# --------------

def get_parameters():

  if (len(sys.argv) != 4):
      print ("Add API gateway URL, the API Key and the local filename as argument, f.e. python ./upload_with_timeout.py https://0ntricimgi.execute-api.eu-west-1.amazonaws.com/Prod/getpresignedurl 7ptnuyh526 myfile.txt")
      sys.exit(1)

  api_gateway_url = sys.argv[1]
  api_key         = sys.argv[2]
  local_filename  = sys.argv[3]

  return {"api_gateway_url": api_gateway_url, "api_key": api_key, "local_filename": local_filename}

# get_presigned_url
# -----------------

def get_presigned_url_data(url, api_key):

  headers = {'x-api-key': api_key}
  response = requests.get(url, headers = headers)

  print("Status code: "+str(response.status_code))
  print("Content: "+str(response.content))

  content = response.json()

  return content["url"]

# post_file_to_s3
# ---------------

def post_file_to_s3(filename, presigned_url, fields):

  with open(filename, 'rb') as f:
    files = {'file': (filename, f)}
    http_response = requests.post(presigned_url, data=fields, files=files)

  return http_response

# Main program:
# =============

response        = get_parameters()

api_gateway_url = response["api_gateway_url"]
api_key         = response["api_key"]
local_filename  = response["local_filename"]

print ("api_gateway_url = " + api_gateway_url)
print ("api_key         = " + api_key)
print ("local_filename  = " + local_filename)

response      = get_presigned_url_data(api_gateway_url, api_key)
presigned_url = response["url"]
fields        = response["fields"]

time.sleep(40)

response = post_file_to_s3(local_filename, presigned_url, fields)
print("Status code: "+str(response.status_code))
print("Content: "+str(response.content))
print(response)
