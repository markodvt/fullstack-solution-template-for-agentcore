# Task 1.2 Verification: Agent Discovery Lambda

**Task:** Verify agent discovery Lambda works correctly  
**Date:** 2025-02-26  
**Status:** ⚠️ PARTIAL - Missing Runtime API Integration

## Summary

The agent discovery Lambda (`infra-cdk/lambdas/agent-discovery/index.py`) is **partially implemented**. It successfully retrieves agent metadata from SSM Parameter Store with proper error handling, but it is **missing the Runtime API integration** specified in Requirements 10.2 and 10.12.

## Verification Results

### ✅ 1. SSM Parameter Integration - VERIFIED

**Implementation:** Lines 30-80 in `index.py`

The Lambda correctly:
- Queries SSM Parameter Store at path `/{stack_name_base}/agents`
- Retrieves all agent parameters recursively with pagination support
- Extracts agent names from parameter paths
- Fetches detailed metadata for each agent including:
  - `runtime-arn` → `runtimeArn`
  - `runtime-id` → `runtimeId`
  - `display-name` → `displayName`
  - `description` → `description`
  - `is-default` → `isDefault`
  - `status` → `status`
  - `error` → `error`
  - `pattern` → `pattern`

**IAM Permissions:** Verified in `backend-stack.ts` lines 658-673
```typescript
actions: [
  "ssm:GetParameter",
  "ssm:GetParameters",
  "ssm:GetParametersByPath",
]
resources: [
  `arn:aws:ssm:${region}:${account}:parameter/${stack_name_base}/agents`,
  `arn:aws:ssm:${region}:${account}:parameter/${stack_name_base}/agents/*`,
]
```

**Validation:**
- ✅ Handles pagination with `NextToken`
- ✅ Validates required fields (`displayName`, `status`)
- ✅ Logs warnings for missing agents or fields
- ✅ Returns `None` for invalid agents (graceful degradation)
- ✅ Sorts agents: default first, then alphabetically

### ❌ 2. Runtime API Integration - MISSING

**Requirement 10.2:** "WHEN the `/api/agents` endpoint receives a GET request, THE Discovery_Service SHALL call the AgentCore Runtime API to list agents"

**Current State:** The Lambda does NOT call the Runtime API.

**Expected Implementation:**
```python
import boto3

# Create bedrock-agentcore-control client
agentcore_client = boto3.client('bedrock-agentcore-control')

def list_runtimes_from_api():
    """Query Runtime API for agent list and status."""
    try:
        response = agentcore_client.list_agent_runtimes(maxResults=100)
        
        runtimes = []
        for runtime in response.get('agentRuntimes', []):
            runtimes.append({
                'runtimeArn': runtime['agentRuntimeArn'],
                'runtimeId': runtime['agentRuntimeId'],
                'name': runtime['agentRuntimeName'],
                'description': runtime.get('description', ''),
                'status': runtime['status'],  # CREATING, READY, CREATE_FAILED, etc.
                'lastUpdatedAt': runtime.get('lastUpdatedAt')
            })
        
        # Handle pagination
        while 'nextToken' in response:
            response = agentcore_client.list_agent_runtimes(
                maxResults=100,
                nextToken=response['nextToken']
            )
            for runtime in response.get('agentRuntimes', []):
                # ... append to runtimes list
        
        return runtimes
    except ClientError as e:
        logger.error(f"Runtime API error: {e}")
        return []  # Fallback to SSM-only per Requirement 10.12
```

**Required IAM Permissions (MISSING):**
```typescript
agentDiscoveryLambda.addToRolePolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      "bedrock-agentcore-control:ListAgentRuntimes",
      "bedrock-agentcore-control:GetAgentRuntime",  // Optional for details
    ],
    resources: ["*"],  // ListAgentRuntimes requires wildcard
  })
)
```

**Hybrid Approach (from Design Document):**
The design specifies a hybrid SSM + Runtime API approach:
1. Call Runtime API to get agent list with real-time status
2. Call SSM to get additional metadata (display names, patterns, etc.)
3. Merge the two data sources by matching on `runtimeArn` or `runtimeId`
4. If Runtime API fails, fall back to SSM-only (Requirement 10.12)

**Benefits of Runtime API Integration:**
- Real-time deployment status (CREATING, READY, CREATE_FAILED, etc.)
- Accurate `lastUpdatedAt` timestamps
- Authoritative source for runtime existence
- Detects agents deployed outside of CDK
- Aligns with Requirements 10.2 and design architecture

### ✅ 3. Error Handling - VERIFIED

**401 Unauthorized:** Handled by API Gateway Cognito Authorizer (lines 680-688 in `backend-stack.ts`)
- API Gateway validates JWT token before Lambda invocation
- Invalid/missing tokens return 401 automatically
- Lambda never receives unauthorized requests

**500 Internal Server Error:** Properly handled in Lambda (lines 215-250 in `index.py`)
- Missing `STACK_NAME_BASE` environment variable → 500 with "Configuration error"
- SSM `ClientError` exceptions → logged and re-raised → 500 with error message
- Generic exceptions → logged with stack trace → 500 with error message
- All error responses include CORS headers

**Error Logging:**
- ✅ Uses Python `logging` module with INFO level
- ✅ Logs all incoming events
- ✅ Logs warnings for missing agents/fields
- ✅ Logs errors with `exc_info=True` for stack traces
- ✅ CloudWatch log group configured with 7-day retention

### ✅ 4. CORS Configuration - VERIFIED

**Implementation:** Lines 155-178 in `index.py`

- ✅ Reads `CORS_ALLOWED_ORIGINS` from environment (set in `backend-stack.ts` line 639)
- ✅ Validates request origin against allowed list
- ✅ Returns appropriate `Access-Control-Allow-Origin` header
- ✅ Includes `Access-Control-Allow-Headers` and `Access-Control-Allow-Methods`
- ✅ Applies CORS headers to both success and error responses

**Allowed Origins:** `${frontendUrl},http://localhost:3000` (for local development)

### ✅ 5. Response Format - VERIFIED

**Current Response:**
```json
{
  "agents": [
    {
      "name": "orchestrator",
      "displayName": "Orchestrator",
      "description": "Main agent that routes queries",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "runtimeId": "...",
      "status": "success",
      "isDefault": true,
      "pattern": "strands-multi-agent-orchestrator"
    }
  ],
  "count": 1
}
```

**Notes:**
- ✅ Returns array of agent objects
- ✅ Includes all required fields from Requirements 10.6-10.11
- ⚠️ `status` field is from SSM (static), not Runtime API (dynamic)
- ⚠️ Missing fields that Runtime API would provide: `lastUpdatedAt`, real-time deployment status

## Requirements Mapping

| Requirement | Status | Notes |
|-------------|--------|-------|
| 1.1 - Retrieve agent metadata from Runtime API | ❌ MISSING | Only SSM is queried |
| 1.2 - Scan agents directory | ⚠️ PARTIAL | SSM stores metadata, but no file scanning |
| 10.1 - Provide `/api/agents` endpoint | ✅ VERIFIED | Configured in `backend-stack.ts` |
| 10.2 - Call Runtime API to list agents | ❌ MISSING | Not implemented |
| 10.3 - Scan agents directory | ⚠️ PARTIAL | SSM approach, not file scanning |
| 10.5 - Return JSON array of agents | ✅ VERIFIED | Correct format |
| 10.6-10.11 - Include required fields | ✅ VERIFIED | All fields present |
| 10.12 - Fallback to local on API failure | ⚠️ N/A | No Runtime API call to fail |
| 10.13 - Return 500 on error | ✅ VERIFIED | Proper error handling |

## Recommendations

### 1. Add Runtime API Integration (HIGH PRIORITY)

**Why:** Required by Requirement 10.2 and design architecture

**Implementation Steps:**
1. Add `boto3.client('bedrock-agentcore-control')` to Lambda
2. Implement `list_runtimes_from_api()` function
3. Merge Runtime API data with SSM data in `discover_agents()`
4. Add fallback logic per Requirement 10.12
5. Add IAM permissions for `bedrock-agentcore-control:ListAgentRuntimes`

**Code Location:** Add to `infra-cdk/lambdas/agent-discovery/index.py`

### 2. Update CDK Stack IAM Permissions

**File:** `infra-cdk/lib/backend-stack.ts` (after line 673)

```typescript
// Grant Lambda permissions to list agent runtimes
agentDiscoveryLambda.addToRolePolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      "bedrock-agentcore-control:ListAgentRuntimes",
    ],
    resources: ["*"],  // ListAgentRuntimes requires wildcard resource
  })
)
```

### 3. Implement Hybrid Merge Logic

**Approach:**
1. Call Runtime API first to get authoritative runtime list
2. For each runtime, look up additional metadata from SSM
3. If SSM has agents not in Runtime API, include them with status "not_deployed"
4. If Runtime API fails, fall back to SSM-only mode

**Benefits:**
- Real-time deployment status
- Detects manually deployed agents
- Graceful degradation
- Aligns with design document

### 4. Add Unit Tests

**Missing Tests:**
- Test Runtime API integration
- Test hybrid merge logic
- Test fallback behavior when Runtime API fails
- Test pagination for Runtime API
- Test status mapping (READY → "deployed", CREATE_FAILED → "failed")

### 5. Update Status Field Mapping

**Current:** SSM stores static "success" or "failed" strings  
**Proposed:** Map Runtime API status to frontend-friendly values

```python
STATUS_MAPPING = {
    'READY': 'deployed',
    'CREATING': 'pending',
    'UPDATING': 'pending',
    'CREATE_FAILED': 'failed',
    'UPDATE_FAILED': 'failed',
    'DELETING': 'deleting',
}
```

## Testing Checklist

- [x] Lambda has SSM read permissions
- [x] Lambda handles missing environment variables
- [x] Lambda handles SSM errors gracefully
- [x] Lambda returns proper CORS headers
- [x] Lambda returns 500 on errors
- [x] API Gateway has Cognito authorizer (401 handling)
- [ ] Lambda has Runtime API permissions
- [ ] Lambda calls Runtime API
- [ ] Lambda merges Runtime + SSM data
- [ ] Lambda falls back to SSM on Runtime API failure
- [ ] Lambda handles Runtime API pagination

## Conclusion

The agent discovery Lambda is **functional but incomplete**. It successfully retrieves agent metadata from SSM with proper error handling and CORS support. However, it is **missing the Runtime API integration** specified in the requirements and design document.

**Impact:**
- ⚠️ Agent status is static (from SSM) instead of real-time (from Runtime API)
- ⚠️ Cannot detect agents deployed outside of CDK
- ⚠️ Does not align with Requirement 10.2
- ⚠️ Does not implement the hybrid architecture from design document

**Next Steps:**
1. Implement Runtime API integration (see Recommendation #1)
2. Add IAM permissions (see Recommendation #2)
3. Implement hybrid merge logic (see Recommendation #3)
4. Add unit tests for new functionality
5. Test with real Runtime API responses

**Estimated Effort:** 2-3 hours to implement Runtime API integration and testing
