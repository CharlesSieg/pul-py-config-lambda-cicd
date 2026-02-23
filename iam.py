import json

import pulumi
import pulumi_aws as aws


def create_codebuild_role(config, ecr_repo, artifact_bucket):
    """Create an IAM role for CodeBuild with ECR, S3, and CloudWatch Logs permissions."""
    name_prefix = config["name_prefix"]

    # Get the current AWS account ID and region
    current = aws.get_caller_identity()
    region = config["region"]

    # Trust policy for CodeBuild
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "codebuild.amazonaws.com",
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": current.account_id,
                    },
                },
            }
        ],
    })

    role = aws.iam.Role(
        "codebuild-role",
        name=f"{name_prefix}-codebuild-role",
        assume_role_policy=trust_policy,
        tags=config["common_tags"],
    )

    # Policy granting ECR push/pull, S3 artifact access, and CloudWatch Logs
    policy_document = pulumi.Output.all(
        ecr_repo.arn, artifact_bucket.arn
    ).apply(lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:CompleteLayerUpload",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:InitiateLayerUpload",
                    "ecr:PutImage",
                    "ecr:UploadLayerPart",
                    "ecr:BatchGetImage",
                ],
                "Resource": args[0],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject",
                ],
                "Resource": f"{args[1]}/*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketAcl",
                    "s3:GetBucketLocation",
                ],
                "Resource": args[1],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": f"arn:aws:logs:{region}:{current.account_id}:log-group:/aws/codebuild/{name_prefix}-build*",
            },
        ],
    }))

    aws.iam.RolePolicy(
        "codebuild-policy",
        name=f"{name_prefix}-codebuild-policy",
        role=role.id,
        policy=policy_document,
    )

    return role


def create_codepipeline_role(config, artifact_bucket, codebuild_project,
                              codestar_connection, lambda_function, codedeploy_role):
    """Create an IAM role for CodePipeline with permissions for all pipeline stages."""
    name_prefix = config["name_prefix"]

    # Get the current AWS account ID
    current = aws.get_caller_identity()

    # Trust policy for CodePipeline
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "codepipeline.amazonaws.com",
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": current.account_id,
                    },
                },
            }
        ],
    })

    role = aws.iam.Role(
        "codepipeline-role",
        name=f"{name_prefix}-codepipeline-role",
        assume_role_policy=trust_policy,
        tags=config["common_tags"],
    )

    # Policy granting access to S3, CodeBuild, CodeDeploy, CodeStar, Lambda, and IAM
    policy_document = pulumi.Output.all(
        artifact_bucket.arn,
        codebuild_project.arn,
        codestar_connection.arn,
        lambda_function.arn,
        codedeploy_role.arn,
    ).apply(lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:GetBucketVersioning",
                    "s3:PutObject",
                ],
                "Resource": [
                    args[0],
                    f"{args[0]}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "codebuild:StartBuild",
                    "codebuild:BatchGetBuilds",
                ],
                "Resource": args[1],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "codedeploy:CreateDeployment",
                    "codedeploy:GetDeployment",
                    "codedeploy:GetApplication",
                    "codedeploy:GetApplicationRevision",
                    "codedeploy:RegisterApplicationRevision",
                    "codedeploy:GetDeploymentConfig",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "codestar-connections:UseConnection",
                ],
                "Resource": args[2],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction",
                    "lambda:GetFunction",
                    "lambda:GetAlias",
                    "lambda:UpdateAlias",
                ],
                "Resource": [
                    args[3],
                    f"{args[3]}:*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:PassRole",
                ],
                "Resource": args[4],
                "Condition": {
                    "StringEquals": {
                        "iam:PassedToService": "codedeploy.amazonaws.com",
                    },
                },
            },
        ],
    }))

    aws.iam.RolePolicy(
        "codepipeline-policy",
        name=f"{name_prefix}-codepipeline-policy",
        role=role.id,
        policy=policy_document,
    )

    return role


def create_lambda_role(config):
    """Create an IAM execution role for the Lambda function."""
    name_prefix = config["name_prefix"]

    # Trust policy for Lambda
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com",
                },
                "Action": "sts:AssumeRole",
            }
        ],
    })

    role = aws.iam.Role(
        "lambda-role",
        name=f"{name_prefix}-lambda-role",
        assume_role_policy=trust_policy,
        tags=config["common_tags"],
    )

    # Attach the basic execution managed policy
    aws.iam.RolePolicyAttachment(
        "lambda-basic-execution",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    return role


def create_codedeploy_role(config):
    """Create an IAM service role for CodeDeploy."""
    name_prefix = config["name_prefix"]

    # Trust policy for CodeDeploy
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "codedeploy.amazonaws.com",
                },
                "Action": "sts:AssumeRole",
            }
        ],
    })

    role = aws.iam.Role(
        "codedeploy-role",
        name=f"{name_prefix}-codedeploy-role",
        assume_role_policy=trust_policy,
        tags=config["common_tags"],
    )

    # Attach the CodeDeploy for Lambda managed policy
    aws.iam.RolePolicyAttachment(
        "codedeploy-lambda-policy",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/AWSCodeDeployRoleForLambda",
    )

    return role
