import pulumi


def get_config():
    """Read Pulumi configuration with sensible defaults."""
    cfg = pulumi.Config()
    aws_cfg = pulumi.Config("aws")

    project_name = cfg.require("project_name")
    environment = cfg.get("environment") or "dev"
    region = aws_cfg.get("region") or "us-east-1"

    name_prefix = f"{project_name}-{environment}"

    return {
        "project_name": project_name,
        "environment": environment,
        "region": region,
        "name_prefix": name_prefix,
        "github_repo_owner": cfg.require("github_repo_owner"),
        "github_repo_name": cfg.require("github_repo_name"),
        "github_branch": cfg.get("github_branch") or "main",
        "lambda_memory_size": cfg.get_int("lambda_memory_size") or 256,
        "lambda_timeout": cfg.get_int("lambda_timeout") or 30,
        "lambda_architecture": cfg.get("lambda_architecture") or "x86_64",
        "common_tags": {
            "Project": project_name,
            "Environment": environment,
            "ManagedBy": "pulumi",
        },
    }
