#!/usr/bin/env python3
import os

from typing import Optional

import aws_cdk as cdk

from aws_learning_infra.aws_learning_pipeline_stack import AwsLearningPipelineStack
from aws_learning_infra.aws_learning_stack import AwsLearningStack


def main() -> None:
    app = cdk.App()

    account = os.getenv("CDK_DEFAULT_ACCOUNT")
    region = os.getenv("CDK_DEFAULT_REGION")

    env = cdk.Environment(account=account, region=region)

    AwsLearningStack(
        app,
        "AwsLearningStack",
        env=env,
    )

    CODESTAR_CONNECTION_ARN = 'arn:aws:codeconnections:us-east-1:716542960961:connection/2259f377-12fe-4b22-bd45-5fe62f6eba45'
    REPO_OWNER = 'glocalsaint'
    REPO_NAME = 'AWSLearning'
    REPO_BRANCH = 'master'
    connection_arn: Optional[str] = CODESTAR_CONNECTION_ARN # os.getenv("CODESTAR_CONNECTION_ARN")
    repo_owner: Optional[str] = REPO_OWNER # os.getenv("REPO_OWNER")
    repo_name: Optional[str] = REPO_NAME # os.getenv("REPO_NAME")
    repo_branch: str = REPO_BRANCH # os.getenv("REPO_BRANCH", "main")

    if connection_arn and repo_owner and repo_name:
        AwsLearningPipelineStack(
            app,
            "AwsLearningPipelineStack",
            env=env,
            connection_arn=connection_arn,
            repo_owner=repo_owner,
            repo_name=repo_name,
            branch=repo_branch,
        )

    app.synth()


if __name__ == "__main__":
    main()
