AWSLearning playground combining infrastructure and application code for the Person service.

## Directories

- `infra/` – AWS CDK app that provisions DynamoDB, SQS, the stream-processing Lambda, the API Gateway + Lambda web service for Person CRUD, and the deployment pipeline.
- `fastapi_service/` – Optional FastAPI REST service that reads/writes Person records to DynamoDB.

See the README in each directory for setup and deployment instructions.

## CI/CD pipeline (AWS CodePipeline + CodeBuild)

- Provisioned via CDK in `AwsLearningPipelineStack`.
- Uses a CodeStar Connections source (GitHub) feeding a CodeBuild project that runs `cdk synth` and `cdk deploy AwsLearningStack`.
- Requires environment variables during `cdk deploy` of the pipeline stack:
  - `CODESTAR_CONNECTION_ARN` – ARN of the pre-created CodeStar Connections connection to your repository.
  - `REPO_OWNER`, `REPO_NAME`, and optional `REPO_BRANCH` (default `main`) describing the repository to monitor.
- Ensure the target AWS account/region are bootstrapped with `cdk bootstrap`. The pipeline assumes permissions to deploy infrastructure (broad IAM permissions are granted to CodeBuild by default—tighten as needed).
- After the pipeline stack is deployed, pushes to the configured branch trigger automatic builds and deployments.
