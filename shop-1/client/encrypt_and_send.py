#!/usr/bin/python3
#
# encrypt_and_send.py
# -------------------
# Encrypts the contents of sales.txt in this directory, use a key that contains the id of the shop from the
# command line and send it to the URL that is also specified on the command line
#

import sys
import boto3
import requests
import json
import base64

# Constants used in this script

FILENAME           = "./sales.txt"
NUMBER_OF_REQUESTS = 1
KEY_PREFIX         = "alias/KeyL-"

# get_parameters: 
# - check if there are two parameters and stop if there are not
# - return the shop, the derived key name and the url

def get_parameters():

  if (len(sys.argv) != 3):
      print ("Add two arguments, f.e. ./encrypt_and_send.py AMIS1 https://amis.retsema.eu/shop")
      sys.exit(1)

  shop_id   = sys.argv[1]
  key_alias = KEY_PREFIX + shop_id
  url       = sys.argv[2]

  return {"shop_id": shop_id, "key_alias": key_alias, "url": url}

# encrypt_sales:
# - get sales information from the file
# - encrypt it with the key (with contains the name of the shop)

def encrypt_sales(key_alias):

  sales        = open(FILENAME, "r")
  file_content = sales.read()
  sales.close()

  kms            = boto3.client('kms')
  encrypted_file = kms.encrypt(KeyId=key_alias, Plaintext=file_content, EncryptionAlgorithm='RSAES_OAEP_SHA_256')

  # To be able to send the encrypted text in JSON format to the other side, encode it with base64 and utf-8
  #
  encrypted_content = encrypted_file["CiphertextBlob"]
  content_base64    = base64.standard_b64encode(encrypted_content).decode("utf-8")

  #
  # To check if the decrypted CiphertextBlob is the same as here, uncomment next line
  #
  #print("Encrypted content (first 20 characters) = "+str(encrypted_content[0:20]))

  return {"content_base64": content_base64}

# create_data:
# - create json with data that has to be send
# - the simplest data string contains just shop id and content_base64. It is allowed to send extra data (which will be ignored)

def create_data(shop_id, content_base64):

  data = {"shop_id": shop_id, "content_base64": content_base64}

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

response       = encrypt_sales(key_alias)
content_base64 = response["content_base64"]

response       = create_data(shop_id,content_base64)
data           = response["data"]

print ("Data           = "+json.dumps(data))

response       = send_data(url, data)
reply          = response["reply"]

print ("Status code    = "+str(reply.status_code))
print ("Content        = "+str(reply.content))
