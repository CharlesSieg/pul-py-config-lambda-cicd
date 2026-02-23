import pulumi_aws as aws


def create_cloudwatch_resources(config, lambda_function):
    """Create CloudWatch log group and error alarm for the Lambda function."""
    name_prefix = config["name_prefix"]

    # Log group for Lambda function logs
    log_group = aws.cloudwatch.LogGroup(
        "lambda-log-group",
        name=f"/aws/lambda/{name_prefix}-lambda",
        retention_in_days=14,
        tags=config["common_tags"],
    )

    # Error alarm — triggers CodeDeploy rollback when errors exceed threshold
    error_alarm = aws.cloudwatch.MetricAlarm(
        "lambda-error-alarm",
        alarm_name=f"{name_prefix}-lambda-errors",
        alarm_description=f"Lambda error alarm for {name_prefix}-lambda",
        namespace="AWS/Lambda",
        metric_name="Errors",
        dimensions={
            "FunctionName": lambda_function.function_name,
        },
        statistic="Sum",
        comparison_operator="GreaterThanThreshold",
        threshold=0,
        period=60,
        evaluation_periods=1,
        treat_missing_data="notBreaching",
        tags=config["common_tags"],
    )

    return log_group, error_alarm
