#!/usr/bin/python3
#
# rubish.py
# ---------
# Send rubish to the URL that specified on the command line

import sys
import boto3
import requests
import json
import base64

# Constants used in this script

NUMBER_OF_REQUESTS = 1

# get_parameters 
# --------------

def get_parameters():

  if (len(sys.argv) != 3):
      print ("Add two arguments, f.e. ./rubish.py AMIS1 https://amis1.retsema.eu/shop")
      sys.exit(1)

  shop_id   = sys.argv[1]
  url       = sys.argv[2]

  return {"shop_id": shop_id, "url": url}

# create_data
# -----------

def create_data():

  data = {"nothing": "", "anything": "This is rubish, created by client/rubish.sh"}

  return {"data": data}

# send_data
# ---------

def send_data(url, data):

  for request_number in range(NUMBER_OF_REQUESTS):
    print ("request_number = "+str(request_number+1))
    reply = requests.post(url, json.dumps(data))

  return {"reply": reply}

# Main program
# ============

response  = get_parameters()
shop_id   = response["shop_id"]
url       = response["url"]

print ("Shop id        = " + shop_id)
print ("URL            = " + url)

response       = create_data()
data           = response["data"]

print ("Data           = "+json.dumps(data))

response       = send_data(url, data)
reply          = response["reply"]

print ("Status code    = "+str(reply.status_code))
print ("Content        = "+str(reply.content))
