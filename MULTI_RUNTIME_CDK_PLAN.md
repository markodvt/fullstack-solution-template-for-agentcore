# Multi-Runtime CDK Implementation Plan

## Goal

Modify the CDK infrastructure to deploy **4 agent runtimes** in a **single stack** with **shared infrastructure**.

## Current vs Target Architecture

### Current (Single Runtime)
```
Stack: marodon-fast
├── Cognito User Pool
├── Frontend (Amplify)
├── Memory (shared)
└── Runtime (1): Colorado Agent
```

### Target (Multi-Runtime)
```
Stack: marodon-fast
├── Cognito User Pool (shared)
├── Frontend (Amplify) with agent selector
├── Memory (shared across all agents)
└── Runtimes (4):
    ├── Runtime 1: Colorado Agent
    ├── Runtime 2: UMich Agent
    ├── Runtime 3: Coder Agent
    └── Runtime 4: Orchestrator Agent
```

## Configuration Changes

### config.yaml (Already Updated)
```yaml
backend:
  agents:
    - pattern: strands-colorado-agent
      name: colorado
    - pattern: strands-umich-agent
      name: umich
    - pattern: strands-coder-agent
      name: coder
    - pattern: strands-orchestrator-agent
      name: orchestrator
  deployment_type: docker
```

## CDK Changes Required

### 1. Update ConfigManager Types
**File**: `infra-cdk/lib/utils/config-manager.ts`

Add support for agents array:
```typescript
export interface AgentConfig {
  pattern: string;
  name: string;
}

export interface BackendConfig {
  pattern?: string;  // Keep for backward compatibility
  agents?: AgentConfig[];  // New multi-agent support
  deployment_type: "docker" | "zip";
}
```

### 2. Modify BackendStack to Create Multiple Runtimes
**File**: `infra-cdk/lib/backend-stack.ts`

Current approach:
- Single `createAgentCoreRuntime()` call
- Creates one runtime based on `config.backend.pattern`

New approach:
- Loop through `config.backend.agents` array
- Create one runtime per agent
- Store each runtime ARN in SSM with agent name suffix
- Share same memory across all runtimes
- Each runtime gets unique environment variables

### 3. Key Implementation Details

#### Memory (Shared)
- Create ONE memory resource
- All runtimes use the same `MEMORY_ID`
- Each agent uses unique session prefix (colorado_, umich_, coder_, orchestrator_)

#### Runtimes (Per-Agent)
For each agent in config:
1. Create runtime artifact from pattern directory
2. Create runtime with unique name: `{stack_name}_{agent_name}`
3. Store runtime ARN in SSM: `/{stack_name}/runtime-arn-{agent_name}`
4. Set environment variables:
   - `MEMORY_ID`: Shared memory ID
   - `STACK_NAME`: Stack name
   - `AWS_DEFAULT_REGION`: Region
   - For orchestrator only: Other runtime ARNs

#### IAM Permissions
- Each runtime gets standard permissions (Bedrock, Memory, SSM)
- Coder agent gets additional Code Interpreter permissions
- Orchestrator gets permission to invoke other runtimes

#### Frontend Configuration
Generate `aws-exports.json` with all agents:
```json
{
  "agents": [
    {
      "id": "orchestrator",
      "name": "Orchestrator",
      "runtimeArn": "arn:...:orchestrator",
      "pattern": "strands-single-agent"
    },
    {
      "id": "colorado",
      "name": "Colorado Teacher",
      "runtimeArn": "arn:...:colorado",
      "pattern": "strands-single-agent"
    },
    // ... etc
  ],
  "defaultAgent": "orchestrator"
}
```

## Implementation Steps

### Step 1: Update ConfigManager
- Add `AgentConfig` interface
- Update `BackendConfig` to support agents array
- Maintain backward compatibility with single pattern

### Step 2: Refactor Backend Stack
- Extract runtime creation logic into reusable function
- Loop through agents array
- Create runtime for each agent
- Store ARNs with agent-specific names

### Step 3: Update Frontend Stack
- Read all runtime ARNs from SSM
- Generate agents array in aws-exports.json
- Deploy to Amplify

### Step 4: Create Orchestrator Agent
- Implement orchestrator pattern (after other agents deployed)
- Add tools to invoke other agents
- Deploy as 4th runtime

