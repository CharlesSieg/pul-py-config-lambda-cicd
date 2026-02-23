import json

import pulumi_aws as aws


def create_ecr_repo(config):
    """Create an ECR repository for Lambda container images."""
    name_prefix = config["name_prefix"]

    # ECR repository with immutable tags and scan-on-push
    repo = aws.ecr.Repository(
        "lambda-ecr-repo",
        name=f"{name_prefix}-lambda",
        image_tag_mutability="IMMUTABLE",
        image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
            scan_on_push=True,
        ),
        tags=config["common_tags"],
    )

    # Lifecycle policy to keep only the last 10 images
    aws.ecr.LifecyclePolicy(
        "lambda-ecr-lifecycle",
        repository=repo.name,
        policy=json.dumps({
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep only the last 10 images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10,
                    },
                    "action": {
                        "type": "expire",
                    },
                }
            ]
        }),
    )

    return repo
