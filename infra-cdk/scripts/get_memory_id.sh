#!/bin/bash
# Get Memory ID from deployed stack
#
# Usage: ./get_memory_id.sh [stack-name-base]

STACK_NAME_BASE=${1:-"fullstack-agentcore-solution-template"}
STACK_NAME="${STACK_NAME_BASE}-BackendStack"

echo "Getting Memory ID from stack: $STACK_NAME"

# Get the Memory resource from CloudFormation
MEMORY_ID=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query "StackResources[?ResourceType=='AWS::BedrockAgentCore::Memory'].PhysicalResourceId" \
    --output text)

if [ -z "$MEMORY_ID" ]; then
    echo "Error: Could not find Memory ID in stack $STACK_NAME"
    exit 1
fi

echo "Memory ID: $MEMORY_ID"
echo ""
echo "To run validation script:"
echo "python infra-cdk/scripts/validate_memory_api.py --memory-id $MEMORY_ID --region us-east-1"
