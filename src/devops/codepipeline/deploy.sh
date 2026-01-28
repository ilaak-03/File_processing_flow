#!/bin/bash
set -e

# First argument: environment
ENV=$1

# Load environment variables
source ../env/${ENV}-env.sh

# Deploy the CodePipeline stack
aws cloudformation deploy \
  --template-file pipeline.yaml \
  --stack-name file-flow-pipeline-${ENV} \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      GitHubOwner=$GITHUB_OWNER \
      GitHubRepo=$GITHUB_REPO \
      GitHubBranch=$GITHUB_BRANCH \
      CodeStarConnectionArn=$CODESTAR_ARN \
      ArtifactBucketName=$ARTIFACT_BUCKET \
      Environment=$ENV \
      AWSAccountId=$AWS_ACCOUNT_ID
