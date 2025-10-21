from aws_cdk import (
    Aws,
    Duration,
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cp_actions,
    aws_iam as iam,
)
from constructs import Construct


class AwsLearningPipelineStack(Stack):
    """CodePipeline + CodeBuild continuous deployment stack."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        connection_arn: str,
        repo_owner: str,
        repo_name: str,
        branch: str = "main",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not connection_arn:
            raise ValueError("connection_arn is required to create the pipeline")

        source_output = codepipeline.Artifact("SourceArtifact")

        pipeline = codepipeline.Pipeline(
            self,
            "AwsLearningPipeline",
            pipeline_name="AwsLearningPipeline",
            restart_execution_on_update=True,
        )

        source_action = cp_actions.CodeStarConnectionsSourceAction(
            action_name="Source",
            owner=repo_owner,
            repo=repo_name,
            branch=branch,
            connection_arn=connection_arn,
            output=source_output,
        )

        pipeline.add_stage(stage_name="Source", actions=[source_action])

        project = codebuild.PipelineProject(
            self,
            "AwsLearningBuildDeploy",
            project_name="AwsLearningBuildDeploy",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=False,
            ),
            environment_variables={
                "CDK_DEFAULT_ACCOUNT": codebuild.BuildEnvironmentVariable(value=Aws.ACCOUNT_ID),
                "CDK_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=Aws.REGION),
            },
            timeout=Duration.minutes(30),
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "runtime-versions": {"python": "3.11", "nodejs": "18"},
                            "commands": [
                                "npm install -g aws-cdk",
                                "python -m pip install --upgrade pip",
                                "pip install -r infra/requirements.txt",
                            ],
                        },
                        "build": {
                            "commands": [
                                "cd infra",
                                "cdk synth",
                                "cdk deploy AwsLearningStack --require-approval never",
                            ]
                        },
                    },
                    "artifacts": {
                        "files": [
                            "**/*",
                        ]
                    },
                }
            ),
        )

        project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:*",
                    "dynamodb:*",
                    "lambda:*",
                    "logs:*",
                    "sqs:*",
                    "apigateway:*",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:PassRole",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "sts:AssumeRole",
                    "codebuild:*",
                ],
                resources=["*"],
            )
        )

        build_action = cp_actions.CodeBuildAction(
            action_name="BuildAndDeploy",
            project=project,
            input=source_output,
        )

        pipeline.add_stage(stage_name="BuildDeploy", actions=[build_action])
