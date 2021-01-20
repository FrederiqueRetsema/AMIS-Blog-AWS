sam build
sam deploy
sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket fra-euwest1 --s3-prefix MemcachedNetwork
sam publish --template packaged.yaml --region eu-west-1