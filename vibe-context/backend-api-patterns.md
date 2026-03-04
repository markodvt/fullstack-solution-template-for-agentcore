# Backend API Patterns and Deployment Configuration

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

This document captures the patterns and best practices for adding backend APIs and managing deployment configuration in the FAST (Fullstack AgentCore Solution Template) project. Following these patterns ensures consistency, maintainability, and proper integration between infrastructure, backend services, and frontend applications.

## Table of Contents

1. [Backend API Integration Pattern](#backend-api-integration-pattern)
2. [Configuration Storage Patterns](#configuration-storage-patterns)
3. [Agent Metadata Storage Pattern](#agent-metadata-storage-pattern)
4. [Deployment Workflow](#deployment-workflow)
5. [Common Patterns and Anti-Patterns](#common-patterns-and-anti-patterns)
6. [Troubleshooting](#troubleshooting)
7. [Complete Example: Adding a New Backend API](#complete-example-adding-a-new-backend-api)

---

## Backend API Integration Pattern

When adding a new backend API endpoint to the FAST project, follow this complete integration pattern to ensure the API is accessible to the frontend and properly configured across all deployment stages.

### Step 1: Create the Lambda Function

**Location:** `infra-cdk/lambdas/{api-name}/index.py`

Create a new directory under `infra-cdk/lambdas/` with your API name and implement the Lambda handler.

**Best Practices:**
- Use AWS Lambda Powertools for Python for logging, tracing, and event handling
- Implement proper input validation using Pydantic models
- Use camelCase for API contracts (frontend) but snake_case internally (Python)
- Extract user identity from JWT tokens in the request context (never trust request body)
- Implement proper CORS handling with environment-based allowed origins
- Use structured error responses with appropriate HTTP status codes
- Add comprehensive logging for debugging and monitoring

**Example Structure:**
```python
# infra-cdk/lambdas/my-api/index.py
import os
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from pydantic import BaseModel, Field

# Environment variables
TABLE_NAME = os.environ["TABLE_NAME"]
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

# Configure CORS
cors_origins = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(",")]
cors_config = CORSConfig(
    allow_origin=cors_origins[0],
    extra_origins=cors_origins[1:] if len(cors_origins) > 1 else None,
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(cors=cors_config)

# Request/response models
class MyRequest(BaseModel):
    field1: str = Field(..., min_length=1, max_length=100)
    field2: str

@app.post("/my-endpoint")
def handle_request():
    # Extract user ID from JWT
    claims = app.current_event.request_context.authorizer.get("claims", {})
    user_id = claims.get("sub") or "unknown"
    
    # Validate and process request
    data = MyRequest(**app.current_event.json_body)
    # ... implementation
    
    return {"success": True}

def handler(event, context):
    return app.resolve(event, context)
```

### Step 2: Add Lambda to CDK Stack

**Location:** `infra-cdk/lib/backend-stack.ts`

Create a private method in `BackendStack` class to set up the Lambda function, API Gateway integration, IAM permissions, and SSM parameters.

**Pattern to Follow:**
1. Create Lambda function using `PythonFunction` construct
2. Grant necessary IAM permissions (DynamoDB, AgentCore, SSM, etc.)
3. Create or reuse API Gateway REST API
4. Add Cognito authorizer for authentication
5. Create API Gateway resource and method
6. Store API URL in SSM Parameter Store
7. Store API URL as public property for CloudFormation export

**Example Implementation:**
```typescript
// In backend-stack.ts

export class BackendStack extends cdk.NestedStack {
  public readonly feedbackApiUrl: string;
  public readonly memoryApiUrl: string;
  public readonly myNewApiUrl: string; // Add public property
  private api: apigateway.RestApi;
  
  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);
    
    // ... existing code ...
    
    // Create your new API
    this.createMyNewApi(props.config, props.frontendUrl);
  }
  
  private createMyNewApi(config: AppConfig, frontendUrl: string): void {
    // 1. Create Lambda function
    const myApiLambda = new PythonFunction(this, "MyApiLambda", {
      functionName: `${config.stack_name_base}-my-api`,
      runtime: lambda.Runtime.PYTHON_3_13,
      entry: path.join(__dirname, "..", "lambdas", "my-api"),
      handler: "handler",
      environment: {
        TABLE_NAME: myTable.tableName,
        CORS_ALLOWED_ORIGINS: `${frontendUrl},http://localhost:3000`,
      },
      timeout: cdk.Duration.seconds(30),
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          "MyApiPowertoolsLayer",
          `arn:aws:lambda:${cdk.Stack.of(this).region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-arm64:18`
        ),
      ],
      logGroup: new logs.LogGroup(this, "MyApiLambdaLogGroup", {
        logGroupName: `/aws/lambda/${config.stack_name_base}-my-api`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // 2. Grant IAM permissions
    myTable.grantReadWriteData(myApiLambda);
    
    myApiLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [`arn:aws:ssm:${this.region}:${this.account}:parameter/${config.stack_name_base}/*`],
      })
    );

    // 3. Create or reuse API Gateway (reuse existing this.api if available)
    // If this is your first API, create the API Gateway:
    // this.api = new apigateway.RestApi(this, "Api", { ... });
    
    // 4. Create Cognito authorizer
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(
      this,
      "MyApiAuthorizer",
      {
        cognitoUserPools: [this.userPool],
        identitySource: "method.request.header.Authorization",
        authorizerName: `${config.stack_name_base}-my-api-authorizer`,
      }
    );

    // 5. Add API Gateway resource and method
    const myApiResource = this.api.root.addResource("my-endpoint");
    myApiResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(myApiLambda),
      {
        authorizer,
        authorizationType: apigateway.AuthorizationType.COGNITO,
      }
    );

    // 6. Store API URL in SSM Parameter Store
    new ssm.StringParameter(this, "MyApiUrlParam", {
      parameterName: `/${config.stack_name_base}/my-api-url`,
      stringValue: `${this.api.url}my-endpoint`,
      description: "My API endpoint URL",
    });

    // 7. Store API URL as public property for CloudFormation export
    this.myNewApiUrl = `${this.api.url}my-endpoint`;
  }
}
```

**Why Each Step Matters:**
- **Lambda Function**: Implements the business logic with proper error handling and validation
- **IAM Permissions**: Follows principle of least privilege - only grant what's needed
- **API Gateway**: Provides HTTP endpoint with throttling, caching, and logging
- **Cognito Authorizer**: Ensures only authenticated users can access the API
- **SSM Parameter**: Makes URL available to other backend services and scripts
- **Public Property**: Enables CloudFormation export for deployment automation

### Step 3: Export API URL from Main Stack

**Location:** `infra-cdk/lib/fast-main-stack.ts`

Add a CloudFormation output in the main stack to export the API URL for use by deployment scripts.

**Example:**
```typescript
// In fast-main-stack.ts

