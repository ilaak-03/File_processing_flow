#!/bin/bash
set -e

ENV=$1
source ../env/${ENV}-env.sh

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
