# Lambda CI/CD Pipeline — Pulumi (Python)

Pulumi Python program for deploying a CI/CD pipeline for containerized AWS Lambda functions.

## Architecture

```
GitHub → CodeStar Connection → CodePipeline → CodeBuild → ECR → CodeDeploy → Lambda
```

## Resources Created

- **Amazon ECR** — Container image repository with immutable tags and scan-on-push
- **AWS CodeBuild** — Build project for Docker image builds with ECR push
- **AWS CodePipeline** — V2 pipeline orchestrating source, build, and deploy stages
- **AWS CodeDeploy** — Lambda deployment with Canary10Percent5Minutes traffic shifting
- **AWS Lambda** — Container image function with "live" alias for traffic shifting
- **CloudWatch** — Lambda log group and error alarm for CodeDeploy rollback triggers
- **S3** — Pipeline artifact bucket with versioning and encryption
- **IAM** — Least-privilege roles for CodeBuild, CodePipeline, Lambda, and CodeDeploy
- **CodeStar Connection** — GitHub source integration (requires manual console activation)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
pulumi stack init dev
pulumi config set project_name myapp
pulumi config set github_repo_owner MyOrg
pulumi config set github_repo_name my-lambda
pulumi config set aws:region us-east-1
pulumi up
```

After deploying, activate the CodeStar Connection in the AWS Console under Developer Tools → Connections.

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `project_name` | — | Project name used in resource naming |
| `environment` | `dev` | Environment (dev, staging, prod) |
| `github_repo_owner` | — | GitHub repository owner |
| `github_repo_name` | — | GitHub repository name |
| `github_branch` | `main` | Branch to trigger pipeline |
| `lambda_memory_size` | `256` | Lambda memory in MB (128–10240) |
| `lambda_timeout` | `30` | Lambda timeout in seconds (1–900) |
| `lambda_architecture` | `x86_64` | Lambda architecture (x86_64, arm64) |

## Bootstrap Sequence

CodeDeploy requires an existing Lambda function with a published version. The Lambda function requires a container image in ECR. Therefore:

1. Run `pulumi up` (this will create ECR but Lambda creation may fail)
2. Build and push an initial image to the ECR repository
3. Run `pulumi up` again (Lambda and remaining resources will succeed)

## Related

- [Terraform implementation](https://github.com/CharlesSieg/tf-config-lambda-cicd)
- [Architecture article](https://charlessieg.com/articles/aws-lambda-container-cicd-pipeline-architecture.html)