export class FastMainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastAmplifyStackProps) {
    super(scope, id, props);
    
    // ... create nested stacks ...
    
    // Add output for your new API
    new cdk.CfnOutput(this, "MyNewApiUrl", {
      value: this.backendStack.myNewApiUrl,
      description: "My New API Gateway URL",
      exportName: `${props.config.stack_name_base}-MyNewApiUrl`,
    });
  }
}
```

**Why This Matters:**
- CloudFormation outputs are queryable via AWS CLI
- Deployment scripts use these outputs to generate frontend configuration
- Export names allow cross-stack references if needed

### Step 4: Add to Frontend Deployment Script

**Location:** `scripts/deploy-frontend.py`

Update the deployment script to fetch your new API URL and include it in `aws-exports.json`.

**Changes Required:**

1. **Add to required outputs list** (for validation):
```python
def generate_aws_exports(
    stack_name: str,
    outputs: Dict[str, str],
    region: str,
    pattern: str,
    frontend_dir: Path,
) -> None:
    required = [
        "CognitoClientId",
        "CognitoUserPoolId",
        "AmplifyUrl",
        "RuntimeArn",
        "FeedbackApiUrl",
        "MemoryApiUrl",
        "MyNewApiUrl",  # Add your new API here
    ]
```

2. **Add to aws-exports.json generation**:
```python
    aws_exports = {
        "authority": f"https://cognito-idp.{region}.amazonaws.com/{outputs['CognitoUserPoolId']}",
        "client_id": outputs["CognitoClientId"],
        "redirect_uri": outputs["AmplifyUrl"],
        "post_logout_redirect_uri": outputs["AmplifyUrl"],
        "response_type": "code",
        "scope": "email openid profile",
        "automaticSilentRenew": True,
        "agentRuntimeArn": outputs["RuntimeArn"],
        "awsRegion": region,
        "feedbackApiUrl": outputs["FeedbackApiUrl"],
        "memoryApiUrl": outputs["MemoryApiUrl"],
        "myNewApiUrl": outputs["MyNewApiUrl"],  # Add your new API here
        "agentPattern": pattern,
    }
```

**Why This Matters:**
- Frontend needs API URLs to make requests
- Configuration is generated dynamically from deployed infrastructure
- No hardcoded URLs means environment-agnostic deployments

### Step 5: Use in Frontend

**Location:** `frontend/src/services/myNewService.ts`

Create a service module to interact with your new API endpoint.

**Example:**
```typescript
// frontend/src/services/myNewService.ts
import { getAuthToken } from './authService';

interface MyApiRequest {
  field1: string;
  field2: string;
}

