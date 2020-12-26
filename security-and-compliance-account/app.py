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

#!/usr/bin/env python3

from aws_cdk import core

from stacks.pipeline_stack.cdk_stack import PipelineStack
from stacks.cross_account_role_stack.cdk_stack import CrossAccountRoleStack

app = core.App()

# Create Pipeline Stack and retrieve ARN of codecommit repo
pipeline_stack = PipelineStack(
  app,
  'PipelineStack',
  stack_name='cf-SecurityAndCompliancePipeline',
  description = 'Security and compliance pipeline'
)

source_repo_arn = pipeline_stack.source_repo_arn

# Create CrossAccount IAM role stack and pass ARN of codecommit repo
CrossAccountRoleStack(
  app, 
  'CrossAccountRoleStack',
  source_repo_arn=source_repo_arn,
  stack_name='cf-CrossAccountRoles', 
  description = 'IAM role to allows app accounts to pull code for compliance check'
)

app.synth()
