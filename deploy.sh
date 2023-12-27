#!/bin/bash

# Source common script
source "$(dirname '$0')/common.sh"

# Variables needed for this script
GITHUB_OWNER="Omni-Logistics"
GITHUB_REPO="pricing-algorithm"
REQUIRE_PROD_DEPLOYMENT_APPROVAL="true"
TECHNICAL_CONTACT="tgilbertson@omnilogistics.com"
NOTIFY_ON_EVENTS="tgilbertson@omnilogistics.com"

########## NOTHING TO CHANGE BELOW THIS LINE ##########

# Required parameters & Usage
if [ -z "$1" ]; then
  echo "Usage: $0 <branch>"
  echo "Example: $0 master"
  exit 1
fi

# Save parameters
GITHUB_BRANCH="$1"

# Based on branch, this is either CI or CI/CD
if [ "${GITHUB_BRANCH}" != "master" ]; then
  PIPELINE_IAC="ci.yaml"
else
  PIPELINE_IAC="cicd.yaml"
fi

# Common function to deploy a CloudFormation template
function deployTemplate {
  local PROFILE="$1"; shift;
  local REGION="$1"; shift;
  local STACK_NAME="$1"; shift;
  local TEMPLATE_NAME="$1"; shift;
  local CAPABILITIES="$1"; shift;
  local PARAMETER_OVERRIDES="$*"

  CMD="aws --profile '${PROFILE}' --region '${REGION}' cloudformation deploy --stack-name '${STACK_NAME}' --template-file '${TEMPLATE_NAME}' --capabilities '${CAPABILITIES}'"
  if [ -n "${PARAMETER_OVERRIDES}" ]; then
    CMD="${CMD} --parameter-overrides ${PARAMETER_OVERRIDES}"
  fi
  echo "================================================================================"
  echo "Deploying ${STACK_NAME} to ${PROFILE}:${REGION} ..."
  echo "${CMD}"
  eval ${CMD}
  if [ $? -ne 0 ]; then
    echo "Error deploying CloudFormation template, halting."
    exit 1
  fi
  echo "================================================================================"
}

# Common function to wait for a CloudFormation template to complete
function waitForCFCompletion {
  local PROFILE="$1"
  local REGION="$2"
  local STACK_NAME="$3"
  local TIMEOUT="$4"

  # Wait for CloudFormation stack to be in a completion state
  CODE=2
  TIMEOUT_TIME=$(( $(date +%s) + ${TIMEOUT} ))
  while [ $(date +%s) -lt ${TIMEOUT_TIME} ]; do
    local STACK_STATUS=$(aws --profile "${PROFILE}" --region "${REGION}" cloudformation describe-stacks --stack-name ${STACK_NAME} --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
    if [ "${STACK_STATUS}" != "CREATE_COMPLETE" ] &&
        [ "${STACK_STATUS}" != "CREATE_FAILED" ] &&
        [ "${STACK_STATUS}" != "ROLLBACK_COMPLETE" ] &&
        [ "${STACK_STATUS}" != "ROLLBACK_FAILED" ] &&
        [ "${STACK_STATUS}" != "UPDATE_COMPLETE" ] &&
        [ "${STACK_STATUS}" != "UPDATE_FAILED" ] &&
        [ "${STACK_STATUS}" != "UPDATE_ROLLBACK_COMPLETE" ] &&
        [ "${STACK_STATUS}" != "UPDATE_ROLLBACK_FAILED" ]; then
      echo "  Pending stack ${STACK_NAME} completion, status is ${STACK_STATUS:-DOES_NOT_EXIST}"
      sleep 5
    else
      echo "  Stack ${STACK_NAME} completed, status is ${STACK_STATUS}"
      if [ "${STACK_STATUS}" = "CREATE_COMPLETE" ] ||
          [ "${STACK_STATUS}" = "UPDATE_COMPLETE" ]; then
        # Success
        CODE=0
      else
        # Failure
        CODE=1
      fi
      break
    fi
  done

  # Did we timeout
  if [ ${CODE} -eq 2 ]; then
    echo "Timed out waiting for stack ${STACK_NAME} to complete"
  fi

  # Return our status (success=0, failure=1, timeout=2)
  return ${CODE}
}

# Common function to look up a value from a CloudFormation stack output
function lookupValue {
  local PROFILE="$1"
  local REGION="$2"
  local STACK_NAME="$3"
  local PARAM_NAME="$4"

  aws --profile "${PROFILE}" --region "${REGION}" cloudformation describe-stacks --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='${PARAM_NAME}'].OutputValue" --output text
}

# Deploy pre-req deployer roles to Dev & Prod accounts
STACK_NAME="${APPLICATION}-codepipelinerole-${GITHUB_BRANCH}"
deployTemplate "${DEV_AWS_PROFILE}"  "${AWS_REGION}" "${STACK_NAME}-dev"  "prerequisites/deployer-roles.yaml" "CAPABILITY_NAMED_IAM" Application="${APPLICATION}" Environment="dev"  GitHubBranch="${GITHUB_BRANCH}" ToolsAccount="${TOOLS_AWS_ACCOUNT_ID}" TechnicalContact="${TECHNICAL_CONTACT}"
deployTemplate "${PROD_AWS_PROFILE}" "${AWS_REGION}" "${STACK_NAME}-prod" "prerequisites/deployer-roles.yaml" "CAPABILITY_NAMED_IAM" Application="${APPLICATION}" Environment="prod" GitHubBranch="${GITHUB_BRANCH}" ToolsAccount="${TOOLS_AWS_ACCOUNT_ID}" TechnicalContact="${TECHNICAL_CONTACT}"

# Deploy the infrastructure for pricing algorithm serverless application
DEPLOYABLE_UNIT="pricing-algorithm"
STACK_NAME="${APPLICATION}-${DEPLOYABLE_UNIT}-${GITHUB_BRANCH}"
deployTemplate "${TOOLS_AWS_PROFILE}" "${AWS_REGION}" "${STACK_NAME}-pipeline" "${DEPLOYABLE_UNIT}/${PIPELINE_IAC}" "CAPABILITY_NAMED_IAM" Application="${APPLICATION}" DeployableUnitName="${DEPLOYABLE_UNIT}" GitHubOwner="${GITHUB_OWNER}" GitHubRepo="${GITHUB_REPO}" GitHubBranch="${GITHUB_BRANCH}" ManualApproval="${REQUIRE_PROD_DEPLOYMENT_APPROVAL}" TechnicalContact="${TECHNICAL_CONTACT}" NotifyOnEvents="${NOTIFY_ON_EVENTS}" DevAccount="${DEV_AWS_ACCOUNT_ID}" ProdAccount="${PROD_AWS_ACCOUNT_ID}"