interface MyApiResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export async function callMyApi(request: MyApiRequest): Promise<MyApiResponse> {
  const config = await fetch('/aws-exports.json').then(r => r.json());
  const token = await getAuthToken();
  
  const response = await fetch(config.myNewApiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }
  
  return response.json();
}
```

---

## Configuration Storage Patterns

Understanding where different types of configuration data are stored is crucial for proper system integration.

### SSM Parameter Store

**Purpose:** Store configuration values that need to be accessed by backend services, Lambda functions, and deployment scripts.

**Use Cases:**
- API endpoint URLs
- Agent metadata (runtime ARNs, display names, descriptions)
- Service configuration values
- Resource identifiers (Memory ID, Gateway URL)

**Naming Convention:** `/{stack-name-base}/{category}/{key}`

**Examples:**
```
/${stack-name-base}/feedback-api-url
/${stack-name-base}/memory-api-url
/${stack-name-base}/agents/{agent-name}/runtime-arn
/${stack-name-base}/agents/{agent-name}/display-name
/${stack-name-base}/gateway_url
/${stack-name-base}/cognito-user-pool-id
```

**Access Pattern:**
```python
# From Lambda or Python script
import boto3
ssm = boto3.client('ssm')
response = ssm.get_parameter(Name=f'/{stack_name}/feedback-api-url')
api_url = response['Parameter']['Value']
```

### S3 Storage

**Purpose:** Store files, deployment packages, and binary assets.

**Use Cases:**
- Agent source code files (.py)
- Deployment packages (ZIP files for Lambda)
- Static assets
- Build artifacts

**Bucket Naming:** `{stack-name-base}-{purpose}`

**Examples:**
```
{stack-name-base}-agent-source-code/agents/{agent-name}/{agent-name}_agent.py
{stack-name-base}-staging/amplify-deploy-{timestamp}.zip
```

**Access Pattern:**
```python
# From Lambda or Python script
import boto3
s3 = boto3.client('s3')
response = s3.get_object(
    Bucket=f'{stack_name}-agent-source-code',
    Key=f'agents/{agent_name}/{agent_name}_agent.py'
)
content = response['Body'].read().decode('utf-8')
```

### CloudFormation Outputs

**Purpose:** Export values from infrastructure stacks for use by deployment scripts and cross-stack references.

**Use Cases:**
- API Gateway URLs
- Resource ARNs
- Amplify App IDs
- Cognito configuration
- Values needed by deployment automation

**Naming Convention:** PascalCase descriptive names

**Examples:**
```typescript
new cdk.CfnOutput(this, "FeedbackApiUrl", {
  value: this.backendStack.feedbackApiUrl,
  description: "Feedback API Gateway URL",
  exportName: `${props.config.stack_name_base}-FeedbackApiUrl`,
});
```

**Access Pattern:**
```python
# From deployment script
import boto3
cfn = boto3.client('cloudformation')
response = cfn.describe_stacks(StackName=stack_name)
outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
api_url = outputs['FeedbackApiUrl']
```

### aws-exports.json (Frontend Configuration)

**Purpose:** Provide runtime configuration to the frontend application.

**Use Cases:**
- API endpoint URLs
- Cognito authentication configuration
- AWS region
- Agent runtime ARNs
- Feature flags

**Location:** `frontend/public/aws-exports.json` (generated during deployment)

**Generation:** Created by `scripts/deploy-frontend.py` from CloudFormation outputs

**Example Structure:**
```json
{
  "authority": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_ABC123",
  "client_id": "abc123def456",
  "redirect_uri": "https://main.d1234567890.amplifyapp.com",
  "post_logout_redirect_uri": "https://main.d1234567890.amplifyapp.com",
  "response_type": "code",
  "scope": "email openid profile",
  "automaticSilentRenew": true,
  "agentRuntimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/abc123",
  "awsRegion": "us-east-1",
  "feedbackApiUrl": "https://abc123.execute-api.us-east-1.amazonaws.com/prod/feedback",
  "memoryApiUrl": "https://abc123.execute-api.us-east-1.amazonaws.com/prod/memory",
  "agentPattern": "strands-single-agent"
}
```

**Access Pattern:**
```typescript
// From React component
const config = await fetch('/aws-exports.json').then(r => r.json());
const apiUrl = config.feedbackApiUrl;
```

---

## Agent Metadata Storage Pattern

Agent metadata is stored in SSM Parameter Store with a hierarchical structure for easy discovery and management.

### Storage Structure

**Base Path:** `/{stack-name-base}/agents/{agent-name}/`

**Parameters Stored:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `/runtime-arn` | String | AgentCore Runtime ARN | `arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/abc123` |
| `/runtime-id` | String | AgentCore Runtime ID | `abc123def456` |
| `/display-name` | String | Human-readable agent name | `Research Assistant` |
| `/description` | String | Short description | `Helps with research tasks` |
| `/tools` | JSON Array | List of tool names | `["sample_tool", "code_interpreter"]` |
| `/model` | String | Model ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `/source-code-url` | String | S3 URL for source code | `s3://stack-agent-source-code/agents/research/research_agent.py` |
| `/system-prompt` | String | Agent system prompt | `You are a helpful research assistant...` |
| `/long-description` | String | Generated description | `This agent specializes in...` |
| `/status` | String | Deployment status | `success` or `failed` |
| `/pattern` | String | Agent pattern type | `strands-multi-agent-orchestrator` |
| `/is-default` | String | Default agent flag | `true` or `false` |

