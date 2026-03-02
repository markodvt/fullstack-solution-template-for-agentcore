# Agent Metadata Enhancement Recommendation

**Date:** February 28, 2025  
**Context:** Enhanced Agent UI Phases 1-2 complete, need to add tools list and source code display  
**Goal:** Enable UI to display agent tools and source code without tight coupling to backend deployment

---

## Current Architecture

### Data Flow
```
Agent .py files (patterns/*/agents/*/*.py)
    ↓
CDK Deployment (backend-stack.ts)
    ↓
SSM Parameter Store (/{stack}/agents/{name}/*)
    ↓
Agent Discovery Lambda (reads SSM)
    ↓
Frontend (/api/agents endpoint)
```

### Currently Stored in SSM
- `runtime-arn` - AgentCore Runtime ARN
- `runtime-id` - Runtime identifier
- `display-name` - Human-readable name
- `description` - Agent description
- `is-default` - Default agent flag
- `pattern` - Pattern type (e.g., "strands-multi-agent-orchestrator")
- `status` - Deployment status (success/failed)
- `error` - Error message (if failed)

### Currently Missing from SSM
- ❌ **Tools list** - Array of tool names the agent has access to
- ❌ **Model ID** - The LLM model used by the agent
- ❌ **Source code** - The agent's Python implementation

---

## Problem Statement

**Issue 1: Tools Information**
- Agent tiles show "Tools info pending"
- Agent details page doesn't display tools list
- Information exists in agent .py files but not persisted to SSM

**Issue 2: Source Code Display**
- Agent details page shows "Source code is not available for this agent"
- Source code exists in agent .py files but not accessible to frontend
- Users want to see agent implementation for transparency

**Issue 3: Model Information**
- Model ID is hardcoded in agent .py files but not exposed to UI
- Users want to know which LLM model each agent uses

**Root Cause:**
- Agent metadata extraction happens at CDK deployment time
- Only basic metadata from `agents.json` is stored in SSM
- Rich metadata from agent .py files (tools, model, source code) is not extracted or stored

---

## Recommended Solution

### Option 1: Enhanced SSM Storage (RECOMMENDED)

**Approach:** Extract and store additional metadata in SSM during CDK deployment

**Advantages:**
- ✅ Maintains existing architecture (SSM as source of truth)
- ✅ No new AWS services required
- ✅ Loosely coupled (frontend deployment independent of backend)
- ✅ Consistent with current pattern
- ✅ Simple to implement
- ✅ Works for both single-agent and multi-agent patterns

**Implementation:**

#### 1. Add Metadata Extraction to CDK Deployment

**File:** `infra-cdk/lib/backend-stack.ts`

**Location:** In `storeAgentMetadata()` method (lines 1200-1260)

**New SSM Parameters to Add:**

```typescript
// Tools list (JSON array)
new ssm.StringParameter(this, `SSMAgentTools-${agentName}`, {
  parameterName: `${baseParam}/tools`,
  stringValue: JSON.stringify(toolsList),
  description: `Tools available to ${agentName} agent`,
})

// Model ID
new ssm.StringParameter(this, `SSMAgentModel-${agentName}`, {
  parameterName: `${baseParam}/model`,
  stringValue: modelId,
  description: `LLM model used by ${agentName} agent`,
})

// Source code (base64 encoded to handle special characters)
new ssm.StringParameter(this, `SSMAgentSourceCode-${agentName}`, {
  parameterName: `${baseParam}/source-code`,
  stringValue: Buffer.from(sourceCode).toString('base64'),
  description: `Source code for ${agentName} agent`,
  tier: ssm.ParameterTier.ADVANCED, // Supports up to 8KB
})
```

#### 2. Create Metadata Extraction Function

**File:** `infra-cdk/lib/backend-stack.ts`

**Add new method:**

