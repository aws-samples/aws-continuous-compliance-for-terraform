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
with open('stacks/pipeline_stack/cdk_stack_param.json', 'r') as f:
  params = json.load(f)
print(params)

class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        #####################################---START PREREQS---##########################################
        # Create a new Code Commit Repo for holding workload code
        source_repo = codecommit.Repository(
            self,
            'CodeCommitRepo',
            repository_name = params['CODE_COMMIT_SOURCE_REPO_NAME'],
            description = 'Workload repository'
        )
        # Source Repo ARN is going to be passed into the subsequent stacks that are created after this one.
        self.source_repo_arn = source_repo.repository_arn

        ## Terraform workload statefile resource creation

        # encryption key for terraform workload state file bucket
        statefile_encryption_key = kms.Key(
            self,
            'WorkloadStatefileEncryptionKey',
            #alias = core.Aws.STACK_NAME,
            alias = 'workload/statefile',
            description = 'Encryption key for workload statefile bucket',
            enabled = True,
            enable_key_rotation = True
        )

        # terraform workload state file bucket
        statefile_bucket = s3.Bucket(
            self,
            'WorkloadStatefileS3Bucket',
            access_control = s3.BucketAccessControl.PRIVATE,
            bucket_name = params['WORKLOAD_STATEFILE_BUCKET_NAME_PREFIX']+core.Aws.ACCOUNT_ID+'-'+core.Aws.REGION,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = statefile_encryption_key,
            lifecycle_rules = [
                s3.LifecycleRule(
                    enabled = True,
                    id = 'LccRule1-ExpireAllNoncurrentIn8Days',
                    noncurrent_version_expiration = core.Duration.days(8),
                    prefix = ''
                )
            ],
            public_read_access = False,
            removal_policy = core.RemovalPolicy.DESTROY,
            versioned = True
        )

        # CodePipeline artifact_bucket ecryption key
        pipeline_encryption_key = kms.Key(
            self,
            'PipelineEncryptionKey',
            #alias = core.Aws.STACK_NAME,
            alias = 'codepipeline/workload',
            description = 'Encryption key for workload codepipeline artifact_bucket',
            enabled = True,
            enable_key_rotation = True
        )
        print(core.Aws.ACCOUNT_ID)

        # CodePipeline Bucket
        pipeline_bucket = s3.Bucket(
            self,
            'CodePipelineS3Bucket',
            access_control = s3.BucketAccessControl.PRIVATE,
            bucket_name = 'pipeline-bucket-workload-'+core.Aws.ACCOUNT_ID,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = pipeline_encryption_key,
            lifecycle_rules = [
                s3.LifecycleRule(
                    enabled = True,
                    id = 'LccRule1-ExpireAllNoncurrentIn8Days',
                    noncurrent_version_expiration = core.Duration.days(8),
                    prefix = ''
                )
            ],
            public_read_access = False,
            removal_policy = core.RemovalPolicy.DESTROY,
            versioned = True
        )

        # Retrieve cross account role from params
        cross_account_role = params['COMPLIANCE_CODE']['CROSS_ACCOUNT_ROLE_ARN']
        print(cross_account_role)

        # IAM Role for CodePipeline
        code_pipeline_role = iam.Role(
            self,
            'CodePipelineRole',
            assumed_by = iam.ServicePrincipal('codepipeline.amazonaws.com')
        )

        # IAM Policy for CodePipeline
        code_pipeline_policy = iam.Policy(
            self,
            'CodePipelinePolicy',
            roles = [
                code_pipeline_role
            ],
            statements = [
                iam.PolicyStatement(
                    sid = 'KmsAllowKeyUsage',
                    actions = [
                        'kms:DescribeKey',
                        'kms:GetKeyPolicy',
                        'kms:List*',
                        'kms:Encrypt',
                        'kms:Decrypt',
                        'kms:ReEncrypt*',
                        'kms:Generate*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        pipeline_encryption_key.key_arn
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'CodeCommitRepoAccess',
                    actions = [
                        'codecommit:GetBranch',
                        'codecommit:GetCommit',
                        'codecommit:UploadArchive',
                        'codecommit:GetUploadArchiveStatus',
                        'codecommit:CancelUploadArchive'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        source_repo.repository_arn
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'PipelineBucketAccess',
                    actions = [
                        's3:GetBucket*',
                        's3:ListBucket*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        pipeline_bucket.bucket_arn
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'PipelineBucketObjectAccess',
                    actions = [
                        's3:AbortMultipartUpload',
                        's3:GetObject*',
                        's3:PutObject*',
                        's3:DeleteObject*',
                        's3:RestoreObject',
                        's3:ListMultipartUploadParts'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        pipeline_bucket.bucket_arn+'/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'PassRoleAccess',
                    actions = [
                        'iam:PassRole'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'BuilStartStopAccess',
                    actions = [
                        'codebuild:StartBuild',
                        'codebuild:BatchGetBuilds'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'AssumeDeploymentRolePolicy',
                    actions = [
                        'sts:AssumeRole'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [cross_account_role]
                )
            ]
        )

        # IAM Role for CodeBuild projects
        code_build_role = iam.Role(
            self,
            'CodeBuildRole',
            assumed_by = iam.ServicePrincipal('codebuild.amazonaws.com')
        )

        # IAM Policy for CodeBuild Projects
        code_build_policy = iam.Policy(
            self,
            'CodeBuildPolicy',
            roles = [
                code_build_role
            ],
            statements = [
                iam.PolicyStatement(
                    sid = 'KmsAllowKeyUsage',
                    actions = [
                        'kms:DescribeKey',
                        'kms:GetKeyPolicy',
                        'kms:List*',
                        'kms:Encrypt',
                        'kms:Decrypt',
                        'kms:ReEncrypt*',
                        'kms:Generate*',
                        'kms:TagResource',
                        'kms:UntagResource',
                        'kms:CreateKey',
                        'kms:GetKeyRotationStatus',
                        'kms:ScheduleKeyDeletion',
                        'kms:PutKeyPolicy'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'CloudWatchLogsPermissionsForAllCodeBuildProjects',
                    actions = [
                        'logs:*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'S3BucketAccess',
                    actions = [
                        's3:GetBucket*',
                        's3:ListBucket*',
                        's3:CreateBucket',
                        's3:DeleteBucket',
                        's3:PutBucketTagging',
                        's3:PutLifecycleConfiguration',
                        's3:GetLifecycleConfiguration',
                        's3:GetEncryptionConfiguration',
                        's3:PutEncryptionConfiguration',
                        's3:GetAccelerateConfiguration',
                        's3:PutAccelerateConfiguration',
                        's3:GetReplicationConfiguration',
                        's3:PutReplicationConfiguration',
                        's3:ReplicateTags',
                        's3:GetBucketPolicy',
                        's3:PutBucketPolicy',
                        's3:PutBucketLifecycle',
                        's3:GetAccelerateConfiguration',
                        's3:GetObject',
                        's3:PutObject',
                        's3:DeleteObjectVersion',
                        's3:GetBucketLogging',
                        's3:PutBucketLogging'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'StateFileBucketObjectAccess',
                    actions = [
                        's3:GetObject*',
                        's3:PutObject*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        statefile_bucket.bucket_arn+'/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'CodeCommitAccessPolicy',
                    actions = [
                        'codecommit:*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        source_repo.repository_arn
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'PassRoleAccess',
                    actions = [
                        'iam:PassRole',
                        'iam:CreateRole',
                        'iam:TagRole',
                        'iam:GetRole',
                        'iam:CreateInstanceProfile',
                        'iam:GetInstanceProfile',
                        'iam:DeleteInstanceProfile',
                        'iam:AddRoleToInstanceProfile',
                        'iam:ListInstanceProfilesForRole',
                        'iam:ListRolePolicies',
                        'iam:ListAttachedRolePolicies',
                        'iam:TagInstanceProfile',
                        'iam:RemoveRoleFromInstanceProfile',
                        'iam:DeleteRole'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'CodeBuildPermissions',
                    actions = [
                        'codebuild:Get*',
                        'codebuild:List*',
                        'codebuild:Describe*',
                        'codebuild:*Report*',
                        'codebuild:BatchPutTestCases'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'SnsPermissions',
                    actions = [
                        'sns:CreateTopic',
                        'sns:TagResource',
                        'sns:GetTopicAttributes',
                        'sns:ListTagsForResource',
                        'SNS:DeleteTopic'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'DlmPermissions',
                    actions = [
                        'dlm:*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'CWPermissions',
                    actions = [
                        'cloudwatch:*',
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'CloudTrailPermissions',
                    actions = [
                        'cloudtrail:*',
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'LambdaPermissions',
                    actions = [
                        'lambda:*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['arn:aws:lambda:*:*:function:demo-lambda']
                ),
                iam.PolicyStatement(
                    sid = 'ec2Permissions',
                    actions = [
                        'ec2:AuthorizeSecurityGroupEgress',
                        'ec2:AuthorizeSecurityGroupIngress',
                        'ec2:CreateSecurityGroup',
                        'ec2:DeleteSecurityGroup',
                        'ec2:DescribeSecurityGroups',
                        'ec2:RevokeSecurityGroupEgress',
                        'ec2:UpdateSecurityGroupRuleDescriptionsIngress',
                        'ec2:UpdateSecurityGroupRuleDescriptionsEgress',
                        'ec2:DescribeTags',
                        'ec2:CreateTags',
                        'ec2:DeleteTags',
                        'ec2:CreateVolume',
                        'ec2:DescribeVolume*',
                        'ec2:DescribeAvailabilityZones',
                        'ec2:CreateKeyPair',
                        'ec2:DeleteKeyPair',
                        'ec2:ImportKeyPair',
                        'ec2:DescribeKeyPairs',
                        'ec2:RunInstances',
                        'ec2:DescribeInstances',
                        'ec2:DescribeInstanceStatus',
                        'ec2:AssociateIamInstanceProfile',
                        'ec2:StartInstances',
                        'ec2:StopInstances',
                        'ec2:TerminateInstances',
                        'ec2:DescribeInstanceAttribute',
                        'ec2:DescribeVpcs',
                        'ec2:DescribeAccountAttributes',
                        'ec2:DescribeInstanceCreditSpecifications',
                        'ec2:GetDefaultCreditSpecification',
                        'ec2:ModifyDefaultCreditSpecification',
                        'ec2:ModifyInstanceCreditSpecification',
                        'ec2:DeleteVolume',
                        'ec2:DescribeNetworkInterfaceAttribute',
                        'ec2:DescribeNetworkInterfaces',
                        'ec2:DescribeNetworkInterfacePermissions',
                        'ec2:AttachNetworkInterface',
                        'ec2:DescribeNetworkInterfaces',
                        'ec2:DescribeNetworkInterfaceAttribute',
                        'ec2:DescribeNetworkInterfacePermissions',
                        'ec2:RevokeSecurityGroupIngress',
                        'ec2:DescribeImages'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'AssumeCrossAccountRoleForCodePull',
                    actions = [
                        'sts:AssumeRole'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [cross_account_role]
                )
            ]
        )

        # CodePipeline Encryption Key Policy
        pipeline_encryption_key.add_to_resource_policy(
            statement = iam.PolicyStatement(
                sid = 'KmsAllowKeyAdministration',
                actions = [
                    'kms:*'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.AccountRootPrincipal()
                ],
                resources = ['*']
            )
        )

        pipeline_encryption_key.add_to_resource_policy(
            statement = iam.PolicyStatement(
                sid = 'KmsAllowKeyUsage',
                actions = [
                    'kms:Decrypt',
                    'kms:DescribeKey',
                    'kms:Encrypt',
                    'kms:GenerateDataKey',
                    'kms:GenerateDataKeyWithoutPlainText',
                    'kms:ReEncrypt',
                    'kms:ReEncryptTo',
                    'kms:ReEncryptFrom',
                    'kms:TagResource',
                    'kms:CreateKey'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.ArnPrincipal(
                        arn = code_pipeline_role.role_arn
                    )
                ],
                resources = ['*']
            )
        )

        # CodePipeline Bucket Policy
        pipeline_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid = 'CodePipelineUsage',
                actions = [
                    's3:List*',
                    's3:Get*',
                    's3:Put*',
                    's3:Delete*',
                    's3:AbortMultipartUpload',
                    's3:RestoreObject',
                    's3:ListMultipartUploadParts'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.ArnPrincipal(
                        arn = code_pipeline_role.role_arn
                    )
                ],
                resources = [
                    pipeline_bucket.bucket_arn,
                    pipeline_bucket.bucket_arn+'/*'
                ]
            ),
        )

        # workload statefile Encryption Key Policy
        statefile_encryption_key.add_to_resource_policy(
            statement = iam.PolicyStatement(
                sid = 'KmsAllowKeyAdministration',
                actions = [
                    'kms:*'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.AccountRootPrincipal()
                ],
                resources = ['*']
            )
        )

        statefile_encryption_key.add_to_resource_policy(
            statement = iam.PolicyStatement(
                sid = 'KmsAllowKeyUsage',
                actions = [
                    'kms:Decrypt',
                    'kms:DescribeKey',
                    'kms:Encrypt',
                    'kms:GenerateDataKey',
                    'kms:GenerateDataKeyWithoutPlainText',
                    'kms:ReEncrypt',
                    'kms:ReEncryptTo',
                    'kms:ReEncryptFrom',
                    'kms:TagResource',
                    'kms:CreateKey'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.ArnPrincipal(
                        arn = code_build_role.role_arn
                    )
                ],
                resources = ['*']
            )
        )

        # workload statefile Bucket Policy
        statefile_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid = 'CodeBuildUsage',
                actions = [
                    's3:List*',
                    's3:Get*',
                    's3:Put*',
                    's3:Delete*',
                    's3:AbortMultipartUpload',
                    's3:RestoreObject',
                    's3:ListMultipartUploadParts'
                ],
                effect = iam.Effect.ALLOW,
                principals = [
                    iam.ArnPrincipal(
                        arn = code_build_role.role_arn
                    )
                ],
                resources = [
                    statefile_bucket.bucket_arn,
                    statefile_bucket.bucket_arn+'/*'
                ]
            ),
        )

        #####################################---END PREREQS---##########################################

        # Create code build project for pulling compliance code from remote Security & Compliance repo and executing compliance run on workload terraform
        code_build_compliance_run = codebuild.PipelineProject(
            self,
            'CodeBuildForComplianceRun',
            build_spec = codebuild.BuildSpec.from_source_filename('buildspec-compliance.yml'),
            description = 'CodeBuild project for pulling code from remote Security & Compliance repo and executing compliance run on workload terraform workload',
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.from_code_build_image_id(
                    'aws/codebuild/standard:4.0'
                ),
                compute_type = codebuild.ComputeType.SMALL
                #environment_variables = {
                #  'CROSS_ACCOUNT_ROLE': codebuild.BuildEnvironmentVariable(value=cross_account_role)
                #}
            ),
            project_name = 'cb-compliance-run-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_build_role
        )

        # Create code build project for workload deployment
        code_build_workload_deployment_run = codebuild.PipelineProject(
            self,
            'CodeBuildForWorkloadDeployment',
            build_spec = codebuild.BuildSpec.from_source_filename('buildspec-workload-deploy.yml'),
            description = 'CodeBuild project for deploying the terraform workload',
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.from_code_build_image_id(
                    'aws/codebuild/standard:4.0'
                ),
                compute_type = codebuild.ComputeType.SMALL
                #environment_variables = {
                #  'CROSS_ACCOUNT_ROLE': codebuild.BuildEnvironmentVariable(value=cross_account_role)
                #}
            ),
            project_name = 'cb-workload-deployment-run-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_build_role
        )

        # Create CodePipeline for compliance check of terraform workload
        pipeline = codepipeline.Pipeline(
            self,
            'WorkloadPipeline',
            artifact_bucket = pipeline_bucket,
            pipeline_name = 'pipeline-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_pipeline_role
        )

        # Add CodeCommit source repo as the action
        pipeline.add_stage(
            stage_name = 'Source',
            actions = [
                codepipeline_actions.CodeCommitSourceAction(
                    action_name = "Source",
                    output = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                    repository = source_repo,
                    branch = params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
                    trigger = codepipeline_actions.CodeCommitTrigger.EVENTS
                )
            ]
        )

        # Add stage to pull compliance source code and run compliance check
        tf_code_artifact_name_prefix = "tf_code_"
        pull_tf_code_stage = pipeline.add_stage(stage_name = 'RunComplianceCheck')
        #for tf_workload in params['TERRAFORM_APPLICATION_WORKLOAD_LIST']:
        pull_tf_code_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                input = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                project = code_build_compliance_run,
                environment_variables = {
                    'CROSS_ACCOUNT_ROLE': codebuild.BuildEnvironmentVariable(
                        value = cross_account_role,
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'COMPLIANCE_REPO_URL': codebuild.BuildEnvironmentVariable(
                        value = params['COMPLIANCE_CODE']['GIT_REPO_URL'],
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'WORLOAD_STATEFILE_BUCKET_NAME': codebuild.BuildEnvironmentVariable(
                        value = statefile_bucket.bucket_name,
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    )
                },
                outputs = [
                    codepipeline.Artifact(artifact_name = tf_code_artifact_name_prefix+params['COMPLIANCE_CODE']['ID'])
                ],
                type = codepipeline_actions.CodeBuildActionType.BUILD,
                action_name = 'RunCompliance_'+params['COMPLIANCE_CODE']['ID'],
                run_order = 5
            )
        )

        # Add stage to deploy workload
        tf_code_artifact_name_prefix2 = "tf_code2_"
        tf_workload_deploy_stage = pipeline.add_stage(stage_name = 'DeployWorkload')
        tf_workload_deploy_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                input = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                project = code_build_workload_deployment_run,
                environment_variables = {
                    'CROSS_ACCOUNT_ROLE': codebuild.BuildEnvironmentVariable(
                        value = cross_account_role,
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'COMPLIANCE_REPO_URL': codebuild.BuildEnvironmentVariable(
                        value = params['COMPLIANCE_CODE']['GIT_REPO_URL'],
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'WORLOAD_STATEFILE_BUCKET_NAME': codebuild.BuildEnvironmentVariable(
                        value = statefile_bucket.bucket_name,
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    )
                },
                outputs = [
                    codepipeline.Artifact(artifact_name = tf_code_artifact_name_prefix2+params['COMPLIANCE_CODE']['ID'])
                ],
                type = codepipeline_actions.CodeBuildActionType.BUILD,
                action_name = 'DeployWorkload_'+params['COMPLIANCE_CODE']['ID'],
                run_order = 6
            )
        )

        ########################### List of Outputs ##########################
        core.CfnOutput(
            self,
            'OutSourceRepoArn',
            value = source_repo.repository_arn,
            description = 'workload source Repository ARN',
            export_name = 'WORKLOAD-SOURCE-REPO-ARN'
        )

        core.CfnOutput(
            self,
            'OutSourceRepoHttpUrl',
            value = source_repo.repository_clone_url_http,
            description = 'Workload source Repository Http URL',
            export_name = 'WORKLOAD-SOURCE-REPO-HTTP-URL'
        )

        core.CfnOutput(
            self,
            'OutPipelineBucketName',
            value = pipeline_bucket.bucket_name,
            description = 'Pipeline Bucket Name',
            export_name = 'PIPELINE-BUCKET-NAME'
        )

        core.CfnOutput(
            self,
            'OutStateFileBucketName',
            value = statefile_bucket.bucket_name,
            description = 'Terraform Backend StateFile Bucket Name',
            export_name = 'STATEFILE-BUCKET-NAME'
        )
        ##########################################################################
