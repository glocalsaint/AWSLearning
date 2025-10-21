from pathlib import Path

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_lambda_event_sources,
    aws_sqs as sqs,
)
from constructs import Construct


class AwsLearningStack(Stack):
    """Infrastructure stack provisioning Person resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = dynamodb.Table(
            self,
            "PersonTable",
            table_name="Person",
            partition_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=RemovalPolicy.DESTROY,
        )

        queue = sqs.Queue(
            self,
            "PersonStreamQueue",
            queue_name="person_stream",
        )

        lambda_dir = Path(__file__).resolve().parent / "lambda"

        publisher_function = _lambda.Function(
            self,
            "PersonStreamPublisher",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="person_stream_publisher.handler",
            code=_lambda.Code.from_asset(str(lambda_dir)),
            environment={
                "QUEUE_URL": queue.queue_url,
            },
        )

        api_function = _lambda.Function(
            self,
            "PersonApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="person_api.handler",
            code=_lambda.Code.from_asset(str(lambda_dir)),
            environment={
                "TABLE_NAME": table.table_name,
            },
        )

        table.grant_read_write_data(api_function)
        queue.grant_send_messages(publisher_function)
        table.grant_stream_read(publisher_function)

        publisher_function.add_event_source(
            aws_lambda_event_sources.DynamoEventSource(
                table,
                starting_position=_lambda.StartingPosition.TRIM_HORIZON,
                batch_size=10,
            )
        )

        api = apigateway.LambdaRestApi(
            self,
            "PersonServiceApi",
            handler=api_function,
            proxy=False,
            deploy_options=apigateway.StageOptions(stage_name="prod"),
        )

        person_resource = api.root.add_resource("person")
        person_resource.add_method("POST")

        person_item = person_resource.add_resource("{name}")
        person_item.add_method("GET")

        CfnOutput(
            self,
            "PersonApiUrl",
            value=api.url,
        )
