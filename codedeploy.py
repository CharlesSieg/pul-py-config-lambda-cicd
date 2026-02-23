import pulumi_aws as aws


def create_codedeploy(config, lambda_function, lambda_alias, error_alarm, codedeploy_role):
    """Create a CodeDeploy application and deployment group for Lambda canary deployments."""
    name_prefix = config["name_prefix"]

    # CodeDeploy application for Lambda
    app = aws.codedeploy.Application(
        "codedeploy-app",
        name=f"{name_prefix}-lambda-deploy",
        compute_platform="Lambda",
        tags=config["common_tags"],
    )

    # Deployment group with canary traffic shifting and alarm-based rollback
    deployment_group = aws.codedeploy.DeploymentGroup(
        "codedeploy-deployment-group",
        app_name=app.name,
        deployment_group_name=f"{name_prefix}-lambda-dg",
        service_role_arn=codedeploy_role.arn,
        deployment_config_name="CodeDeployDefault.LambdaCanary10Percent5Minutes",
        deployment_style=aws.codedeploy.DeploymentGroupDeploymentStyleArgs(
            deployment_type="BLUE_GREEN",
            deployment_option="WITH_TRAFFIC_CONTROL",
        ),
        auto_rollback_configuration=aws.codedeploy.DeploymentGroupAutoRollbackConfigurationArgs(
            enabled=True,
            events=[
                "DEPLOYMENT_FAILURE",
                "DEPLOYMENT_STOP_ON_ALARM",
            ],
        ),
        alarm_configuration=aws.codedeploy.DeploymentGroupAlarmConfigurationArgs(
            alarms=[error_alarm.alarm_name],
            enabled=True,
        ),
        tags=config["common_tags"],
    )

    return app, deployment_group