### Source Code Storage

Agent source code is stored in S3 for version control and retrieval:

**Bucket:** `{stack-name-base}-agent-source-code`

**Key Pattern:** `agents/{agent-name}/{agent-name}_agent.py`

**Purpose:**
- Version control of agent implementations
- Source code retrieval for UI display
- Backup and audit trail
- LLM-based description generation

### Discovery Pattern

Backend services discover agents by querying SSM Parameter Store:

```python
# Example: Agent Discovery Lambda
import boto3

ssm = boto3.client('ssm')
stack_name = os.environ['STACK_NAME_BASE']

# List all agents
response = ssm.get_parameters_by_path(
    Path=f'/{stack_name}/agents/',
    Recursive=True
)

# Group by agent name
agents = {}
for param in response['Parameters']:
    parts = param['Name'].split('/')
    agent_name = parts[3]  # /{stack}/agents/{name}/{key}
    key = parts[4]
    
    if agent_name not in agents:
        agents[agent_name] = {}
    
    agents[agent_name][key] = param['Value']
```

---

## Deployment Workflow

The FAST project uses a multi-stage deployment process to ensure infrastructure and frontend are properly synchronized.

### Complete Deployment Steps

```bash
# 1. Navigate to CDK directory
cd infra-cdk

# 2. Install dependencies (if needed)
npm install

# 3. Build TypeScript CDK code
npm run build

# 4. Deploy infrastructure (backend + Amplify hosting)
npx cdk deploy --all

# 5. Return to project root
cd ..

# 6. Deploy frontend to Amplify
python scripts/deploy-frontend.py
```

### What Happens in Each Step

**Step 1-3: Build CDK**
- Compiles TypeScript to JavaScript
- Validates CDK constructs
- Prepares CloudFormation templates

**Step 4: Deploy Infrastructure**
- Creates/updates CloudFormation stacks
- Deploys nested stacks in order:
  1. Amplify Hosting Stack (creates predictable domain)
  2. Cognito Stack (creates user pool and clients)
  3. Backend Stack (creates APIs, Lambda functions, AgentCore resources)
- Stores configuration in SSM Parameter Store
- Exports CloudFormation outputs

**Step 5-6: Deploy Frontend**
- Fetches CloudFormation outputs via AWS CLI
- Generates `aws-exports.json` from outputs
- Builds React application with configuration
- Creates deployment ZIP package
- Uploads to S3 staging bucket
- Triggers Amplify deployment
- Polls deployment status until complete

### Deployment Order Matters

The deployment order is critical because of dependencies:

1. **Amplify Stack First**: Creates predictable domain URL needed by Cognito callbacks
2. **Cognito Stack Second**: Creates user pool needed by backend APIs for authentication
3. **Backend Stack Third**: Creates APIs that reference Cognito and Amplify URL
4. **Frontend Deployment Last**: Requires all infrastructure outputs to generate configuration

### Environment-Specific Deployments

The same deployment process works across environments by using stack names:

```bash
# Development
STACK_NAME=fast-dev npx cdk deploy --all
python scripts/deploy-frontend.py fast-dev

# Staging
STACK_NAME=fast-staging npx cdk deploy --all
python scripts/deploy-frontend.py fast-staging

# Production
STACK_NAME=fast-prod npx cdk deploy --all
python scripts/deploy-frontend.py fast-prod
```

---

## Common Patterns and Anti-Patterns

### ✅ DO: Follow the FeedbackApiUrl Pattern

The Feedback API demonstrates the complete integration pattern:

1. Lambda in `infra-cdk/lambdas/feedback/index.py`
2. CDK method `createFeedbackApi()` in `backend-stack.ts`
3. Public property `public readonly feedbackApiUrl: string`
4. SSM parameter `/${stack-name}/feedback-api-url`
5. CloudFormation output in `fast-main-stack.ts`
6. Required output in `deploy-frontend.py`
7. Field in `aws-exports.json`

**Why:** This ensures the API is accessible everywhere it's needed.

### ✅ DO: Store API URLs in Both SSM and CloudFormation Outputs

