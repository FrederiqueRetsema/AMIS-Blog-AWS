#!/usr/bin/python3
#
# rubish.py
# ---------
# Send rubish to the URL that specified on the command line
#

import sys
import boto3
import requests
import json
import base64

# Constants used in this script

NUMBER_OF_REQUESTS = 1

# get_parameters: 
# - check if there are two parameters and stop if there are not
# - return the shop, the derived key name and the url

def get_parameters():

  if (len(sys.argv) != 3):
      print ("Add two arguments, f.e. ./rubish.py AMIS1 https://amis.retsema.eu/shop")
      sys.exit(1)

  shop_id   = sys.argv[1]
  key_alias = KEY_PREFIX + shop_id
  url       = sys.argv[2]

  return {"shop_id": shop_id, "key_alias": key_alias, "url": url}

# create_data:
# - create json with rubish data that has to be send

def create_data():

  data = {"nothing": "", "anything": "This is rubish, created by client/rubish.sh"}

  return {"data": data}

# send_data:
# - send it x times to the url

def send_data(url, data):

  for request_number in range(NUMBER_OF_REQUESTS):
    print ("request_number = "+str(request_number+1))
    reply = requests.post(url, json.dumps(data))

  return {"reply": reply}

# Main program:
# - get parameters
# - encrypt the file with sales
# - create data
# - send the data

response = get_parameters()
shop_id  = response["shop_id"]
key_alias = response["key_alias"]
url       = response["url"]

print ("Shop id        = " + shop_id)
print ("Key alias      = " + key_alias)
print ("URL            = " + url)

response       = create_data()
data           = response["data"]

print ("Data           = "+json.dumps(data))

response       = send_data(url, data)
reply          = response["reply"]

print ("Status code    = "+str(reply.status_code))
print ("Content        = "+str(reply.content))
