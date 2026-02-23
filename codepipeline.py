import pulumi_aws as aws


def create_codepipeline(config, artifact_bucket, codestar_connection,
                         codebuild_project, codedeploy_app, codedeploy_group,
                         codepipeline_role):
    """Create a V2 CodePipeline with Source, Build, and Deploy stages."""
    name_prefix = config["name_prefix"]

    pipeline = aws.codepipeline.Pipeline(
        "codepipeline",
        name=f"{name_prefix}-pipeline",
        role_arn=codepipeline_role.arn,
        pipeline_type="V2",
        execution_mode="QUEUED",
        artifact_stores=[aws.codepipeline.PipelineArtifactStoreArgs(
            location=artifact_bucket.bucket,
            type="S3",
        )],
        stages=[
            # Stage 1: Source — pull code from GitHub via CodeStar Connection
            aws.codepipeline.PipelineStageArgs(
                name="Source",
                actions=[aws.codepipeline.PipelineStageActionArgs(
                    name="GitHub-Source",
                    category="Source",
                    owner="AWS",
                    provider="CodeStarSourceConnection",
                    version="1",
                    output_artifacts=["source_output"],
                    configuration={
                        "ConnectionArn": codestar_connection.arn,
                        "FullRepositoryId": f"{config['github_repo_owner']}/{config['github_repo_name']}",
                        "BranchName": config["github_branch"],
                        "OutputArtifactFormat": "CODE_ZIP",
                    },
                )],
            ),
            # Stage 2: Build — build Docker image and push to ECR
            aws.codepipeline.PipelineStageArgs(
                name="Build",
                actions=[aws.codepipeline.PipelineStageActionArgs(
                    name="Docker-Build",
                    category="Build",
                    owner="AWS",
                    provider="CodeBuild",
                    version="1",
                    input_artifacts=["source_output"],
                    output_artifacts=["build_output"],
                    configuration={
                        "ProjectName": codebuild_project.name,
                    },
                )],
            ),
            # Stage 3: Deploy — canary deployment to Lambda via CodeDeploy
            aws.codepipeline.PipelineStageArgs(
                name="Deploy",
                actions=[aws.codepipeline.PipelineStageActionArgs(
                    name="Lambda-Deploy",
                    category="Deploy",
                    owner="AWS",
                    provider="CodeDeployToLambda",
                    version="1",
                    input_artifacts=["build_output"],
                    configuration={
                        "ApplicationName": codedeploy_app.name,
                        "DeploymentGroupName": codedeploy_group.deployment_group_name,
                    },
                )],
            ),
        ],
        tags=config["common_tags"],
    )

    return pipeline