```typescript
/**
 * Extract metadata from agent Python file.
 * Parses the agent source code to extract tools list, model ID, and source code.
 * 
 * @param agentFilePath - Path to agent .py file
 * @returns Extracted metadata
 */
private extractAgentMetadata(agentFilePath: string): {
  tools: string[]
  modelId: string
  sourceCode: string
} {
  const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')
  
  // Extract tools list
  // Pattern 1: tools=[tool1, tool2, ...]
  // Pattern 2: tools=[gateway_client, tool1, tool2]
  const toolsMatch = sourceCode.match(/tools\s*=\s*\[([\s\S]*?)\]/m)
  let tools: string[] = []
  
  if (toolsMatch) {
    const toolsContent = toolsMatch[1]
    
    // Extract tool names (handle various formats)
    // - Direct tool names: http_request, current_time
    // - Gateway client: gateway_client
    // - Method calls: specialist_tools.invoke_colorado
    const toolNames = toolsContent
      .split(',')
      .map(t => t.trim())
      .filter(t => t && !t.startsWith('#'))
      .map(t => {
        // Remove quotes if present
        t = t.replace(/['"]/g, '')
        // Extract just the tool name (handle method calls)
        if (t.includes('.')) {
          return t.split('.').pop() || t
        }
        return t
      })
      .filter(Boolean)
    
    tools = toolNames
  }
  
  // Extract model ID
  // Pattern: model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  const modelMatch = sourceCode.match(/model_id\s*=\s*["']([^"']+)["']/)
  const modelId = modelMatch ? modelMatch[1] : 'unknown'
  
  return {
    tools,
    modelId,
    sourceCode
  }
}
```

#### 3. Update `storeAgentMetadata()` Method

**File:** `infra-cdk/lib/backend-stack.ts`

**Modify method signature and add extraction:**

```typescript
private storeAgentMetadata(
  config: AppConfig,
  pattern: string,
  agentEntry: AgentManifestEntry,
  runtime: agentcore.Runtime,
  status: "success" | "failed"
): void {
  const agentName = agentEntry.name
  const baseParam = `/${config.stack_name_base}/agents/${agentName}`

  // Determine agent file path
  const patternPath = path.resolve(__dirname, "..", "..", "patterns", pattern)
  const agentFilePath = path.join(patternPath, "agents", agentName, `${agentName}_agent.py`)
  
  // Extract metadata from agent file
  let metadata = { tools: [], modelId: 'unknown', sourceCode: '' }
  try {
    if (fs.existsSync(agentFilePath)) {
      metadata = this.extractAgentMetadata(agentFilePath)
    }
  } catch (error) {
    console.warn(`Failed to extract metadata for ${agentName}:`, error)
  }

  // ... existing SSM parameters ...

  // Add new SSM parameters for tools, model, and source code
  new ssm.StringParameter(this, `SSMAgentTools-${agentName}`, {
    parameterName: `${baseParam}/tools`,
    stringValue: JSON.stringify(metadata.tools),
    description: `Tools available to ${agentName} agent`,
  })

  new ssm.StringParameter(this, `SSMAgentModel-${agentName}`, {
    parameterName: `${baseParam}/model`,
    stringValue: metadata.modelId,
    description: `LLM model used by ${agentName} agent`,
  })

  new ssm.StringParameter(this, `SSMAgentSourceCode-${agentName}`, {
    parameterName: `${baseParam}/source-code`,
    stringValue: Buffer.from(metadata.sourceCode).toString('base64'),
    description: `Source code for ${agentName} agent`,
    tier: ssm.ParameterTier.ADVANCED, // Supports up to 8KB
  })
}
```

#### 4. Update Agent Discovery Lambda

**File:** `infra-cdk/lambdas/agent-discovery/index.py`

**Modify `get_agent_metadata()` function:**

```python
def get_agent_metadata(
    stack_name_base: str, agent_name: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a single agent from SSM Parameter Store.

    Args:
        stack_name_base: Base name of the CloudFormation stack
        agent_name: Name of the agent (e.g., "orchestrator", "umich")

    Returns:
        Dictionary containing agent metadata, or None if agent not found
    """
    base_path = f"/{stack_name_base}/agents/{agent_name}"

    try:
        # Get all parameters for this agent
        response = ssm_client.get_parameters_by_path(
            Path=base_path, Recursive=False, WithDecryption=False
        )

        if not response.get("Parameters"):
            logger.warning(f"No parameters found for agent: {agent_name}")
            return None

        # Parse parameters into metadata dictionary
        metadata = {"name": agent_name}

        for param in response["Parameters"]:
            param_name = param["Name"].split("/")[-1]  # Get last part of path
            param_value = param["Value"]

            # Map parameter names to metadata fields
            if param_name == "runtime-arn":
                metadata["runtimeArn"] = param_value
            elif param_name == "runtime-id":
                metadata["runtimeId"] = param_value
            elif param_name == "display-name":
                metadata["displayName"] = param_value
            elif param_name == "description":
                metadata["description"] = param_value
            elif param_name == "is-default":
                metadata["isDefault"] = param_value.lower() == "true"
            elif param_name == "status":
                metadata["status"] = param_value
            elif param_name == "error":
                metadata["error"] = param_value
            elif param_name == "pattern":
                metadata["pattern"] = param_value
            # NEW: Add tools, model, and source code
            elif param_name == "tools":
                try:
                    metadata["tools"] = json.loads(param_value)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tools JSON for {agent_name}")
                    metadata["tools"] = []
            elif param_name == "model":
                metadata["model"] = param_value
            elif param_name == "source-code":
                try:
                    # Decode base64 source code
                    import base64
                    metadata["sourceCode"] = base64.b64decode(param_value).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to decode source code for {agent_name}: {e}")
                    metadata["sourceCode"] = None

        # Validate required fields
        required_fields = ["displayName", "status"]
        for field in required_fields:
            if field not in metadata:
                logger.warning(
                    f"Missing required field '{field}' for agent: {agent_name}"
                )
                return None

        return metadata

    except ClientError as e:
        logger.error(f"Error retrieving metadata for agent {agent_name}: {str(e)}")
        return None
```

