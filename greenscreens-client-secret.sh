#!/bin/bash
################################################################################
# This script is used to provide a simple, command-line way to view or update
# the password used for Greenscreens api.
################################################################################

# Source common script
source "$(dirname '$0')/common.sh"

# Required parameters & Usage
if [ -z "$1" ]; then
  echo "Usage: $0 <environment> [secret]"
  echo "Where: environment = dev or prod"
  echo "       secret = update secret, if provided, otherwise view secret"
  exit 1
fi

# Save parameters
ENV="$1"
SECRET="$2"

# Variables needed for this script
PARAM_NAME="/app/${APPLICATION}/${ENV}/pricing-algorithm/greenscreens-secret"

# Set appropriate AWS profile based on environment
if [ "${ENV}" = "prod" ]; then
  AWS_PROFILE="${PROD_AWS_PROFILE}"
else
  AWS_PROFILE="${DEV_AWS_PROFILE}"
fi

# Get the secret, if it exists
VALUE=$(aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" ssm get-parameter --name "${PARAM_NAME}" --with-decryption --query "Parameter.Value" --output text 2>/dev/null)

# Did we find a secret?
if [ -n "${VALUE}" ]; then
  # Secret exists, do we want to view or update it?
  if [ -n "${SECRET}" ]; then
    # Update the secret
    aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" ssm put-parameter --name "${PARAM_NAME}" --value "${SECRET}" --type SecureString --overwrite
  else
    # View secret
    echo "${VALUE}"
  fi
else
  echo "The Greenscreens secret does not yet exist in Parameter Store, you need to run the deploy.sh script."
  exit 1
fi