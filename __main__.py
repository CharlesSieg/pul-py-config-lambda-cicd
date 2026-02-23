"""CI/CD pipeline for containerized AWS Lambda functions.

Deploys a complete pipeline: GitHub source via CodeStar Connection, CodeBuild
for Docker image builds pushed to ECR, and CodeDeploy for canary Lambda
deployments with alarm-based automatic rollback.

Pipeline flow:
    GitHub → CodeStar → CodePipeline → CodeBuild → ECR → CodeDeploy → Lambda
"""

import pulumi

from config import get_config
from ecr import create_ecr_repo
from s3 import create_artifact_bucket
from iam import (
    create_codebuild_role,
    create_codedeploy_role,
    create_codepipeline_role,
    create_lambda_role,
)
from codestar import create_codestar_connection
from codebuild import create_codebuild_project
from lambda_function import create_lambda_function
from cloudwatch import create_cloudwatch_resources
from codedeploy import create_codedeploy
from codepipeline import create_codepipeline

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

config = get_config()

# ---------------------------------------------------------------------------
# ECR — container image repository
# ---------------------------------------------------------------------------

ecr_repo = create_ecr_repo(config)

# ---------------------------------------------------------------------------
# S3 — pipeline artifact bucket
# ---------------------------------------------------------------------------

artifact_bucket = create_artifact_bucket(config)

# ---------------------------------------------------------------------------
# IAM — roles that do not depend on other resources
# ---------------------------------------------------------------------------

lambda_role = create_lambda_role(config)
codedeploy_role = create_codedeploy_role(config)

# ---------------------------------------------------------------------------
# CodeStar — GitHub source connection
# ---------------------------------------------------------------------------

codestar_connection = create_codestar_connection(config)

# ---------------------------------------------------------------------------
# IAM — CodeBuild role (depends on ECR and S3)
# ---------------------------------------------------------------------------

codebuild_role = create_codebuild_role(config, ecr_repo, artifact_bucket)

# ---------------------------------------------------------------------------
# CodeBuild — Docker image build project
# ---------------------------------------------------------------------------

codebuild_project = create_codebuild_project(config, ecr_repo, codebuild_role)

# ---------------------------------------------------------------------------
# Lambda — containerized function with "live" alias
# ---------------------------------------------------------------------------

lambda_function, lambda_alias = create_lambda_function(config, ecr_repo, lambda_role)

# ---------------------------------------------------------------------------
# CloudWatch — log group and error alarm
# ---------------------------------------------------------------------------

log_group, error_alarm = create_cloudwatch_resources(config, lambda_function)

# ---------------------------------------------------------------------------
# CodeDeploy — canary deployment with alarm rollback
# ---------------------------------------------------------------------------

codedeploy_app, codedeploy_group = create_codedeploy(
    config, lambda_function, lambda_alias, error_alarm, codedeploy_role
)

# ---------------------------------------------------------------------------
# IAM — CodePipeline role (depends on most resources)
# ---------------------------------------------------------------------------

codepipeline_role = create_codepipeline_role(
    config, artifact_bucket, codebuild_project, codestar_connection,
    lambda_function, codedeploy_role
)

# ---------------------------------------------------------------------------
# CodePipeline — orchestrates source, build, and deploy stages
# ---------------------------------------------------------------------------

pipeline = create_codepipeline(
    config, artifact_bucket, codestar_connection, codebuild_project,
    codedeploy_app, codedeploy_group, codepipeline_role
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

pulumi.export("pipeline_arn", pipeline.arn)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("lambda_function_arn", lambda_function.arn)
pulumi.export("lambda_function_name", lambda_function.function_name)
pulumi.export("codedeploy_app_name", codedeploy_app.name)
pulumi.export("codedeploy_group_name", codedeploy_group.deployment_group_name)
