# ⚠️ Local-only helper. CI/CD deploys this stack in real environments.

#!/bin/bash
set -e

ENV=$1
source ../env/${ENV}-env.sh

sam build -t resources.yaml

sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name file-flow-resources-${ENV} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-south-1 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset
