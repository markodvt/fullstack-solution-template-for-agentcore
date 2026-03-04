# Phase 4: Memory Visualization - Deployment & Testing Guide

## Overview

This guide covers deploying and testing the Memory API backend implementation for Phase 4 of the enhanced-agent-ui feature.

## Prerequisites

- AWS CLI configured with appropriate credentials
- CDK CLI installed: `npm install -g aws-cdk`
- Node.js 18+
- Python 3.13+
- Deployed Cognito stack (from previous phases)

## Step 1: Build and Deploy CDK Stack

### 1.1 Navigate to infra-cdk directory

```bash
cd infra-cdk
```

### 1.2 Install dependencies (if not already done)

```bash
npm install
```

### 1.3 Build TypeScript

```bash
npm run build
```

### 1.4 Review changes before deployment

```bash
npx cdk diff
```

Expected changes:
- New Lambda function: `{stack-name}-memory`
- New IAM role and policies for Memory Lambda
- New API Gateway resource: `/memory`
- New SSM parameter: `/{stack-name}/memory-api-url`
- New CloudWatch log group: `/aws/lambda/{stack-name}-memory`

### 1.5 Deploy the stack

```bash
npx cdk deploy --all
```

This will:
1. Create the Memory Lambda function
2. Grant permissions to access AgentCore Memory
3. Add `/memory` endpoint to API Gateway
4. Configure Cognito authorizer
5. Store API URL in SSM

## Step 2: Verify Deployment

### 2.1 Check Lambda function exists

```bash
aws lambda get-function --function-name {stack-name}-memory
```

### 2.2 Check API Gateway endpoint

```bash
aws ssm get-parameter --name "/{stack-name}/memory-api-url" --query "Parameter.Value" --output text
```

### 2.3 Check CloudWatch logs

```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/{stack-name}-memory"
```

## Step 3: Get Authentication Token

You need a valid JWT token from Cognito to test the API.

### 3.1 Use the existing test script

```bash
cd infra-cdk/scripts
python test_get_cognito_token.py
```

This will output a JWT token. Copy it for use in API testing.

### 3.2 Alternative: Manual authentication

If the script doesn't work, authenticate via the frontend and extract the token from browser developer tools (Application > Local Storage > `CognitoIdentityServiceProvider`).

## Step 4: Test Memory API

### 4.1 Get API URL

```bash
API_URL=$(aws ssm get-parameter --name "/{stack-name}/memory-api-url" --query "Parameter.Value" --output text)
echo "Memory API URL: $API_URL"
```

### 4.2 Test basic request (no filters)

```bash
curl -X GET "$API_URL" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "memories": [],
  "count": 0,
  "nextToken": null
}
```

Note: Empty response is expected if no memories exist yet. This is NOT an error.

### 4.3 Test with agent name filter

```bash
curl -X GET "$API_URL?agentName=default" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 4.4 Test with user ID filter

```bash
curl -X GET "$API_URL?userId=test-user" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 4.5 Test with sort order

```bash
curl -X GET "$API_URL?sortOrder=asc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 4.6 Test with pagination limit

```bash
curl -X GET "$API_URL?limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

## Step 5: Test Error Handling

### 5.1 Test missing authentication (401)

```bash
curl -X GET "$API_URL" \
  -H "Content-Type: application/json"
```

Expected: 401 Unauthorized

### 5.2 Test invalid token (401)

```bash
curl -X GET "$API_URL" \
  -H "Authorization: Bearer invalid-token" \
  -H "Content-Type: application/json"
```

Expected: 401 Unauthorized

### 5.3 Test invalid parameter (400)

```bash
curl -X GET "$API_URL?limit=invalid" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

Expected: 400 Bad Request

## Step 6: Validate Memory API Response Schema

### 6.1 Get Memory ID

```bash
cd infra-cdk/scripts
./get_memory_id.sh
```

### 6.2 Run validation script

```bash
python validate_memory_api.py \
  --memory-id YOUR_MEMORY_ID \
  --region us-east-1 \
  --actor-id YOUR_USER_ID
```

This will:
- Test ListEvents API
- Test RetrieveMemoryRecords for all memory strategies
- Document actual response schemas
- Save results to `memory_api_validation_results.json`

### 6.3 Review validation results

```bash
cat memory_api_validation_results.json
```

Compare the actual response schemas with the documented schemas in `infra-cdk/lambdas/memory/MEMORY_API_SCHEMAS.md`.

## Step 7: Check CloudWatch Logs

### 7.1 View recent logs

```bash
aws logs tail /aws/lambda/{stack-name}-memory --follow
```

### 7.2 Search for errors

```bash
aws logs filter-log-events \
  --log-group-name "/aws/lambda/{stack-name}-memory" \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

## Step 8: Create Test Memories (Optional)

To test with actual data, you need to create some memories by chatting with agents.

### 8.1 Use the frontend chat interface

1. Navigate to the frontend application
2. Select an agent
3. Have a conversation
4. Memories will be automatically created by the agent

### 8.2 Verify memories were created

```bash
curl -X GET "$API_URL" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

You should now see memories in the response.

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Invalid or expired JWT token

**Solution**: 
1. Get a fresh token using `test_get_cognito_token.py`
2. Verify token is not expired (tokens typically expire after 1 hour)
3. Check Cognito User Pool configuration

### Issue: 500 Internal Server Error

**Cause**: Lambda execution error

**Solution**:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/{stack-name}-memory --follow`
2. Look for Python exceptions or stack traces
3. Verify MEMORY_ID environment variable is set
4. Verify IAM permissions are correct

### Issue: Empty response but expecting data

**Cause**: No memories exist for the user, or filtering is too restrictive

**Solution**:
1. Create test memories by chatting with agents
2. Verify user ID in JWT matches the actor ID used in conversations
3. Remove filters to see all memories
4. Check Memory API validation results to confirm memory strategies are working

### Issue: CORS errors in browser

**Cause**: Frontend origin not in CORS_ALLOWED_ORIGINS

**Solution**:
1. Check Lambda environment variables
2. Verify frontend URL is included in CORS_ALLOWED_ORIGINS
3. Redeploy if needed

### Issue: Memory ID not found

**Cause**: Shared resources not initialized or deployment order issue

**Solution**:
1. Verify multi-agent pattern is being used (single-agent patterns may not create shared resources)
2. Check CDK deployment logs for errors
3. Verify Memory resource was created in CloudFormation

## Next Steps

After successful deployment and testing:

1. ✅ Mark task 14.3 as complete
2. ✅ Move to task 15: Memory Page (Frontend)
3. ✅ Implement Memory service layer
4. ✅ Create Memory page components
5. ✅ Test end-to-end memory visualization

## Reference

- Memory API Lambda: `infra-cdk/lambdas/memory/index.py`
- CDK Stack: `infra-cdk/lib/backend-stack.ts` (createMemoryApi method)
- API Schemas: `infra-cdk/lambdas/memory/MEMORY_API_SCHEMAS.md`
- Memory Integration Guide: `docs/MEMORY_INTEGRATION.md`