```typescript
// Store in SSM for backend services
new ssm.StringParameter(this, "MyApiUrlParam", {
  parameterName: `/${config.stack_name_base}/my-api-url`,
  stringValue: `${this.api.url}my-endpoint`,
});

// Store as public property for CloudFormation export
this.myApiUrl = `${this.api.url}my-endpoint`;
```

**Why:** Backend services use SSM, deployment scripts use CloudFormation outputs.

### ✅ DO: Add Public Properties to BackendStack

```typescript
export class BackendStack extends cdk.NestedStack {
  public readonly feedbackApiUrl: string;
  public readonly memoryApiUrl: string;
  public readonly myNewApiUrl: string; // Add this
}
```

**Why:** Enables the main stack to export the value as a CloudFormation output.

### ✅ DO: Use Consistent Naming Conventions

- **SSM Parameters**: kebab-case (`feedback-api-url`)
- **CloudFormation Outputs**: PascalCase (`FeedbackApiUrl`)
- **TypeScript Properties**: camelCase (`feedbackApiUrl`)
- **JSON Fields**: camelCase (`feedbackApiUrl`)

**Why:** Consistency makes the codebase easier to navigate and maintain.

### ✅ DO: Validate Required Outputs in Deployment Script

```python
required = [
    "CognitoClientId",
    "CognitoUserPoolId",
    "AmplifyUrl",
    "RuntimeArn",
    "FeedbackApiUrl",
    "MemoryApiUrl",
]
missing = [k for k in required if k not in outputs]
if missing:
    raise ValueError(f"Missing required stack outputs: {', '.join(missing)}")
```

**Why:** Fails fast with clear error message if infrastructure is incomplete.

### ❌ DON'T: Store API URLs Only in SSM Without CloudFormation Output

```typescript
// ❌ WRONG - Only in SSM
new ssm.StringParameter(this, "MyApiUrlParam", {
  parameterName: `/${config.stack_name_base}/my-api-url`,
  stringValue: `${this.api.url}my-endpoint`,
});
// Missing: public property and CloudFormation output
```

**Why This Fails:** Deployment script can't fetch the URL from CloudFormation outputs.

### ❌ DON'T: Hardcode API URLs in Frontend Code

```typescript
// ❌ WRONG - Hardcoded URL
const response = await fetch('https://abc123.execute-api.us-east-1.amazonaws.com/prod/feedback', {
  method: 'POST',
  body: JSON.stringify(data),
});
```

**Why This Fails:** Breaks when deploying to different environments or regions.

**✅ CORRECT:**
```typescript
const config = await fetch('/aws-exports.json').then(r => r.json());
const response = await fetch(config.feedbackApiUrl, {
  method: 'POST',
  body: JSON.stringify(data),
});
```

### ❌ DON'T: Skip Adding to aws-exports.json

```python
# ❌ WRONG - Missing from aws-exports
aws_exports = {
    "authority": f"https://cognito-idp.{region}.amazonaws.com/{outputs['CognitoUserPoolId']}",
    "client_id": outputs["CognitoClientId"],
    # ... other fields ...
    # Missing: "myNewApiUrl": outputs["MyNewApiUrl"],
}
```

**Why This Fails:** Frontend can't access the API URL at runtime.

### ❌ DON'T: Forget to Add Public Property in BackendStack

```typescript
// ❌ WRONG - Missing public property
export class BackendStack extends cdk.NestedStack {
  public readonly feedbackApiUrl: string;
  public readonly memoryApiUrl: string;
  // Missing: public readonly myNewApiUrl: string;
  
  private createMyNewApi(config: AppConfig, frontendUrl: string): void {
    // ... creates API ...
    // Missing: this.myNewApiUrl = `${this.api.url}my-endpoint`;
  }
}
```

**Why This Fails:** Main stack can't access the URL to create CloudFormation output.

### ❌ DON'T: Trust Request Body for User Identity

```python
# ❌ WRONG - Trusting request body
def handler(event, context):
    body = json.loads(event['body'])
    user_id = body.get('userId')  # NEVER DO THIS!
```

**Why This Fails:** Users can impersonate others by sending fake user IDs.

**✅ CORRECT:**
```python
# ✅ CORRECT - Extract from validated JWT
def handler(event, context):
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims.get('sub')  # Validated by Cognito authorizer
```

### ✅ DO: Reuse Existing API Gateway

If you already have an API Gateway (like `this.api`), add new resources to it instead of creating a new one:

```typescript
// ✅ CORRECT - Reuse existing API
const myNewResource = this.api.root.addResource("my-new-endpoint");
myNewResource.addMethod("POST", new apigateway.LambdaIntegration(myLambda), {
  authorizer,
  authorizationType: apigateway.AuthorizationType.COGNITO,
});
```

