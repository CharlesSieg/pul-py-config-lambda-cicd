import pulumi
import pulumi_aws as aws


def create_lambda_function(config, ecr_repo, lambda_role):
    """Create a containerized Lambda function with a 'live' alias for traffic shifting."""
    name_prefix = config["name_prefix"]

    # Build the initial image URI from the ECR repo
    # On first deploy, there may be no image yet — see README bootstrap sequence
    image_uri = ecr_repo.repository_url.apply(lambda url: f"{url}:latest")

    # Lambda function using container image
    function = aws.lambda_.Function(
        "lambda-function",
        function_name=f"{name_prefix}-lambda",
        role=lambda_role.arn,
        package_type="Image",
        image_uri=image_uri,
        memory_size=config["lambda_memory_size"],
        timeout=config["lambda_timeout"],
        architectures=[config["lambda_architecture"]],
        publish=True,
        tags=config["common_tags"],
    )

    # Create the "live" alias pointing to the latest published version
    alias = aws.lambda_.Alias(
        "lambda-alias-live",
        name="live",
        function_name=function.function_name,
        function_version=function.version,
    )

    return function, alias
