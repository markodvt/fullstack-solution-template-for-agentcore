# Agent Discovery API Implementation Plan

## Context

The backend has successfully deployed 4 agents (orchestrator, colorado, umich, coder) to AgentCore Runtime. Agent metadata is stored in SSM Parameter Store at paths like:
- `/{stack_name_base}/agents/{agent_name}/runtime-arn`
- `/{stack_name_base}/agents/{agent_name}/runtime-id`
- `/{stack_name_base}/agents/{agent_name}/display-name`
- `/{stack_name_base}/agents/{agent_name}/description`
- `/{stack_name_base}/agents/{agent_name}/is-default`
- `/{stack_name_base}/agents/{agent_name}/status`

The frontend is getting a 404 error because it's still configured for single-agent mode and doesn't know about the new multi-agent deployment.

## Goal

Create an agent discovery API endpoint that:
1. Retrieves agent metadata from SSM Parameter Store
2. Returns a list of available agents with display names and descriptions
3. Allows the frontend to discover and connect to the deployed agents

## Implementation Steps

### Step 1: Create Lambda Function for Agent Discovery

**Location**: `infra-cdk/lambdas/agent-discovery/index.py`

**Functionality**:
- Read stack name from environment variable
- Query SSM Parameter Store for all agents under `/{stack_name_base}/agents/`
- Parse agent metadata from SSM parameters
- Return JSON response with agent list

**Response Format**:
```json
{
  "agents": [
    {
      "name": "orchestrator",
      "displayName": "Orchestrator",
      "description": "Main agent that routes queries to specialized agents",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "runtimeId": "...",
      "isDefault": true,
      "status": "success"
    },
    {
      "name": "umich",
      "displayName": "UMich Specialist",
      "description": "Specialized agent for University of Michigan queries",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "runtimeId": "...",
      "isDefault": false,
      "status": "success"
    }
  ]
}
```

### Step 2: Add API Gateway Endpoint

**Location**: `infra-cdk/lib/backend-stack.ts`

**Method**: `createAgentDiscoveryApi()`

**Implementation**:
- Create Lambda function using PythonFunction construct
- Grant SSM read permissions to Lambda
- Add `/agents` GET endpoint to existing API Gateway (reuse feedback API)
- Configure CORS for frontend access
- Add Cognito authorizer for authentication
- Store API URL in SSM for frontend access

### Step 3: Update Frontend to Use Discovery Endpoint

**Location**: `frontend/src/services/agentDiscoveryService.ts`

**Functionality**:
- Fetch agent list from `/agents` endpoint
- Cache agent metadata
- Provide methods to get available agents
- Handle authentication with Cognito tokens

### Step 4: Test the Implementation

**Test Steps**:
1. Deploy CDK stack with new endpoint
2. Test Lambda function directly
3. Test API Gateway endpoint with authentication
4. Verify frontend can fetch agent list
5. Verify frontend can connect to UMich agent

## Code Conventions to Follow

1. Add docstrings to all functions explaining purpose, inputs, and outputs
2. Use explicit strong types in method signatures
3. Comment non-obvious code thoroughly
4. Avoid fallback to default values - fail loudly
5. Use named parameters over positional parameters

## Security Considerations

- Use Cognito authorizer for API authentication
- Grant minimal IAM permissions (SSM read-only for agent parameters)
- Validate all inputs
- Use CORS to restrict frontend origins
- Log all access for auditing

## Alignment with Spec

This implements Task 8.1 from the multi-agent-orchestration-pattern spec:
- **Requirement 4.3**: Store agent metadata in SSM Parameter Store ✅ (already done)
- **Requirement 4.4**: Frontend retrieves available agents from discovery API ✅ (to be implemented)

## Next Steps After Implementation

1. Update frontend to display agent selection dropdown
2. Implement agent switching logic
3. Test orchestrator routing to specialists
4. Verify conversation history per agent
