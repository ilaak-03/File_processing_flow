#!/bin/bash
set -e

ENV=$1
source ../env/${ENV}-env.sh

aws cloudformation deploy \
  --template-file resources.yaml \
  --stack-name file-flow-resources-${ENV} \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      Environment=$ENV