#### 5. Frontend Automatically Receives New Fields

**No changes needed!** The frontend already:
- Fetches from `/api/agents` endpoint
- Has TypeScript interfaces with optional fields
- Components handle missing fields gracefully

**Verification:**
- Check `frontend/src/services/agentDiscoveryService.ts` - `Agent` interface
- Check `frontend/src/components/AgentTile.tsx` - handles missing tools
- Check `frontend/src/pages/AgentDetailsPage.tsx` - handles missing source code

---

### SSM Parameter Size Considerations

**Standard Tier:** 4KB limit  
**Advanced Tier:** 8KB limit (use for source code)

**Typical Agent File Sizes:**
- `umich_agent.py`: ~5KB
- `orchestrator_agent.py`: ~8KB
- `colorado_agent.py`: ~4KB
- `coder_agent.py`: ~6KB

**Strategy:**
- Use Advanced tier for source code parameters
- If agent file exceeds 8KB, truncate with message: "Source code too large to display"
- Alternative: Store in S3 and put S3 URL in SSM (see Option 2)

---

### Option 2: S3 + SSM Hybrid

**Approach:** Store source code in S3, reference in SSM

**Advantages:**
- ✅ No size limits for source code
- ✅ Can store additional artifacts (requirements.txt, Dockerfile, etc.)
- ✅ Versioning support via S3
- ✅ Can serve source code directly from S3 (with presigned URLs)

**Disadvantages:**
- ❌ More complex architecture
- ❌ Additional S3 bucket management
- ❌ Frontend needs S3 access or proxy through Lambda
- ❌ Overkill for current needs

**When to use:** If agent files exceed 8KB or need versioning

**Implementation Sketch:**

