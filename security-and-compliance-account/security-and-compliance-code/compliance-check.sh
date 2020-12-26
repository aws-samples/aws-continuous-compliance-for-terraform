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

# CLI Parameters
# Terraform plan directory
arg_tf_dir=$1
# Cucumber Reports directory
arg_reports_dir=$2
# Tag that identifies specific features to be run
arg_tag=$3

# Create Terraform Plan
echo $arg_tf_dir
cd $arg_tf_dir
terraform init \
  -backend-config="region=${AWS_DEFAULT_REGION}" \
  -backend-config="bucket=${TF_BACKEND_S3_BUCKET}"
terraform plan -var "region=${AWS_DEFAULT_REGION}" -out="plan.out"

# Check for compliance
cd $CODEBUILD_SRC_DIR
if [[ $arg_tag != "" ]]
then
  echo "Compliance check requested for tag $arg_tag"
  terraform-compliance -f ./src/ -p $arg_tf_dir/plan.out --cucumber-json=$arg_reports_dir/test.json --tags $arg_tag
  terraform-compliance -f ./src/ -p $arg_tf_dir/plan.out --bdd-xml=$arg_reports_dir/test.xml --tags $arg_tag
else
  echo "Compliance check requested for all tags"
  terraform-compliance -f ./src/ -p $arg_tf_dir/plan.out --cucumber-json=$arg_reports_dir/test.json
  terraform-compliance -f ./src/ -p $arg_tf_dir/plan.out --bdd-xml=$arg_reports_dir/test.xml
fi

# Handle reponse
var_resp_code=$?

# Generate Cucumber report
sed -i 's/\.[0-9]*,/,/g' $arg_reports_dir/test.json
java -jar ./lib/cucumber-sandwich.jar -f $arg_reports_dir -o $arg_reports_dir -n
if [ $var_resp_code == 0 ]
then
  echo Success
  exit 0
else
  echo Failure
  exit 1
fi