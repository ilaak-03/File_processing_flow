#!/bin/bash
set -e

# ----------------------------
# Usage: ./deploy-resources.sh <env>
# Example: ./deploy-resources.sh dev
# ----------------------------

# First argument: environment
ENV=$1

# Load environment variables from your env file
source ../env/${ENV}-env.sh

# CloudFormation stack name
STACK_NAME="file-flow-resources-${ENV}"

# Local SAM template
TEMPLATE_FILE="resources.yaml"

# S3 bucket to store Lambda code and artifacts
# Make sure this bucket exists and your IAM role has access
PACKAGE_BUCKET=$ARTIFACT_BUCKET

echo "Packaging CloudFormation template..."
aws cloudformation package \
    --template-file $TEMPLATE_FILE \
    --s3-bucket $PACKAGE_BUCKET \
    --output-template-file packaged.yaml \
    --region ap-south-1

echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Environment=$ENV \
        ArtifactBucketName=$PACKAGE_BUCKET \
        AWSAccountId=$AWS_ACCOUNT_ID \
    --region ap-south-1

echo "Deployment of $STACK_NAME completed successfully!"
