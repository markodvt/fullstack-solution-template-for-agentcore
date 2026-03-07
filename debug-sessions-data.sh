#!/bin/bash

# Script to invoke observability-sessions Lambda directly for debugging
# This bypasses the UI and shows raw data returned by the Lambda

set -e

echo "=== Observability Sessions Lambda Debug Script ==="
echo ""

# Find the Lambda function name
echo "Finding Lambda function..."
FUNCTION_NAME=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'observability-sessions')].FunctionName" --output text)

if [ -z "$FUNCTION_NAME" ]; then
    echo "ERROR: Could not find Lambda function containing 'observability-sessions'"
    echo "Available functions:"
    aws lambda list-functions --query "Functions[].FunctionName" --output text
    exit 1
fi

echo "Found Lambda: $FUNCTION_NAME"
echo ""

# Calculate time range (last 7 days in milliseconds)
END_TIME=$(date +%s)000
START_TIME=$((END_TIME - 604800000))

echo "Time range:"
echo "  Start: $(date -r $((START_TIME / 1000)) '+%Y-%m-%d %H:%M:%S')"
echo "  End:   $(date -r $((END_TIME / 1000)) '+%Y-%m-%d %H:%M:%S')"
echo ""

# Create test payload simulating API Gateway event
# Note: JWT auth will fail, but we can still see the data structure
cat > /tmp/lambda-test-payload.json <<EOF
{
  "httpMethod": "GET",
  "headers": {
    "origin": "http://localhost:3000",
    "Authorization": "Bearer mock-token-for-testing"
  },
  "requestContext": {
    "authorizer": {
      "claims": {
        "sub": "test-user-id",
        "cognito:username": "test-user"
      }
    }
  },
  "queryStringParameters": {
    "startTime": "$START_TIME",
    "endTime": "$END_TIME",
    "limit": "100"
  }
}
EOF

echo "Test payload created (no agentName filter - will return ALL sessions)"
echo ""

# Invoke Lambda
echo "Invoking Lambda function..."
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload file:///tmp/lambda-test-payload.json \
    --cli-binary-format raw-in-base64-out \
    debug-sessions-output.json

echo ""
echo "=== Raw Lambda Response ==="
cat debug-sessions-output.json
echo ""
echo ""

# Pretty-print the JSON
echo "=== Pretty-Printed Response ==="
cat debug-sessions-output.json | jq '.'
echo ""

# Extract and display agent names if successful
if cat debug-sessions-output.json | jq -e '.statusCode == 200' > /dev/null 2>&1; then
    echo "=== Session Summary ==="
    
    # Parse the body (it's a JSON string inside the response)
    BODY=$(cat debug-sessions-output.json | jq -r '.body')
    
    # Count sessions
    SESSION_COUNT=$(echo "$BODY" | jq '.count')
    echo "Total sessions returned: $SESSION_COUNT"
    echo ""
    
    # Extract unique agent names
    echo "Unique agent names in sessions:"
    echo "$BODY" | jq -r '.sessions[].agentName' | sort | uniq -c
    echo ""
    
    # Show agent name to display name mapping
    echo "Agent name to display name mapping:"
    echo "$BODY" | jq -r '.sessions[] | "\(.agentName) -> \(.agentDisplayName)"' | sort | uniq
    echo ""
    
    # Show first few sessions
    echo "First 5 sessions:"
    echo "$BODY" | jq '.sessions[:5] | .[] | {sessionId, agentName, agentDisplayName, startTime, status}'
else
    echo "ERROR: Lambda returned non-200 status"
    cat debug-sessions-output.json | jq '.statusCode, .body'
fi

echo ""
echo "=== Debug Complete ==="
echo "Full output saved to: debug-sessions-output.json"
echo "Test payload saved to: /tmp/lambda-test-payload.json"
