import sys
import boto3
import requests
import json
import base64
import os

NUMBER_OF_REQUESTS = 100

# get_parameters
# --------------

def get_parameters():

  shop_id   = os.environ["name_prefix"]+"1"
  key_alias = "alias/"+os.environ["key_prefix"]+shop_id
  url       = os.environ["url"]

  return {"shop_id": shop_id, "key_alias": key_alias, "url": url}

# encrypt_sales
# -------------

def encrypt_sales(key_alias):

  test_content   = {
   "sales": [{"item_no" : "90001", "gross_number": "5", "gross_turnover": "5"},
             {"item_no" : "90002", "gross_number": "1", "gross_turnover": "2"}]
   }

  kms      = boto3.client('kms')
  response = kms.encrypt(KeyId=key_alias, Plaintext=json.dumps(test_content), EncryptionAlgorithm='RSAES_OAEP_SHA_256')
  print("DEBUG: Response of kms.encrypt: "+str(response))

  # To be able to send the encrypted text in JSON format to the other side, encode it with base64 and utf-8
  #
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
    print ("DEBUG: request_number = "+str(request_number+1))
    reply = requests.post(url, json.dumps(data))

  return {"reply": reply}

# Main function
# =============

def lambda_handler(event, context):

  response  = get_parameters()
  shop_id   = response["shop_id"]
  key_alias = response["key_alias"]
  url       = response["url"]

  print ("DEBUG: Shop id        = " + shop_id)
  print ("DEBUG: Key alias      = " + key_alias)
  print ("DEBUG: URL            = " + url)

  response       = encrypt_sales(key_alias)
  content_base64 = response["content_base64"]

  response       = create_data(shop_id,content_base64)
  data           = response["data"]

  print ("DEBUG: Data           = "+json.dumps(data))

  response       = send_data(url, data)
  reply          = response["reply"]

  print ("INFO:  Status code    = "+str(reply.status_code))
  print ("INFO:  Content        = "+str(reply.content))

  return