**Why:** Reduces costs, simplifies CORS configuration, and consolidates API management.

### ✅ DO: Use Environment Variables for Configuration

```typescript
// ✅ CORRECT - Configuration via environment variables
const myLambda = new PythonFunction(this, "MyLambda", {
  environment: {
    TABLE_NAME: myTable.tableName,
    MEMORY_ID: sharedResources.memoryId,
    STACK_NAME_BASE: config.stack_name_base,
    CORS_ALLOWED_ORIGINS: `${frontendUrl},http://localhost:3000`,
  },
});
```

**Why:** Makes Lambda functions configurable without code changes.

---

## Troubleshooting

### Problem: "API URL not found in configuration"

**Symptoms:** Frontend can't find API URL in `aws-exports.json`

**Diagnosis:**
1. Check if `aws-exports.json` exists in `frontend/public/`
2. Verify the field name matches what frontend code expects
3. Check if deployment script ran successfully

**Solution:**
1. Verify CloudFormation output exists in `fast-main-stack.ts`
2. Verify field is added to `aws-exports` object in `deploy-frontend.py`
3. Re-run deployment: `python scripts/deploy-frontend.py <stack-name>`

### Problem: "Missing required stack outputs"

**Symptoms:** Deployment script fails with error about missing outputs

**Diagnosis:**
```
ValueError: Missing required stack outputs: MyNewApiUrl
```

**Solution:**
1. Add CloudFormation output in `fast-main-stack.ts`:
```typescript
new cdk.CfnOutput(this, "MyNewApiUrl", {
  value: this.backendStack.myNewApiUrl,
  description: "My New API Gateway URL",
  exportName: `${props.config.stack_name_base}-MyNewApiUrl`,
});
```

2. Rebuild and redeploy CDK:
```bash
cd infra-cdk
npm run build
npx cdk deploy --all
```

### Problem: "Cannot read property of undefined"

**Symptoms:** TypeScript error when accessing `this.backendStack.myNewApiUrl`

**Diagnosis:** Missing public property in `BackendStack`

**Solution:**
1. Add public property declaration:
```typescript
export class BackendStack extends cdk.NestedStack {
  public readonly myNewApiUrl: string;
}
```

2. Set the property value in your API creation method:
```typescript
private createMyNewApi(config: AppConfig, frontendUrl: string): void {
  // ... create API ...
  this.myNewApiUrl = `${this.api.url}my-endpoint`;
}
```

### Problem: "CORS error when calling API"

**Symptoms:** Browser console shows CORS error

**Diagnosis:** CORS not properly configured

**Solution:**
1. Verify Lambda has CORS configuration:
```python
cors_origins = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(",")]
cors_config = CORSConfig(
    allow_origin=cors_origins[0],
    extra_origins=cors_origins[1:] if len(cors_origins) > 1 else None,
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)
```

2. Verify API Gateway has CORS preflight:
```typescript
this.api = new apigateway.RestApi(this, "Api", {
  defaultCorsPreflightOptions: {
    allowOrigins: [frontendUrl, "http://localhost:3000"],
    allowMethods: ["POST", "GET", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
  },
});
```

### Problem: "Unauthorized" error when calling API

**Symptoms:** API returns 401 Unauthorized

**Diagnosis:** Missing or invalid JWT token

**Solution:**
1. Verify frontend is sending Authorization header:
```typescript
const token = await getAuthToken();
const response = await fetch(apiUrl, {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

2. Verify Cognito authorizer is configured:
```typescript
const authorizer = new apigateway.CognitoUserPoolsAuthorizer(
  this,
  "MyApiAuthorizer",
  {
    cognitoUserPools: [this.userPool],
    identitySource: "method.request.header.Authorization",
  }
);
```

3. Verify method uses the authorizer:
```typescript
myResource.addMethod("POST", new apigateway.LambdaIntegration(myLambda), {
  authorizer,
  authorizationType: apigateway.AuthorizationType.COGNITO,
});
```

### Problem: "Lambda timeout"

**Symptoms:** API Gateway returns 504 Gateway Timeout

**Diagnosis:** Lambda execution exceeds timeout limit

**Solution:**
1. Increase Lambda timeout:
```typescript
const myLambda = new PythonFunction(this, "MyLambda", {
  timeout: cdk.Duration.seconds(60), // Increase from default 30s
});
```

2. Optimize Lambda code to reduce execution time
3. Check CloudWatch Logs for performance bottlenecks

---

## Complete Example: Adding a New Backend API

Let's walk through adding a hypothetical "Notifications API" that allows users to manage notification preferences.

### Step 1: Create Lambda Function

**File:** `infra-cdk/lambdas/notifications/index.py`

```python
"""Notifications API Lambda Handler"""

import os
import json
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from pydantic import BaseModel, Field

# Environment variables
TABLE_NAME = os.environ["TABLE_NAME"]
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

# Configure CORS
cors_origins = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(",")]
cors_config = CORSConfig(
    allow_origin=cors_origins[0],
    extra_origins=cors_origins[1:] if len(cors_origins) > 1 else None,
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(cors=cors_config)
dynamodb = boto3.client("dynamodb")

class NotificationPreferences(BaseModel):
    """Notification preferences model"""
    email_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=False)
    frequency: str = Field(default="daily", pattern="^(realtime|daily|weekly)$")

@app.get("/notifications")
def get_preferences():
    """Get user's notification preferences"""
    # Extract user ID from JWT
    claims = app.current_event.request_context.authorizer.get("claims", {})
    user_id = claims.get("sub")
    
    if not user_id:
        return {"error": "Unauthorized"}, 401
    
    try:
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={"userId": {"S": user_id}}
        )
        
        if "Item" not in response:
            # Return defaults if no preferences exist
            return {
                "emailEnabled": True,
                "pushEnabled": False,
                "frequency": "daily"
            }
        
        item = response["Item"]
        return {
            "emailEnabled": item.get("emailEnabled", {}).get("BOOL", True),
            "pushEnabled": item.get("pushEnabled", {}).get("BOOL", False),
            "frequency": item.get("frequency", {}).get("S", "daily"),
        }
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        return {"error": "Internal server error"}, 500

@app.post("/notifications")
def update_preferences():
    """Update user's notification preferences"""
    # Extract user ID from JWT
    claims = app.current_event.request_context.authorizer.get("claims", {})
    user_id = claims.get("sub")
    
    if not user_id:
        return {"error": "Unauthorized"}, 401
    
    try:
        # Validate request
        prefs = NotificationPreferences(**app.current_event.json_body)
        
        # Save to DynamoDB
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                "userId": {"S": user_id},
                "emailEnabled": {"BOOL": prefs.email_enabled},
                "pushEnabled": {"BOOL": prefs.push_enabled},
                "frequency": {"S": prefs.frequency},
            }
        )
        
        return {"success": True}
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return {"error": str(e)}, 400
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return {"error": "Internal server error"}, 500

def handler(event, context):
    """Lambda handler"""
    return app.resolve(event, context)
```

### Step 2: Add to Backend Stack

**File:** `infra-cdk/lib/backend-stack.ts`

```typescript
export class BackendStack extends cdk.NestedStack {
  public readonly feedbackApiUrl: string;
  public readonly memoryApiUrl: string;
  public readonly notificationsApiUrl: string; // Add public property
  private api: apigateway.RestApi;
  
  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);
    
    // ... existing code ...
    
    // Create Notifications table
    const notificationsTable = this.createNotificationsTable(props.config);
    
    // Create Notifications API
    this.createNotificationsApi(props.config, props.frontendUrl, notificationsTable);
  }
  
  private createNotificationsTable(config: AppConfig): dynamodb.Table {
    return new dynamodb.Table(this, "NotificationsTable", {
      tableName: `${config.stack_name_base}-notifications`,
      partitionKey: {
        name: "userId",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });
  }
  
  private createNotificationsApi(
    config: AppConfig,
    frontendUrl: string,
    notificationsTable: dynamodb.Table
  ): void {
    // Create Lambda function
    const notificationsLambda = new PythonFunction(this, "NotificationsLambda", {
      functionName: `${config.stack_name_base}-notifications`,
      runtime: lambda.Runtime.PYTHON_3_13,
      entry: path.join(__dirname, "..", "lambdas", "notifications"),
      handler: "handler",
      environment: {
        TABLE_NAME: notificationsTable.tableName,
        CORS_ALLOWED_ORIGINS: `${frontendUrl},http://localhost:3000`,
      },
      timeout: cdk.Duration.seconds(30),
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          "NotificationsPowertoolsLayer",
          `arn:aws:lambda:${cdk.Stack.of(this).region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-arm64:18`
        ),
      ],
      logGroup: new logs.LogGroup(this, "NotificationsLambdaLogGroup", {
        logGroupName: `/aws/lambda/${config.stack_name_base}-notifications`,
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Grant DynamoDB permissions
    notificationsTable.grantReadWriteData(notificationsLambda);

    // Create Cognito authorizer
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(
      this,
      "NotificationsApiAuthorizer",
      {
        cognitoUserPools: [this.userPool],
        identitySource: "method.request.header.Authorization",
        authorizerName: `${config.stack_name_base}-notifications-authorizer`,
      }
    );

    // Add API Gateway resource and methods
    const notificationsResource = this.api.root.addResource("notifications");
    
    // GET method
    notificationsResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(notificationsLambda),
      {
        authorizer,
        authorizationType: apigateway.AuthorizationType.COGNITO,
      }
    );
    
    // POST method
    notificationsResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(notificationsLambda),
      {
        authorizer,
        authorizationType: apigateway.AuthorizationType.COGNITO,
      }
    );

    // Store API URL in SSM
    new ssm.StringParameter(this, "NotificationsApiUrlParam", {
      parameterName: `/${config.stack_name_base}/notifications-api-url`,
      stringValue: `${this.api.url}notifications`,
      description: "Notifications API endpoint URL",
    });

    // Store API URL as public property
    this.notificationsApiUrl = `${this.api.url}notifications`;
  }
}
```

### Step 3: Export from Main Stack

**File:** `infra-cdk/lib/fast-main-stack.ts`

```typescript
export class FastMainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastAmplifyStackProps) {
    super(scope, id, props);
    
