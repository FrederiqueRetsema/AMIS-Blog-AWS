#!/bin/bash

# stop_wait_for_custom_resource_in_CloudFormation.sh
# ==================================================
# When you made a tiny error in your Custom Resource in CloudFormation, sometimes deleting the stack takes very long. You can use this script to solve this.
# This script will search all the details that you need. You only need to specify two variables:

export REQUEST_TYPE="Create"                              # Create/Update/Delete
export RESOURCEGROUP_LIKE="CreateDeleteEndpointFunction"  # Name of the Lambda function (part is sufficient), use "lambda" for all the log groups with Lambda functions

# === When you just want to use this script, then you don't need to change anything below this line ===

LOGGROUPS=`aws logs describe-log-groups | grep $RESOURCEGROUP_LIKE | grep "logGroupName" | awk -F'"' '{print $4}'`

for log_group in $LOGGROUPS
do
   echo "Search in ${log_group}..."

   LOGSTREAMS=`aws logs describe-log-streams --log-group-name $log_group | grep logStreamName | awk -F'"' '{print $4}'`
   for log_stream in $LOGSTREAMS
   do
     echo "Search in ${log_group} > ${log_stream}..."

     aws logs get-log-events --log-group $log_group --log-stream $log_stream --query events[*].message | grep RequestType | grep $REQUEST_TYPE | while read -r line
     do

       # The AWS CLI returns json with single quotes. The result also contains json for the policy document, this is too difficult for jq to parse. 
       # awk will do the trick: field seperator is single quote, so the order is name (in i), then colun (:) in i+1 and then the value in i+2. 
       
       # The result of the command in FIELDS will be just the fields we are interested in, these will be parsed directly after this very long statement.
       
       # See for an example of the record that is parsed the blog on the AMIS technology blog.

       FIELDS=`echo $line | awk -F"'" '{for(i=1;i<NF;i++) {if ($i == "RequestId") {r=i+2;RequestId=$r}; if ($i == "ResponseURL") {r=i+2;ResponseURL=$r}; if ($i == "StackId"){r=i+2;StackId=$r};if ($i == "LogicalResourceId"){r=i+2;LogicalResourceId=$r}; if ($i == "PhysicalResourceId"){r=i+2;PhysicalResourceId=$r}}; print RequestId,ResponseURL,StackId,LogicalResourceId,PhysicalResourceId}'`

       REQUEST_ID=`echo $FIELDS | awk '{print $1}'`
       RESPONSE_URL=`echo $FIELDS | awk '{print $2}'`
       STACK_ID=`echo $FIELDS | awk '{print $3}'`
       LOGICAL_RESOURCE_ID=`echo $FIELDS | awk '{print $4}'`
       PHYSICAL_RESOURCE_ID=`echo $FIELDS | awk '{print $5}'`

       echo "TRACE LogicalResourceId = ${LOGICAL_RESOURCE_ID}"
       echo "TRACE RequestId = ${REQUEST_ID}, RESPONSE_URL = ${RESPONSE_URL}, STACK_ID = ${STACK_ID}, LOGICAL_RESOURCE_ID = ${LOGICAL_RESOURCE_ID}, PHYSICAL_RESOURCE_ID = ${PHYSICAL_RESOURCE_ID}"

       # See also: https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-lambda-resource-delete/
       curl -H 'Content-Type: ''' -X PUT -d "{                          
          \"Status\": \"SUCCESS\",                                      
          \"PhysicalResourceId\": \"${PHYSICAL_RESOURCE_ID}\",          
          \"StackId\": \"${STACK_ID}\",
          \"RequestId\": \"${REQUEST_ID}\",
          \"LogicalResourceId\": \"${LOGICAL_RESOURCE_ID}\"
       }" ${RESPONSE_URL}

     done
   done
done
