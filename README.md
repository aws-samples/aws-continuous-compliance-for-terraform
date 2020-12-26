
# Continuous Compliance For Terraform Using Terraform Compliance Framework and Code Pipeline

This codebase is associated with a blog *(blog url to be posted soon)*
There are two sub-projects in this codebase that need to be deployed in two separate AWS accounts
1. Security and compliance account
2. Workload account

## Security and compliance codebase
Here we deploy two CDK stacks.
> 1. Cross Account Roles that give permission to workload account to pull compliance checks from security and compliance account repo to carry out compliance checks
> 2. Pipeline stack that consists of AWS CodePipeline which implements continuous compliance workflow using which we release new compliance checks. It also create a AWS CodeCommit repository where you can checkin the compliance checks.
> Both the stacks can be found under `security-and-compliance-account/stacks` folder. `security-and-compliance-account/app.py` represents the main CDK app that brings together the above two stacks and deploys them one after the other. The main CDK app is invoked when we run cdk commands.
> Besides this, we have provided sample compliance checks implemented using terraform-compliance framework. The code is accompanied by buildspecs as required by the AWS CodeBuild projects in the pipeline.
>
> In order to deploy security and compliance account stacks run below command
> ```security-and-compliance-accountdeploy/deploy.sh <aws-profile-name>```
> You need to first create an AWS profile before you execute the cdk command

## Workload codebase
Here we deploy two CDK stacks.
> 1. Cross Account Roles that give permission to security and compliance account to pull terraform code from workload account repo to carry out compliance checks
> 2. Pipeline stack that consists of AWS CodePipeline which implements CICD workflow to deploy AWS resources written in terraform. It also create a AWS CodeCommit repository where you can checkin the terraform.
> Both the stacks can be found under `workload-account/stacks` folder. `workload-account/app.py` represents the main CDK app that brings together the above two stacks and deploys them one after the other. The main CDK app is invoked when we run cdk commands.
> Besides this, we have provided terraform workload to be deployed by the workload pipeline after it successfully carries out compliance checks. The code is accompanied by buildspecs as required by the AWS CodeBuild projects in the pipeline.
>
> In order to deploy security and compliance account stacks run below command
> ```workload-account/deploy.sh <aws-profile-name>```
> You need to first create an AWS profile before you execute the cdk command