### Step 5: Update Frontend UI
- Add agent selector component
- Load agents from config
- Switch between agents

## Backward Compatibility

Support both old and new config formats:
```typescript
// Old format (single agent)
backend:
  pattern: strands-single-agent

// New format (multi-agent)
backend:
  agents:
    - pattern: strands-colorado-agent
      name: colorado
```

If `agents` array exists, use multi-runtime mode.
If only `pattern` exists, create single runtime (legacy mode).

## Testing Strategy

### Phase 1: Deploy Infrastructure
1. Deploy CDK with 3 specialist agents (colorado, umich, coder)
2. Verify all 3 runtimes created
3. Verify SSM parameters for each runtime ARN
4. Test each agent individually via AWS console

### Phase 2: Create Orchestrator
1. Implement orchestrator agent
2. Deploy as 4th runtime
3. Test orchestrator routing

### Phase 3: Update Frontend
1. Update aws-exports.json generation
2. Add agent selector UI
3. Test agent switching

## Code Structure

### New Function in BackendStack
```typescript
private createAgentRuntime(
  agentConfig: AgentConfig,
  memory: cdk.CfnResource,
  agentRole: AgentCoreRole,
  config: AppConfig
): agentcore.Runtime {
  // Create runtime artifact
  // Create runtime
  // Store ARN in SSM
  // Return runtime
}
```

### Modified createAgentCoreRuntime
```typescript
private createAgentCoreRuntime(config: AppConfig): void {
  // Create shared memory (once)
  const memory = this.createMemory(config);
  
  // Create shared role (once)
  const agentRole = new AgentCoreRole(this, "AgentCoreRole");
  
  // Check if multi-agent or single agent
  if (config.backend.agents && config.backend.agents.length > 0) {
    // Multi-agent mode
    for (const agentConfig of config.backend.agents) {
      this.createAgentRuntime(agentConfig, memory, agentRole, config);
    }
  } else {
    // Legacy single agent mode
    const agentConfig = {
      pattern: config.backend.pattern,
      name: "default"
    };
    this.createAgentRuntime(agentConfig, memory, agentRole, config);
  }
}
```

## Orchestrator Special Handling

The orchestrator needs runtime ARNs of other agents:

```typescript
// When creating orchestrator runtime
if (agentConfig.name === "orchestrator") {
  // Read other runtime ARNs from SSM
  const coloradoArn = ssm.StringParameter.valueFromLookup(
    this,
    `/${config.stack_name_base}/runtime-arn-colorado`
  );
  
  envVars["COLORADO_RUNTIME_ARN"] = coloradoArn;
  envVars["UMICH_RUNTIME_ARN"] = umichArn;
  envVars["CODER_RUNTIME_ARN"] = coderArn;
  
  // Add permission to invoke other runtimes
  agentRole.addToPolicy(
    new iam.PolicyStatement({
      actions: ["bedrock-agentcore:InvokeRuntime"],
      resources: [coloradoArn, umichArn, coderArn]
    })
  );
}
```

## Deployment Order

1. **First Deployment**: Deploy 3 specialist agents (colorado, umich, coder)
   - Creates shared Cognito, Memory, Frontend
   - Creates 3 runtimes
   
2. **Create Orchestrator**: Implement orchestrator agent code
   - Add tools to invoke other agents
   
3. **Second Deployment**: Deploy with orchestrator
   - Adds 4th runtime
   - Orchestrator can read other ARNs from SSM
   
4. **Frontend Update**: Add agent selector
   - Update aws-exports.json generation
   - Add UI component

## Questions Before Implementation

1. Should we deploy orchestrator in first deployment or wait until it's implemented?
   - **Recommendation**: Deploy 3 specialists first, then add orchestrator

2. Should orchestrator be the default agent in UI?
   - **Answer from user**: Yes

3. How should we handle orchestrator dependencies on other runtime ARNs?
   - **Solution**: Use SSM parameter lookup in CDK

## Next Steps

1. Get approval on this plan
2. Implement ConfigManager changes
3. Refactor BackendStack for multi-runtime
4. Deploy 3 specialist agents
5. Test each agent
6. Implement orchestrator
7. Deploy orchestrator
8. Update frontend

Ready to proceed with implementation?
