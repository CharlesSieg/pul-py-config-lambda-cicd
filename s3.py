import pulumi_aws as aws


def create_artifact_bucket(config):
    """Create an S3 bucket for pipeline artifacts."""
    name_prefix = config["name_prefix"]

    # Artifact bucket with versioning and encryption
    bucket = aws.s3.BucketV2(
        "pipeline-artifacts-bucket",
        bucket=f"{name_prefix}-pipeline-artifacts",
        tags=config["common_tags"],
    )

    # Enable versioning
    aws.s3.BucketVersioningV2(
        "pipeline-artifacts-versioning",
        bucket=bucket.id,
        versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
            status="Enabled",
        ),
    )

    # Enable server-side encryption (AES256)
    aws.s3.BucketServerSideEncryptionConfigurationV2(
        "pipeline-artifacts-encryption",
        bucket=bucket.id,
        rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="aws:kms",
            ),
        )],
    )

    # Block all public access
    aws.s3.BucketPublicAccessBlock(
        "pipeline-artifacts-public-access-block",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    return bucket
