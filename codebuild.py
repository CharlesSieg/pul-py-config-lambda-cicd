import pulumi
import pulumi_aws as aws


def create_codebuild_project(config, ecr_repo, codebuild_role):
    """Create a CodeBuild project for building and pushing Docker images to ECR."""
    name_prefix = config["name_prefix"]
    region = config["region"]

    # Get the current AWS account ID
    current = aws.get_caller_identity()

    project = aws.codebuild.Project(
        "codebuild-project",
        name=f"{name_prefix}-build",
        description=f"Build Docker images for {name_prefix} Lambda function",
        service_role=codebuild_role.arn,
        artifacts=aws.codebuild.ProjectArtifactsArgs(
            type="CODEPIPELINE",
        ),
        environment=aws.codebuild.ProjectEnvironmentArgs(
            compute_type="BUILD_GENERAL1_SMALL",
            image="aws/codebuild/amazonlinux2-x86_64-standard:5.0",
            type="LINUX_CONTAINER",
            privileged_mode=True,
            environment_variables=[
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="AWS_DEFAULT_REGION",
                    value=region,
                ),
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="AWS_ACCOUNT_ID",
                    value=current.account_id,
                ),
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="IMAGE_REPO_NAME",
                    value=ecr_repo.name,
                ),
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="IMAGE_TAG",
                    value="latest",
                ),
            ],
        ),
        source=aws.codebuild.ProjectSourceArgs(
            type="CODEPIPELINE",
        ),
        tags=config["common_tags"],
    )

    return project
