#!/usr/bin/python3
#
# 100x.py
# -------

import sys
import boto3
import requests
import json
import base64
import datetime

FILENAME           = "./sales.txt"
NUMBER_OF_REQUESTS = 100
KEY_PREFIX         = "alias/KeyQ-"

# get_parameters
# --------------

def get_parameters():

  if (len(sys.argv) != 3):
      print ("Add two arguments, f.e. ./encrypt_and_send.py AMIS1 https://amis.retsema.eu/shop")
      sys.exit(1)

  shop_id   = sys.argv[1]
  key_alias = KEY_PREFIX + shop_id
  url       = sys.argv[2]

  return {"shop_id": shop_id, "key_alias": key_alias, "url": url}

# get_message_id
# --------------

def get_message_id():

  datetime_object     = datetime.datetime.now()

  year  = datetime_object.year
  month = datetime_object.month
  day   = datetime_object.day
  hour  = datetime_object.hour
  min   = datetime_object.minute
  sec   = datetime_object.second
  msec  = datetime_object.microsecond

  format_string = "{msec:06}{sec:02}{min:02}{hour:02}-{year:04}{month:02}{day:02}"
  message_id    = format_string.format(msec = msec, sec = sec, min = min, hour = hour, year = year, month = month, day = day)

  return { "message_id": message_id } 

# encrypt_sales
# -------------

def encrypt_sales(key_alias):

  sales_file   = open(FILENAME, "r")
  file_content = sales_file.read()
  sales_file.close()

  kms      = boto3.client('kms')
  response = kms.encrypt(KeyId=key_alias, Plaintext=file_content, EncryptionAlgorithm='RSAES_OAEP_SHA_256')

  encrypted_content = response["CiphertextBlob"]
  content_base64    = base64.standard_b64encode(encrypted_content).decode("utf-8")

  return {"content_base64": content_base64}

# create_data
# -----------

def create_data(shop_id, message_id, content_base64):

  data = {"shop_id": shop_id, "message_id": message_id, "content_base64": content_base64}

  return {"data": data}

# send_data
# ---------

def send_data(url, data):

  reply = requests.post(url, json.dumps(data))

  return {"reply": reply}

# Main program:
# =============

response  = get_parameters()
shop_id   = response["shop_id"]
key_alias = response["key_alias"]
url       = response["url"]

print ("Shop id        = " + shop_id)
print ("Key alias      = " + key_alias)
print ("URL            = " + url)

response       = encrypt_sales(key_alias)
content_base64 = response["content_base64"]

for request_number in range(NUMBER_OF_REQUESTS):

  response       = get_message_id()
  message_id     = response["message_id"]

  response       = create_data(shop_id, message_id, content_base64)
  data           = response["data"]

  print ("Data           = "+json.dumps(data))

  response       = send_data(url, data)
  reply          = response["reply"]

print ("Status code    = "+str(reply.status_code))
print ("Content        = "+str(reply.content))
