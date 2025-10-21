# AWSLearning Infrastructure (AWS CDK)

This CDK application provisions the backend infrastructure for the Person service.

## Stack overview

- DynamoDB table `Person` with primary key `name` and on-demand capacity. DynamoDB Streams (`NEW_AND_OLD_IMAGES`) are enabled.
- SQS queue `person_stream` that receives Person item events.
- AWS Lambda function `PersonStreamPublisher` subscribed to the DynamoDB stream and forwarding new items to the SQS queue.
- AWS Lambda function `PersonApiFunction` exposed through API Gateway (`/person` POST, `/person/{name}` GET). The API URL is emitted as a CloudFormation output `PersonApiUrl`.
- CodePipeline + CodeBuild deployment pipeline (`AwsLearningPipelineStack`) that watches your repository and runs `cdk deploy` automatically.

## Usage

```bash
cd AWSLearning/infra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Bootstrap (only once per account/region):

```bash
cdk bootstrap
```

Synthesize or deploy:

```bash
cdk synth
cdk deploy
```

The stack name defaults to `AwsLearningStack`. Adjust `app.py` if you need a different name or environment.

## Deploying the pipeline stack

Set the following environment variables before running `cdk deploy AwsLearningPipelineStack`:

- `CODESTAR_CONNECTION_ARN`: ARN of the pre-created CodeStar Connections connection (e.g. GitHub or Bitbucket).
- `REPO_OWNER`: Repository owner/organization.
- `REPO_NAME`: Repository name.
- `REPO_BRANCH`: (Optional) branch to monitor; defaults to `main`.

Deploy:

```bash
export CODESTAR_CONNECTION_ARN=arn:aws:codestar-connections:...
export REPO_OWNER=my-github-user
export REPO_NAME=AWSLearning
# export REPO_BRANCH=main
cdk deploy AwsLearningPipelineStack
```

The CodeBuild project runs `cdk synth` and `cdk deploy AwsLearningStack --require-approval never`. Ensure the target AWS account/region is bootstrapped and that the CodeStar connection has access to the repository. Tighten the IAM permissions granted to the CodeBuild role as needed.