```typescript
// In backend-stack.ts
const agentCodeBucket = new s3.Bucket(this, "AgentSourceCodeBucket", {
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  autoDeleteObjects: true,
  versioned: true,
})

// Upload source code to S3
const s3Key = `agents/${agentName}/source.py`
// ... upload logic ...

// Store S3 reference in SSM
new ssm.StringParameter(this, `SSMAgentSourceCodeUrl-${agentName}`, {
  parameterName: `${baseParam}/source-code-url`,
  stringValue: `s3://${agentCodeBucket.bucketName}/${s3Key}`,
  description: `S3 location of source code for ${agentName} agent`,
})
```

---

### Option 3: DynamoDB Storage

**Approach:** Store all agent metadata in DynamoDB table

**Advantages:**
- ✅ No size limits
- ✅ Rich querying capabilities
- ✅ Can store structured metadata
- ✅ Better for complex queries (e.g., "find all agents using Claude Sonnet")

**Disadvantages:**
- ❌ Requires new DynamoDB table
- ❌ More complex than SSM
- ❌ Breaks existing SSM pattern
- ❌ Overkill for current needs

**When to use:** If need complex queries or very large metadata

---

## Implementation Plan (Option 1 - Recommended)

### Phase 1: Add Metadata Extraction to CDK (2-3 hours)

**Files to modify:**
- `infra-cdk/lib/backend-stack.ts`

**Changes:**
1. Create `extractAgentMetadata()` method
2. Update `storeAgentMetadata()` to call extraction
3. Add new SSM parameters for tools, model, source code
4. Handle extraction errors gracefully (log warnings, continue deployment)

**Testing:**
1. Deploy backend: `cd infra-cdk && cdk deploy`
2. Verify SSM parameters created:
   ```bash
   aws ssm get-parameters-by-path --path "/<stack-name>/agents/umich" --recursive
   ```
3. Check tools, model, and source-code parameters exist
4. Verify base64 encoding of source code

**Estimated effort:** 2-3 hours

---

### Phase 2: Update Agent Discovery Lambda (1-2 hours)

**Files to modify:**
- `infra-cdk/lambdas/agent-discovery/index.py`

**Changes:**
1. Add import for `base64` module
2. Update `get_agent_metadata()` to read new parameters
3. Parse tools JSON array
4. Decode base64 source code
5. Include in response
6. Handle missing/malformed data gracefully

**Testing:**
1. Deploy backend: `cd infra-cdk && cdk deploy`
2. Test API endpoint:
   ```bash
   curl -H "Authorization: Bearer <token>" \
        https://<api-url>/agents
   ```
3. Verify response includes tools, model, sourceCode fields
4. Check error handling for missing data

**Estimated effort:** 1-2 hours

---

### Phase 3: Update Frontend Types (Optional) (30 minutes)

**Files to modify:**
- `frontend/src/services/agentDiscoveryService.ts`

**Changes:**
1. Update `Agent` interface to include:
   ```typescript
   model?: string
   tools?: string[]
   sourceCode?: string
   ```
2. Components already handle optional fields (no changes needed)

**Testing:**
1. Deploy frontend: `python scripts/deploy-frontend.py`
2. Open browser console, check network tab
3. Verify `/api/agents` response includes new fields
4. Check TypeScript compilation (no errors)

**Estimated effort:** 30 minutes

---

### Phase 4: Deploy and Test (1 hour)

**Deployment Steps:**
1. Deploy backend: `cd infra-cdk && cdk deploy`
2. Wait for deployment to complete
3. Deploy frontend: `python scripts/deploy-frontend.py`
4. Wait for frontend deployment

**Testing Checklist:**
- [ ] Agent tiles show "X tools" instead of "Tools info pending"
- [ ] Agent tiles show correct tool count
- [ ] Agent details page displays tools list
- [ ] Agent details page displays model ID
- [ ] Agent details page displays source code with Python syntax highlighting
- [ ] Failed agents show "Source code not available" gracefully
- [ ] No console errors in browser
- [ ] No Lambda errors in CloudWatch

**Estimated effort:** 1 hour

**Total estimated effort:** 4-6 hours

---

## Alternative: Quick Win with agents.json

**Temporary solution while implementing full extraction:**

### Approach

Add tools and model to `agents.json` manifest:

```json
{
  "agents": [
    {
      "name": "umich",
      "displayName": "UMich Specialist",
      "description": "Specialized agent for University of Michigan queries",
      "runtimeId": "umich",
      "isDefault": false,
      "model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
      "tools": ["http_request", "current_time"]
    }
  ]
}
```

Update CDK to read and store these fields in SSM.

**Advantages:**
- ✅ Quick to implement (1 hour)
- ✅ No parsing required
- ✅ Explicit metadata definition

**Disadvantages:**
- ❌ Manual maintenance (tools must be kept in sync)
- ❌ Doesn't provide source code
- ❌ Duplication of information (tools defined in both .py and .json)
- ❌ Risk of drift between manifest and actual code

**Recommendation:** Use as interim solution, then implement full extraction

---

## Security Considerations

### Source Code Exposure

**Question:** Should agent source code be visible to all users?

**Considerations:**
- ✅ **Transparency:** Users can see what the agent does
- ✅ **Trust:** Users can verify agent behavior
- ✅ **Debugging:** Helps users understand agent responses
- ⚠️ **Intellectual Property:** May expose proprietary logic
- ⚠️ **Security:** May reveal sensitive patterns

**Recommendations:**

1. **For internal tools:** Show source code (current use case)
2. **For external/customer-facing:** Consider hiding or redacting
3. **Add toggle:** Allow admins to enable/disable source code display per agent

**Implementation:**

Add `showSourceCode` flag to `agents.json`:

```json
{
  "name": "umich",
  "displayName": "UMich Specialist",
  "description": "...",
  "runtimeId": "umich",
  "isDefault": false,
  "showSourceCode": true  // Admin-controlled flag
}
```

Store in SSM and check in frontend before displaying.

**For this project:** Show source code (internal tool, transparency is valuable)

---

## Testing Strategy

### Unit Tests

**Backend (CDK):**
- Test `extractAgentMetadata()` with various agent file formats
- Test handling of missing tools
- Test handling of missing model ID
- Test base64 encoding/decoding
- Test SSM parameter creation

**Backend (Lambda):**
- Test `get_agent_metadata()` with complete data
- Test handling of missing parameters
- Test JSON parsing of tools array
- Test base64 decoding of source code
- Test error handling

**Frontend:**
- Test `Agent` interface with new fields
- Test components with missing fields
- Test source code syntax highlighting

### Integration Tests

1. Deploy test agent with known tools and model
2. Verify tools appear in agent tile
3. Verify tools appear in agent details
4. Verify model ID appears in agent details
5. Verify source code appears in agent details
6. Verify syntax highlighting works
7. Test with multiple agents
8. Test with failed agent deployment

### Edge Cases

- Agent with no tools (empty array)
- Agent with many tools (>10)
- Agent with very long source code (>8KB)
- Agent with special characters in source code (quotes, backslashes)
- Failed agent deployment (no source code available)
- Malformed tools JSON in SSM
- Corrupted base64 source code in SSM
- Missing SSM parameters

---

## Rollout Plan

### Step 1: Implement Extraction (Backend)
- Add `extractAgentMetadata()` method to CDK
- Update `storeAgentMetadata()` to call extraction
- Add new SSM parameters
- Deploy to dev environment
- Verify SSM parameters created correctly

### Step 2: Update Discovery Lambda
- Add parameter reading for tools, model, source code
- Update response format
- Deploy to dev environment
- Test API response manually
- Verify all fields present

### Step 3: Frontend Verification
- Deploy frontend to dev
- Verify tools display in tiles (count)
- Verify tools display in details (list)
- Verify model ID displays
- Verify source code displays with syntax highlighting
- Test error handling (missing data)

### Step 4: Production Deployment
- Deploy backend to production
- Monitor CloudWatch logs for errors
- Deploy frontend to production
- Verify all agents display correctly
- Monitor user feedback

---

## Success Criteria

✅ **Agent Tiles:**
- Show "X tools" instead of "Tools info pending"
- Display accurate tool count
- Handle agents with 0 tools gracefully

✅ **Agent Details:**
- Display complete tools list with names
- Display model ID (e.g., "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
- Display source code with Python syntax highlighting
- Handle missing source code gracefully ("Source code not available")
- Show error message for failed agents

✅ **Architecture:**
- Frontend deployment remains independent of backend
- No breaking changes to existing functionality
- Backward compatible (handles agents without new metadata)
- Graceful degradation (missing fields don't break UI)

✅ **Performance:**
- No significant increase in API response time
- SSM parameter reads remain fast (<100ms)
- Source code decoding doesn't block response

---

## Conclusion

**Recommended Approach:** Option 1 (Enhanced SSM Storage)

**Rationale:**
- Maintains existing architecture
- Simple to implement
- No new AWS services
- Loosely coupled
- Sufficient for current needs
- Works for both single-agent and multi-agent patterns

**Quick Win:** Add tools and model to `agents.json` as interim solution (optional)

**Timeline:**
- Interim solution: 1 hour (optional)
- Full solution: 4-6 hours
- Total: 4-7 hours

**Next Steps:**
1. Review and approve this recommendation
2. Decide on interim vs. full solution
3. Implement metadata extraction in CDK
4. Update Agent Discovery Lambda
5. Deploy and test in dev environment
6. Deploy to production
7. Update session summary with results

---

## Appendix: Example Agent Metadata

### Example: UMich Agent

**Source File:** `patterns/strands-multi-agent-orchestrator/agents/umich/umich_agent.py`

**Extracted Metadata:**
```json
{
  "name": "umich",
  "displayName": "UMich Specialist",
  "description": "Specialized agent for University of Michigan queries",
  "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/abc123",
  "runtimeId": "umich",
  "isDefault": false,
  "pattern": "strands-multi-agent-orchestrator",
  "status": "success",
  "model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "tools": ["http_request", "current_time"],
  "sourceCode": "\"\"\"\\nUMich Agent - A helpful assistant who LOVES the University of Michigan.\\n\\n..."
}
```

### Example: Orchestrator Agent

**Source File:** `patterns/strands-multi-agent-orchestrator/agents/orchestrator/orchestrator_agent.py`

**Extracted Metadata:**
```json
{
  "name": "orchestrator",
  "displayName": "Orchestrator",
  "description": "Main agent that routes queries to specialized agents",
  "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/xyz789",
  "runtimeId": "orchestrator",
  "isDefault": true,
  "pattern": "strands-multi-agent-orchestrator",
  "status": "success",
  "model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "tools": ["gateway_client", "invoke_colorado", "invoke_umich", "invoke_coder", "tap"],
  "sourceCode": "\"\"\"\\nOrchestrator Agent - Routes user queries to appropriate specialist agents.\\n\\n..."
}
```

---

**Status:** Recommendation ready for review and implementation

**Author:** AI Assistant  
**Reviewed by:** [Pending]  
**Approved by:** [Pending]
