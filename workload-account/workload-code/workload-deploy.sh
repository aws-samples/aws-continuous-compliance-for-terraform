# Copyright 2019-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#!/bin/bash

[ -n "${AWS_DEFAULT_REGION}" ] || { echo "AWS_DEFAULT_REGION environment variable not defined"; exit 1; }
[ -n "${WORLOAD_STATEFILE_BUCKET_NAME}" ] || { echo "WORLOAD_STATEFILE_BUCKET_NAME environment variable not defined"; exit 1; }

if [ "$1" == "--destroy" ]; then
    terraformAction="destroy"
elif [ "$#" -eq 0 ]; then
    terraformAction="apply"
fi


# Create Terraform Plan and apply
cd ./src
terraform init \
-backend-config="bucket=${WORLOAD_STATEFILE_BUCKET_NAME}" \
-backend-config="region=${AWS_DEFAULT_REGION}"

if [ $terraformAction = "apply" ]; then
    terraform apply -auto-approve \
        -var "region=${AWS_DEFAULT_REGION}"
    var_resp_code=$?
elif [ $terraformAction = "destroy" ]; then
    terraform destroy -force \
        -var "region=${AWS_DEFAULT_REGION}"
    var_resp_code=$?
else
    echo "Invalid Terraform action: ${terraformAction}"
    exit 2
fi


# Handle reponse
if [ $var_resp_code = 0 ]
then
  echo Success
  exit 0
else
  echo Failure
  exit 1
fi
