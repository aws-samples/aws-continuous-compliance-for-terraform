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
        # Create a new Code Commit Repo for holding compliance code
        source_repo = codecommit.Repository(
            self,
            'CodeCommitRepo',
            repository_name = params['CODE_COMMIT_SOURCE_REPO_NAME'],
            description = 'Compliance code repository'
        )
        # Source Repo ARN is going to be passed into the subsequent stacks that are created after this one.
        self.source_repo_arn = source_repo.repository_arn

        # CodePipeline ecryption key
        pipeline_encryption_key = kms.Key(
            self,
            'PipelineEncryptionKey',
            alias = 'goldmine/codepipeline/security-compliance',
            description = 'Encryprion for security and compliance codepipeline',
            enabled = True,
            enable_key_rotation = True
        )

        # CodePipeline Bucket
        pipeline_bucket = s3.Bucket(
            self,
            'CodePipelineS3Bucket',
            access_control = s3.BucketAccessControl.PRIVATE,
            bucket_name = 'pipeline-bucket-sec-compliance-'+core.Aws.ACCOUNT_ID,
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

        # Terraform Backend Bucket
        # The bucket is created in the same region as the pipeline. 
        # If you want to use an existing bucket then avoid creating this bucket.
        # Instead, directly supply it to the code build job in the pipeline below.
        # Make sure that the code pipeline role has required access to your bucket. 
        tf_backend_bucket = s3.Bucket(
            self,
            'TfBackendS3Bucket',
            access_control = s3.BucketAccessControl.PRIVATE,
            bucket_name = 'tf-backend-bucket-'+core.Aws.ACCOUNT_ID,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = pipeline_encryption_key,
            public_read_access = False,
            removal_policy = core.RemovalPolicy.DESTROY,
            versioned = True
        )

        # Retrieve cross account role list from params
        cross_account_role_list = []
        for tf_workload in params['TERRAFORM_APPLICATION_WORKLOADS']:
            cross_account_role_list.append(tf_workload['CROSS_ACCOUNT_ROLE_ARN'])
        print(cross_account_role_list)
        
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
                    sid = 'BuildStartStopAccess',
                    actions = [
                        'codebuild:StartBuild',
                        'codebuild:BatchGetBuilds'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
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
                    sid = 'CloudWatchLogsPermissionsForAllCodeBuildProjects',
                    actions = [
                        'logs:*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'TerraformBackendBucketAccess',
                    actions = [
                        's3:GetBucket*',
                        's3:ListBucket*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        tf_backend_bucket.bucket_arn
                    ]
                ),
                iam.PolicyStatement(
                    sid = 'TerraformBackendObjectAccess',
                    actions = [
                        's3:GetObject*',
                        's3:PutObject*'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = [
                        tf_backend_bucket.bucket_arn+'/*'
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
                    sid = 'AssumeCrossAccountRoleForCodePull',
                    actions = [
                        'sts:AssumeRole'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = cross_account_role_list
                ),
                iam.PolicyStatement(
                    sid = 'FetchAZForTerraformPlan',
                    actions = [
                        'ec2:DescribeAvailabilityZones'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
                ),
                iam.PolicyStatement(
                    sid = 'RegionBasedAMILookupForTF',
                    actions = [
                        'ec2:DescribeImages'
                    ],
                    effect = iam.Effect.ALLOW,
                    resources = ['*']
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

        # Terraform Backend Bucket Policy
        tf_backend_bucket.add_to_resource_policy(
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
                        arn = code_build_role.role_arn
                    )
                ],
                resources = [
                    tf_backend_bucket.bucket_arn,
                    tf_backend_bucket.bucket_arn+'/*'
                ]
            ),
        )
        #####################################---END---##########################################

        # Create code build project for pulling code from remote terraform workload repo
        code_build_code_pull = codebuild.PipelineProject(
            self,
            'CodeBuildForCodePull',
            build_spec = codebuild.BuildSpec.from_source_filename('buildspec-code-pull.yml'),
            description = 'CodeBuild project for pulling code from remote terraform workload repos',
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.from_code_build_image_id(
                    'aws/codebuild/amazonlinux2-x86_64-standard:3.0'
                ),
                compute_type = codebuild.ComputeType.SMALL
            ),
            project_name = 'cb-code-pull-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_build_role
        )

        # Create code build project for carrying out compliance checks on terraform workload repo
        code_build_compliance_check = codebuild.PipelineProject(
            self,
            'CodeBuildForComplianceCheck',
            build_spec = codebuild.BuildSpec.from_source_filename('buildspec-compliance-check.yml'),
            description = 'CodeBuild project for carrying out compliance checks on terraform workload repo',
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.from_code_build_image_id(
                    'aws/codebuild/amazonlinux2-x86_64-standard:3.0'
                ),
                compute_type = codebuild.ComputeType.SMALL
            ),
            project_name = 'cb-compliance-check-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_build_role
        )

        # Create code build project for merging compliance code into main branch
        code_build_code_merge = codebuild.PipelineProject(
            self,
            'CodeBuildForCodeMerge',
            build_spec = codebuild.BuildSpec.from_source_filename('buildspec-code-merge.yml'),
            description = 'CodeBuild project for merging compliance code into main branch',
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.from_code_build_image_id(
                    'aws/codebuild/amazonlinux2-x86_64-standard:3.0'
                ),
                compute_type = codebuild.ComputeType.SMALL
            ),
            project_name = 'cb-code-merge-'+params['CODE_COMMIT_SOURCE_REPO_NAME']+'-'+params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
            role = code_build_role
        )

        # Create CodePipeline for compliance check
        pipeline = codepipeline.Pipeline(
            self,
            'SecurityAndCompliancePipeline',
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

        # Add stage to pull terraform source workload
        tf_code_artifact_name_prefix = "tf_code_"
        pull_tf_code_stage = pipeline.add_stage(stage_name = 'PullTerraformCode')
        for tf_workload in params['TERRAFORM_APPLICATION_WORKLOADS']:
            pull_tf_code_stage.add_action(
                codepipeline_actions.CodeBuildAction(
                    input = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                    project = code_build_code_pull,
                    environment_variables = {
                        'CROSS_ACCOUNT_ROLE': codebuild.BuildEnvironmentVariable(
                            value = tf_workload['CROSS_ACCOUNT_ROLE_ARN'],
                            type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                        ),
                        'TF_WOKLOAD_REPO_URL': codebuild.BuildEnvironmentVariable(
                            value = tf_workload['GIT_REPO_URL'],
                            type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                        )

                    },
                    outputs = [
                        codepipeline.Artifact(artifact_name = tf_code_artifact_name_prefix+tf_workload['APP_ID'])
                    ],
                    type = codepipeline_actions.CodeBuildActionType.BUILD,
                    action_name = 'PullCode_'+tf_workload['APP_ID'],
                    run_order = 10
                )
            )
        
        # Add stage to perform compliance check on terraform source workload
        compliance_check_stage = pipeline.add_stage(stage_name = 'PerformComplianceCheck')
        for tf_workload in params['TERRAFORM_APPLICATION_WORKLOADS']:
            compliance_check_stage.add_action(
                codepipeline_actions.CodeBuildAction(
                    input = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                    project = code_build_compliance_check,
                    environment_variables = {
                        'TF_SOURCE_CODE_FOLDER': codebuild.BuildEnvironmentVariable(
                            value = 'CODEBUILD_SRC_DIR_'+tf_code_artifact_name_prefix+tf_workload['APP_ID'],
                            type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                        ),
                        'TF_BACKEND_S3_BUCKET': codebuild.BuildEnvironmentVariable(
                            value = tf_backend_bucket.bucket_name,
                            type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                        )
                    },
                    extra_inputs = [
                        codepipeline.Artifact(artifact_name = tf_code_artifact_name_prefix+tf_workload['APP_ID'])
                    ],
                    outputs = [
                        codepipeline.Artifact(artifact_name = 'report_'+tf_workload['APP_ID'])
                    ],
                    type = codepipeline_actions.CodeBuildActionType.BUILD,
                    action_name = 'ComplianceCheck_'+tf_workload['APP_ID'],
                    run_order = 10
                )
            )
        
        # Add stage to perform compliance check on terraform source workload
        code_merge_stage = pipeline.add_stage(stage_name = 'MergeCode')
        code_merge_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                input = codepipeline.Artifact(artifact_name = 'SourceArtifact'),
                project = code_build_code_merge,
                environment_variables = {
                    'CODE_COMMIT_SOURCE_REPO_NAME': codebuild.BuildEnvironmentVariable(
                        value = params['CODE_COMMIT_SOURCE_REPO_NAME'],
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'CODE_COMMIT_SOURCE_BRANCH': codebuild.BuildEnvironmentVariable(
                        value = params['CODE_COMMIT_SOURCE_REPO_BRANCH'],
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    ),
                    'CODE_COMMIT_TARGET_BRANCH': codebuild.BuildEnvironmentVariable(
                        value = 'main',
                        type = codebuild.BuildEnvironmentVariableType.PLAINTEXT
                    )
                },
                outputs = [
                    codepipeline.Artifact(artifact_name = 'merge_response')
                ],
                type = codepipeline_actions.CodeBuildActionType.BUILD,
                action_name = 'CodeMerge',
                run_order = 10
            )
        )

        ########################### List of Outputs ##########################
        core.CfnOutput(
            self, 
            'OutSourceRepoArn',
            value = source_repo.repository_arn,
            description = 'Source Repository ARN',
            export_name = 'GOLDMINE-SOURCE-REPO-ARN'
        )

        core.CfnOutput(
            self, 
            'OutSourceRepoHttpUrl',
            value = source_repo.repository_clone_url_http,
            description = 'Source Repository Http URL',
            export_name = 'GOLDMINE-SOURCE-REPO-HTTP-URL'
        )

        core.CfnOutput(
            self, 
            'OutPipelineBucketName',
            value = pipeline_bucket.bucket_name,
            description = 'Pipeline Bucket Name',
            export_name = 'PIPELINE-BUCKET-NAME'
        )
        ##########################################################################