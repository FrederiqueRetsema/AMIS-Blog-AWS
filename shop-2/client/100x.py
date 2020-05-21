#!/usr/bin/python3
#
# 100x.py
# -------
# Encrypts the contents of sales.txt in this directory, use a key that contains the id of the shop from the
# command line and send it to the URL that is also specified on the command line
#

import sys
import boto3
import requests
import json
import base64

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

def create_data(shop_id, content_base64):

  data = {"shop_id": shop_id, "content_base64": content_base64}

  return {"data": data}

# send_data
# ---------

def send_data(url, data):

  for request_number in range(NUMBER_OF_REQUESTS):
    print ("request_number = "+str(request_number+1))
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

response       = create_data(shop_id,content_base64)
data           = response["data"]

print ("Data           = "+json.dumps(data))

response       = send_data(url, data)
reply          = response["reply"]

print ("Status code    = "+str(reply.status_code))
print ("Content        = "+str(reply.content))
