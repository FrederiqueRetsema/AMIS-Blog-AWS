# client

This directory simmulates a cash machine, by sending the sales (see sales.txt) to the endpoint that is given as command line parameter.
There are three scripts in this directory:

```
- encrypt_and_send.py - python3 script to encrypt the sales.txt and send it to AWS
- 100x.py             - does the same, but 100x (the same encrypted file)
- rubbish.py          - will send a json message that doesn't contain the relevant keys
```

## Usage

All scripts have the same parameters:
- The first parameter is the shop_id. The shop_id's and the usernames are the same. 
- The url where to send the message to. 

Example for shop_id AMIS1 and your domain name retsema.eu: \
`./encrypt_and_send.py AMIS1 https://amis.retsema.eu/shop`
