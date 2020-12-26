#!/bin/bash

# CLI Parameters
arg_tag=$1

[ -n "${AWS_DEFAULT_REGION}" ] || { echo "AWS_DEFAULT_REGION environment variable not defined"; exit 1; }
[ -n "${WORLOAD_STATEFILE_BUCKET_NAME}" ] || { echo "WORLOAD_STATEFILE_BUCKET_NAME environment variable not defined"; exit 1; }

# Create Terraform Plan
cd ./src
terraform init \
-backend-config="region=${AWS_DEFAULT_REGION}" \
-backend-config="bucket=${WORLOAD_STATEFILE_BUCKET_NAME}"

terraform plan -var "region=${AWS_DEFAULT_REGION}" -out="plan.out"

# Check for compliance
cd ../
if [[ $arg_tag != "" ]]
then
  echo "Compliance check requested for tag $arg_tag"
  terraform-compliance -f security-and-compliance-code/src/ -p ./src/plan.out --cucumber-json=./reports/test.json --tags $arg_tag
  terraform-compliance -f security-and-compliance-code/src/ -p ./src/plan.out --bdd-xml=./reports/test.xml --tags $arg_tag
else
  echo "Compliance check requested for all tags"
  terraform-compliance -f security-and-compliance-code/src/ -p ./src/plan.out --cucumber-json=./reports/test.json
  terraform-compliance -f security-and-compliance-code/src/ -p ./src/plan.out --bdd-xml=./reports/test.xml
fi

# Handle reponse
var_resp_code=$?
if [ $var_resp_code == 0 ]
then
  echo Success
  sed -i 's/\.[0-9]*,/,/g' ./reports/test.json
  java -jar ./lib/cucumber-sandwich.jar -f ./reports -o ./reports -n
  exit 0
else
  echo Failure
  sed -i 's/\.[0-9]*,/,/g' ./reports/test.json
  java -jar ./lib/cucumber-sandwich.jar -f ./reports -o ./reports -n
  exit 1
fi

