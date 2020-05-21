# AMIS-Blog-AWS/shop-2/client

The scripts in this directory simmulate a cash machine, by sending the sales (see sales.txt) to the endpoint that is given as command line parameter.
There are three scripts in this directory:

```
- encrypt_and_send.py - python3 script to encrypt the sales.txt and send it to AWS
- 100x.py             - does the same, but 100 times (the same information)
- rubbish.py          - will send a json message that doesn't contain the relevant keys
```

## Usage

All scripts have the same parameters:
- The first parameter is the shop_id. You can use both AMIS1 and AMIS2.
- The second parameter is the url where to send the message to. 

Example for shop_id AMIS1 and let's assume that your domain name is retsema.eu: \
`./encrypt_and_send.py AMIS1 https://amis1.retsema.eu/shop`
