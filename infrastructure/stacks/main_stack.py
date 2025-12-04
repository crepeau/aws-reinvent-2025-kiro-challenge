from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
import os


class MainStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table for Events
        events_table = dynamodb.Table(
            self,
            "EventsTable",
            partition_key=dynamodb.Attribute(
                name="eventId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # For dev/test - use RETAIN in production
            point_in_time_recovery=True,
        )

        # Lambda Function with bundled dependencies
        api_lambda = _lambda.Function(
            self,
            "EventsAPIFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.handler",
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset(
                "../backend",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    platform="linux/amd64",
                    command=[
                        "bash", "-c",
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                )
            ),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DYNAMODB_TABLE_NAME": events_table.table_name,
                "ALLOWED_ORIGINS": "*",  # Configure for production
            },
        )

        # Grant DynamoDB permissions to Lambda
        events_table.grant_read_write_data(api_lambda)

        # API Gateway
        api = apigw.LambdaRestApi(
            self,
            "EventsAPI",
            handler=api_lambda,
            proxy=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["*"],
            ),
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200,
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "APIEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
        )

        CfnOutput(
            self,
            "DynamoDBTableName",
            value=events_table.table_name,
            description="DynamoDB table name",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=api_lambda.function_name,
            description="Lambda function name",
        )
