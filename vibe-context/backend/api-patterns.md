---
inclusion: fileMatch
fileMatchPattern: 'infra-cdk/lambdas/'
---

# Backend API Patterns and Deployment Configuration

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

This document captures patterns for adding backend APIs and managing deployment configuration in the FAST project. Following these patterns ensures consistency and proper integration between infrastructure, backend services, and frontend.

## Backend API Integration Pattern

### Step 1: Create the Lambda Function

**Location:** `infra-cdk/lambdas/{api-name}/index.py`

Create a new directory under `infra-cdk/lambdas/` with your API name and implement the Lambda handler.

**Example:**
```python
import json
import boto3
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for {api-name} API.
    
    Args:
        event: API Gateway event with body, headers, etc.
        context: Lambda context
        
    Returns:
        API Gateway response with statusCode, body, headers
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        
        # Business logic here
        result = process_request(body)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps(result)
        }
    except Exception as e:
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
```

**Key Points:**
- Always include CORS headers in responses
- Use proper error handling with appropriate status codes
- Parse and validate input
- Return JSON responses

### Step 2: Define Lambda in CDK

**Location:** `infra-cdk/lib/backend-stack.ts`

Add Lambda function definition:

```typescript
const myApiLambda = new lambda.Function(this, 'MyApiFunction', {
  runtime: lambda.Runtime.PYTHON_3_12,
  handler: 'index.lambda_handler',
  code: lambda.Code.fromAsset('lambdas/my-api'),
  environment: {
    REGION: this.region,
    // Add other environment variables
  },
  timeout: cdk.Duration.seconds(30),
});

// Grant permissions if needed
myTable.grantReadWriteData(myApiLambda);
```

### Step 3: Add API Gateway Route

Add route to API Gateway:

```typescript
const myApiIntegration = new apigateway.LambdaIntegration(myApiLambda);

api.root.addResource('my-api').addMethod('POST', myApiIntegration, {
  authorizer: cognitoAuthorizer,
  authorizationType: apigateway.AuthorizationType.COGNITO,
});
```

### Step 4: Export API Configuration

Add endpoint to SSM Parameter Store for frontend discovery:

```typescript
new ssm.StringParameter(this, 'MyApiEndpoint', {
  parameterName: `/fast/${deploymentName}/api/my-api-endpoint`,
  stringValue: `${api.url}my-api`,
});
```

### Step 5: Update Frontend Configuration

The deployment script automatically generates `frontend/public/aws-exports.json` from SSM parameters. Ensure your parameter follows the naming convention: `/fast/${deploymentName}/api/{api-name}-endpoint`

---

## Configuration Storage Patterns

### SSM Parameter Store Pattern

**Naming Convention:**
```
/fast/${deploymentName}/api/{api-name}-endpoint
/fast/${deploymentName}/config/{config-name}
/fast/${deploymentName}/agent/{agent-id}/metadata
```

**CDK Example:**
```typescript
new ssm.StringParameter(this, 'ConfigParam', {
  parameterName: `/fast/${deploymentName}/config/feature-flag`,
  stringValue: 'enabled',
});
```

**Lambda Retrieval:**
```python
import boto3

ssm = boto3.client('ssm')
response = ssm.get_parameter(Name='/fast/dev/config/feature-flag')
value = response['Parameter']['Value']
```

---

## Agent Metadata Storage Pattern

Store agent metadata in SSM for frontend discovery:

```typescript
const agentMetadata = {
  agentId: agent.agentId,
  agentName: 'My Agent',
  description: 'Agent description',
  category: 'general',
};

new ssm.StringParameter(this, 'AgentMetadata', {
  parameterName: `/fast/${deploymentName}/agent/${agent.agentId}/metadata`,
  stringValue: JSON.stringify(agentMetadata),
});
```

---

## Deployment Workflow

1. **Develop Lambda locally** - Test with unit tests
2. **Add Lambda to CDK** - Define in backend-stack.ts
3. **Add API Gateway route** - Wire up integration
4. **Export configuration** - Add SSM parameters
5. **Deploy CDK** - `npx cdk deploy`
6. **Frontend auto-discovers** - Reads aws-exports.json

---

## Common Patterns

### ✅ DO:
- Include CORS headers in all Lambda responses
- Use Cognito authorizer for authenticated endpoints
- Store configuration in SSM Parameter Store
- Follow naming conventions for SSM parameters
- Add proper error handling and logging
- Use environment variables for configuration

### ❌ DON'T:
- Hardcode API endpoints in frontend
- Skip CORS headers (causes browser errors)
- Store secrets in code (use Secrets Manager)
- Forget to grant Lambda permissions to AWS resources
- Use overly permissive IAM policies

---

## Troubleshooting

**CORS Errors:**
- Ensure Lambda returns CORS headers in ALL responses (success and error)
- Check API Gateway CORS configuration
- Verify OPTIONS method is configured

**404 Errors:**
- Check API Gateway route is deployed
- Verify endpoint URL in aws-exports.json
- Ensure SSM parameter name follows convention

**401/403 Errors:**
- Verify Cognito authorizer is configured
- Check JWT token is included in request headers
- Ensure user has proper permissions

**424 Errors:**
- Check Lambda CloudWatch logs for startup failures
- Verify Lambda has required permissions
- Check environment variables are set correctly

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