    // ... existing code ...
    
    // Add CloudFormation output
    new cdk.CfnOutput(this, "NotificationsApiUrl", {
      value: this.backendStack.notificationsApiUrl,
      description: "Notifications API Gateway URL",
      exportName: `${props.config.stack_name_base}-NotificationsApiUrl`,
    });
  }
}
```

### Step 4: Update Deployment Script

**File:** `scripts/deploy-frontend.py`

```python
def generate_aws_exports(
    stack_name: str,
    outputs: Dict[str, str],
    region: str,
    pattern: str,
    frontend_dir: Path,
) -> None:
    # Add to required outputs
    required = [
        "CognitoClientId",
        "CognitoUserPoolId",
        "AmplifyUrl",
        "RuntimeArn",
        "FeedbackApiUrl",
        "MemoryApiUrl",
        "NotificationsApiUrl",  # Add here
    ]
    missing = [k for k in required if k not in outputs]

    if missing:
        raise ValueError(f"Missing required stack outputs: {', '.join(missing)}")

    # Add to aws-exports
    aws_exports = {
        "authority": f"https://cognito-idp.{region}.amazonaws.com/{outputs['CognitoUserPoolId']}",
        "client_id": outputs["CognitoClientId"],
        "redirect_uri": outputs["AmplifyUrl"],
        "post_logout_redirect_uri": outputs["AmplifyUrl"],
        "response_type": "code",
        "scope": "email openid profile",
        "automaticSilentRenew": True,
        "agentRuntimeArn": outputs["RuntimeArn"],
        "awsRegion": region,
        "feedbackApiUrl": outputs["FeedbackApiUrl"],
        "memoryApiUrl": outputs["MemoryApiUrl"],
        "notificationsApiUrl": outputs["NotificationsApiUrl"],  # Add here
        "agentPattern": pattern,
    }
    
    # ... rest of function ...
