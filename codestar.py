import pulumi_aws as aws


def create_codestar_connection(config):
    """Create a CodeStar Connection for GitHub integration."""
    name_prefix = config["name_prefix"]

    connection = aws.codestarconnections.Connection(
        "github-connection",
        name=f"{name_prefix}-github",
        provider_type="GitHub",
        tags=config["common_tags"],
    )

    return connection
