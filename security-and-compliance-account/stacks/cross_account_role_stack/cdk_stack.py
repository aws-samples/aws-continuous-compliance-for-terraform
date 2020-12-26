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

from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
import json
import os

# Pipeline Stack Parameters 
params = {}
with open('stacks/cross_account_role_stack/cdk_stack_param.json', 'r') as f:
  params = json.load(f)
print(params)


class CrossAccountRoleStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, source_repo_arn, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        #####################################---START---##########################################
        # List of principals to have access for code pull
        principal_list = []
        for account in params['TERRAFORM_APPLICATION_WORKLOAD_ACCOUNTS']:
            principal_list.append(iam.AccountPrincipal(account['AWS_ACCOUNT_ID']))
        print(principal_list)

        # IAM Role for Cross Account Access to the security and compliance account
        cross_account_role = iam.Role(
            self,
            'CrossAccountRole',
            assumed_by = iam.CompositePrincipal(*principal_list),
            description = "Cross Account role that allows application accounts to pull compliance checks from securituy and compliance account",
            role_name = 'allow-compliance-code-pull'
        )

        # IAM Policy for cross account role
        cross_account_policy = iam.Policy(
            self,
            'CrossAccountPolicy',
            roles = [
                cross_account_role
            ],
            statements = [
                iam.PolicyStatement(
                    sid = 'KmsAllowKeyUsage',
                    actions = [
                        'codecommit:GitPull'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        source_repo_arn
                    ]
                )
            ]
        )        
        #####################################---END---##########################################

        ########################### List of Outputs ##########################
        core.CfnOutput(
            self, 
            'OutCrossAccountRoleArn',
            value = cross_account_role.role_arn,
            description = 'Cross Account Role ARN',
            export_name = 'GOLDMINE-CROSS-ACCOUNT-CODE-PULL-ROLE-ARN'
        )
        ##########################################################################