```

### Step 5: Create Frontend Service

**File:** `frontend/src/services/notificationsService.ts`

```typescript
import { getAuthToken } from './authService';

export interface NotificationPreferences {
  emailEnabled: boolean;
  pushEnabled: boolean;
  frequency: 'realtime' | 'daily' | 'weekly';
}

/**
 * Fetch user's notification preferences
 */
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const config = await fetch('/aws-exports.json').then(r => r.json());
  const token = await getAuthToken();
  
  const response = await fetch(config.notificationsApiUrl, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch preferences: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Update user's notification preferences
 */
export async function updateNotificationPreferences(
  preferences: NotificationPreferences
): Promise<void> {
  const config = await fetch('/aws-exports.json').then(r => r.json());
  const token = await getAuthToken();
  
  const response = await fetch(config.notificationsApiUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preferences),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update preferences');
  }
}
```

### Step 6: Deploy

```bash
# Build and deploy infrastructure
cd infra-cdk
npm run build
npx cdk deploy --all

# Deploy frontend
cd ..
python scripts/deploy-frontend.py
```

### Step 7: Verify

1. **Check CloudFormation outputs:**
```bash
aws cloudformation describe-stacks --stack-name <stack-name> \
  --query 'Stacks[0].Outputs[?OutputKey==`NotificationsApiUrl`].OutputValue' \
  --output text
```

2. **Check SSM parameter:**
```bash
aws ssm get-parameter --name "/<stack-name>/notifications-api-url" \
  --query 'Parameter.Value' --output text
```

3. **Check aws-exports.json:**
```bash
cat frontend/public/aws-exports.json | grep notificationsApiUrl
```

4. **Test API:**
```bash
# Get JWT token from browser console or Cognito
TOKEN="<your-jwt-token>"
API_URL="<notifications-api-url>"

# Get preferences
curl -H "Authorization: Bearer $TOKEN" $API_URL

# Update preferences
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"emailEnabled":true,"pushEnabled":true,"frequency":"daily"}' \
  $API_URL
```

---

**ALWAYS FOLLOW THESE RULES WHEN WORKING WITH BACKEND APIS**
