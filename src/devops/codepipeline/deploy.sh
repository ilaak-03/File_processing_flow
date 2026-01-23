#!/bin/bash
set -e

ENV=$1
source devops/env/${ENV}-env.sh

aws cloudformation deploy \
  --template-file devops/codepipeline/pipeline.yaml \
  --stack-name file-processing-pipeline-${ENV} \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOwner=$GITHUB_OWNER \
    GitHubRepo=$GITHUB_REPO \
    GitHubBranch=$GITHUB_BRANCH \
    CodeStarConnectionArn=$CODESTAR_ARN \
    ArtifactBucketName=$ARTIFACT_BUCKET \
    Environment=$ENV
