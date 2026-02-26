# Task 7: CDK Stack Multi-Agent Deployment - Implementation Plan

**STATUS: APPROVED - READY FOR IMPLEMENTATION**

## Executive Summary

This plan details the implementation for updating the CDK stack to support the new multi-agent orchestration pattern architecture. The implementation will transition from the current multi-agent deployment approach (using `agents[]` array in config.yaml) to a unified pattern-based approach where a single pattern (`strands-multi-agent-orchestrator`) contains all four agents with a manifest-driven deployment.

**Key User Decisions Applied:**
- ✅ No backward compatibility needed for `agents[]` array (never deployed)
- ✅ AgentCore Runtime provides endpoints directly (no API Gateway routes needed)
- ✅ Orchestrator deployed alongside specialist agents
- ✅ Frontend discovery via Runtime API (Task 8), metadata stored in SSM (Task 7)
- ✅ Graceful degradation for partial deployment failures

## Context

### Current State
- **Config approach**: CDK supports multi-agent deployment via `agents[]` array in config.yaml
- **Pattern structure**: Each agent is treated as a separate pattern directory
- **Runtime creation**: Single `createAgentCoreRuntime()` method creates one runtime per pattern
- **Shared resources**: Memory, Gateway, Code Interpreter, Cognito created once and shared

### Target State
- **Config approach**: Single pattern mode with `pattern: strands-multi-agent-orchestrator`
- **Pattern structure**: One pattern directory containing all four agents in subdirectories
- **Agent discovery**: Pattern contains `agents.json` manifest defining all 4 agents
- **Runtime creation**: CDK reads manifest and creates separate runtime for each agent
- **Docker images**: Each agent has its own Dockerfile for independent building
- **Shared resources**: Continue to be created once and shared across all agents

### Key Architectural Principle
**Patterns represent deployment strategies, not individual agents.** The multi-agent orchestration pattern is a single architectural approach that happens to deploy multiple agent runtimes.


## Key Requirements from Design Document

### 1. Agent Discovery (Requirement 4.2)
- Read `agents.json` manifest from pattern directory to discover agents
- Validate manifest structure (name, displayName, description, runtimeId, isDefault)
- Fail deployment with descriptive error if manifest is invalid

### 2. Multi-Runtime Deployment (Requirement 2.1, 2.2)
- Create separate AgentCore Runtime instance for each agent in manifest
- Each runtime gets its own Docker image built from agent-specific Dockerfile
- All runtimes share the same execution role with appropriate permissions

### 3. Docker Image Building (Requirement 11.2)
- Build separate Docker image for each agent using agent-specific Dockerfile
- Dockerfile path: `patterns/${pattern}/agents/${agentName}/Dockerfile`
- All agents share the same `requirements.txt` at pattern root
- Build context remains repository root for access to shared utilities

### 4. Shared Backend Resources (Requirement 2.3, 2.4)
- Deploy shared resources ONCE (outside agent loop):
  - AgentCore Memory (with long-term memory strategies)
  - AgentCore Gateway (with MCP protocol and JWT auth)
  - Code Interpreter (AWS managed service)
  - Cognito User Pool and clients (already in separate stack)
- All agents reference the same shared resource instances

### 5. Agent Metadata Storage (Requirement 4.3)
- Store agent metadata in SSM Parameter Store for discovery:
  - `/${stackName}/agents/${agentName}/runtime-arn`
  - `/${stackName}/agents/${agentName}/runtime-id`
  - `/${stackName}/agents/${agentName}/endpoint`
  - `/${stackName}/agents/${agentName}/display-name`
  - `/${stackName}/agents/${agentName}/description`
  - `/${stackName}/agents/${agentName}/is-default`

### 6. CloudFormation Outputs (Requirement 4.4)
- Export agent endpoints in CloudFormation outputs:
  - `AgentRuntimeArn-${agentName}` for each agent
  - `AgentRuntimeId-${agentName}` for each agent
  - `AgentRuntimeEndpoint-${agentName}` for each agent
- Include deployment status for each agent (success/failed)

### 7. AgentCore Runtime Architecture
- **AgentCore Runtime is "Lambda for agents"** - a single service per AWS account
- Each agent gets its own endpoint within the Runtime service
- Runtime provides secure, serverless, scalable endpoints
- Each agent has a single `@app.endpoint` entry point (like Lambda handler)
- Agents can run from seconds up to 8 hours
- Runtime integrates with AgentCore Memory, Identity, Observability
- **NO API Gateway routes needed** - Runtime provides the endpoints directly

### 8. Graceful Degradation for Partial Failures
- Deployment should continue even if one agent fails
- Failed agents should log errors and warnings but not block other agents
- Use CDK error handling to wrap each agent deployment in try-catch
- Mark failed agents in SSM with status parameter
- CloudFormation outputs should show deployment status for each agent


## Current CDK Architecture Analysis

### Config Manager (infra-cdk/lib/utils/config-manager.ts)
**Current capabilities**:
- ✅ Supports both `pattern` (single agent) and `agents[]` (multi-agent array)
- ✅ Validates deployment_type (docker or zip)
- ✅ Validates stack_name_base length (max 35 chars)
- ✅ Prefers `agents[]` if both pattern and agents are provided

**Required changes**: 
- ✅ **NO CHANGES NEEDED** - Already supports `backend.pattern` for single pattern mode
- Config validation already handles the case where only `pattern` is specified
- **Note**: `agents[]` array support can remain but is not used (never deployed to production)

### Backend Stack (infra-cdk/lib/backend-stack.ts)
**Current architecture**:
- `createAgentCoreRuntime()` method creates a single runtime
- Reads pattern from `config.backend?.pattern || "strands-single-agent"`
- Creates one `agentRuntimeArtifact` from pattern Dockerfile
- Creates one `agentcore.Runtime` instance
- Stores single runtime ARN in SSM: `/${stackName}/runtime-arn`
- Outputs single runtime ARN and ID

**Shared resources** (already created once):
- ✅ AgentCore Memory (with long-term strategies)
- ✅ AgentCore Gateway (with MCP protocol and JWT auth)
- ✅ Machine Client for M2M authentication
- ✅ Cognito integration
- ✅ Feedback API and DynamoDB table

**Required changes**:
- 🔄 Detect multi-agent pattern and read agents.json manifest
- 🔄 Loop through agents and create runtime for each with error handling
- 🔄 Build agent-specific Docker images
- 🔄 Store per-agent metadata in SSM (including deployment status)
- 🔄 Create per-agent CloudFormation outputs (including deployment status)
- 🔄 Implement graceful degradation for partial deployment failures
- ✅ Keep shared resource creation unchanged
- ✅ No API Gateway route creation needed (Runtime provides endpoints)


## Implementation Steps

### Step 1: Create Agent Manifest Interface and Validation

**File**: `infra-cdk/lib/utils/agent-manifest.ts` (new file)

**Purpose**: Define TypeScript interfaces and validation logic for agents.json manifest

**Implementation**:
```typescript
/**
 * Interface for agent metadata from agents.json manifest.
 */
export interface AgentManifestEntry {
  name: string;
  displayName: string;
  description: string;
  runtimeId: string;
  isDefault: boolean;
}

/**
 * Interface for the complete agents.json structure.
 */
export interface AgentManifest {
  agents: AgentManifestEntry[];
}

/**
 * Validates an agent manifest entry has all required fields.
 * 
 * @param entry - Agent manifest entry to validate
 * @param index - Index in agents array (for error messages)
 * @throws Error if validation fails
 */
export function validateAgentEntry(entry: any, index: number): void {
  const requiredFields = ['name', 'displayName', 'description', 'runtimeId', 'isDefault'];
  
  for (const field of requiredFields) {
    if (!(field in entry)) {
      throw new Error(
        `Agent entry at index ${index} is missing required field: ${field}`
      );
    }
    
    if (field !== 'isDefault' && (!entry[field] || entry[field].trim() === '')) {
      throw new Error(
        `Agent entry at index ${index} has empty value for required field: ${field}`
      );
    }
  }
  
  if (typeof entry.isDefault !== 'boolean') {
    throw new Error(
      `Agent entry at index ${index} has invalid isDefault value (must be boolean)`
    );
  }
}

/**
 * Loads and validates agents.json manifest from pattern directory.
 * 
 * @param patternPath - Absolute path to pattern directory
 * @returns Validated agent manifest
 * @throws Error if manifest is missing, malformed, or invalid
 */
export function loadAgentManifest(patternPath: string): AgentManifest {
  const manifestPath = path.join(patternPath, 'agents.json');
  
  if (!fs.existsSync(manifestPath)) {
    throw new Error(
      `Agent manifest not found at ${manifestPath}. ` +
      `Multi-agent patterns must include agents.json manifest.`
    );
  }
  
  let manifest: AgentManifest;
  try {
    const content = fs.readFileSync(manifestPath, 'utf-8');
    manifest = JSON.parse(content);
  } catch (error) {
    throw new Error(
      `Failed to parse agents.json manifest at ${manifestPath}: ${error}`
    );
  }
  
  if (!manifest.agents || !Array.isArray(manifest.agents)) {
    throw new Error(
      `Invalid agents.json: must contain "agents" array`
    );
  }
  
  if (manifest.agents.length === 0) {
    throw new Error(
      `Invalid agents.json: "agents" array cannot be empty`
    );
  }
  
  // Validate each agent entry
  manifest.agents.forEach((entry, index) => {
    validateAgentEntry(entry, index);
  });
  
  // Validate exactly one default agent
  const defaultAgents = manifest.agents.filter(a => a.isDefault);
  if (defaultAgents.length === 0) {
    throw new Error(
      `Invalid agents.json: must have exactly one agent with isDefault: true`
    );
  }
  if (defaultAgents.length > 1) {
    throw new Error(
      `Invalid agents.json: multiple agents marked as default (${defaultAgents.map(a => a.name).join(', ')})`
    );
  }
  
  return manifest;
}
```

**Testing**: Unit tests in `infra-cdk/test/agent-manifest.test.ts`


### Step 2: Detect Multi-Agent Pattern in Backend Stack

**File**: `infra-cdk/lib/backend-stack.ts`

**Location**: Beginning of `createAgentCoreRuntime()` method

**Implementation**:
```typescript
private createAgentCoreRuntime(config: AppConfig): void {
  const pattern = config.backend?.pattern || "strands-single-agent"
  
  // Detect if this is a multi-agent pattern by checking for agents.json
  const patternPath = path.resolve(__dirname, "..", "..", "patterns", pattern)
  const manifestPath = path.join(patternPath, "agents.json")
  const isMultiAgentPattern = fs.existsSync(manifestPath)
  
  if (isMultiAgentPattern) {
    // Multi-agent deployment: read manifest and create multiple runtimes
    this.createMultiAgentRuntimes(config, pattern, patternPath)
  } else {
    // Single-agent deployment: existing logic
    this.createSingleAgentRuntime(config, pattern, patternPath)
  }
}
```

**Rationale**: 
- Detection is based on presence of `agents.json` file, not pattern name
- This makes the approach extensible to future multi-agent patterns
- Keeps backward compatibility with existing single-agent patterns


### Step 3: Refactor Existing Runtime Creation to Single-Agent Method

**File**: `infra-cdk/lib/backend-stack.ts`

**Purpose**: Extract current runtime creation logic into a dedicated method for single-agent patterns

**Implementation**:
```typescript
/**
 * Creates a single AgentCore Runtime for traditional single-agent patterns.
 * 
 * @param config - Application configuration
 * @param pattern - Pattern name (e.g., "strands-single-agent")
 * @param patternPath - Absolute path to pattern directory
 */
private createSingleAgentRuntime(
  config: AppConfig, 
  pattern: string, 
  patternPath: string
): void {
  // Move existing createAgentCoreRuntime() logic here
  // This includes:
  // - Parameter creation (AgentName, NetworkMode)
  // - Agent runtime artifact creation (Docker or ZIP)
  // - Memory resource creation
  // - Agent role creation and permissions
  // - Runtime creation
  // - SSM parameter storage
  // - CloudFormation outputs
  
  // Keep all existing logic unchanged for backward compatibility
}
```

**Changes from current code**:
- Extract existing logic into this new method
- No functional changes to single-agent deployment
- Maintains backward compatibility


### Step 4: Implement Multi-Agent Runtime Creation

**File**: `infra-cdk/lib/backend-stack.ts`

**Purpose**: Create separate AgentCore Runtime for each agent in manifest with graceful error handling

**Implementation**:
```typescript
/**
 * Creates multiple AgentCore Runtimes for multi-agent orchestration patterns.
 * Reads agents.json manifest and deploys a separate runtime for each agent.
 * Implements graceful degradation - continues deployment even if individual agents fail.
 * 
 * @param config - Application configuration
 * @param pattern - Pattern name (e.g., "strands-multi-agent-orchestrator")
 * @param patternPath - Absolute path to pattern directory
 */
private createMultiAgentRuntimes(
  config: AppConfig,
  pattern: string,
  patternPath: string
): void {
  const stack = cdk.Stack.of(this)
  const deploymentType = config.backend.deployment_type

  // Load and validate agent manifest
  const manifest = loadAgentManifest(patternPath)
  
  // Create shared resources ONCE (outside agent loop)
  const sharedResources = this.createSharedAgentResources(config)
  
  // Store runtime ARNs for cross-agent invocation
  const runtimeArns: { [agentName: string]: string } = {}
  const deploymentStatuses: { [agentName: string]: 'success' | 'failed' } = {}
  
  // Create runtime for each agent with error handling
  for (const agentEntry of manifest.agents) {
    const agentName = agentEntry.name
    
    try {
      // Validate agent directory and Dockerfile exist
      const agentDir = path.join(patternPath, "agents", agentName)
      const dockerfilePath = path.join(agentDir, "Dockerfile")
      
      if (!fs.existsSync(agentDir)) {
        throw new Error(
          `Agent directory not found: ${agentDir}. ` +
          `Manifest references agent "${agentName}" but directory does not exist.`
        )
      }
      
      if (!fs.existsSync(dockerfilePath)) {
        throw new Error(
          `Dockerfile not found: ${dockerfilePath}. ` +
          `Agent "${agentName}" must have a Dockerfile for deployment.`
        )
      }
      
      // Create agent-specific runtime
      const runtime = this.createAgentRuntime(
        config,
        pattern,
        agentEntry,
        sharedResources,
        deploymentType
      )
      
      // Store runtime ARN
      runtimeArns[agentName] = runtime.agentRuntimeArn
      deploymentStatuses[agentName] = 'success'
      
      // Store agent metadata in SSM
      this.storeAgentMetadata(config, agentEntry, runtime, 'success')
      
      // Create CloudFormation outputs
      this.createAgentOutputs(config, agentEntry, runtime, 'success')
      
      console.log(`✅ Successfully deployed agent: ${agentName}`)
      
    } catch (error) {
      // Log error but continue with other agents (graceful degradation)
      console.error(`❌ Failed to deploy agent ${agentName}:`, error)
      deploymentStatuses[agentName] = 'failed'
      
      // Store failure status in SSM
      this.storeAgentFailureMetadata(config, agentEntry, error.message)
      
      // Create failure output
      this.createAgentFailureOutputs(config, agentEntry, error.message)
      
      // Add warning annotation to CloudFormation
      cdk.Annotations.of(this).addWarning(
        `Agent ${agentName} failed to deploy: ${error.message}`
      )
    }
  }
  
  // Check if at least one agent deployed successfully
  const successfulAgents = Object.entries(deploymentStatuses)
    .filter(([_, status]) => status === 'success')
  
  if (successfulAgents.length === 0) {
    throw new Error(
      'All agents failed to deploy. At least one agent must deploy successfully.'
    )
  }
  
  // Store the default runtime ARN (or first successful agent)
  const defaultAgent = manifest.agents.find(a => a.isDefault && deploymentStatuses[a.name] === 'success')
    || manifest.agents.find(a => deploymentStatuses[a.name] === 'success')!
  
  this.runtimeArn = runtimeArns[defaultAgent.name]
  
  // Create summary output
  new cdk.CfnOutput(this, "DeploymentSummary", {
    description: "Multi-agent deployment summary",
    value: JSON.stringify({
      total: manifest.agents.length,
      successful: successfulAgents.length,
      failed: manifest.agents.length - successfulAgents.length,
      agents: deploymentStatuses
    }),
  })
}
```

**Key design decisions**:
- Shared resources created once before agent loop
- Validation happens early (fail-fast on missing directories/Dockerfiles)
- **Graceful degradation**: Errors caught per-agent, deployment continues
- Failed agents logged with warnings, not errors
- Deployment fails only if ALL agents fail
- Runtime ARNs stored in map for potential cross-agent invocation
- Default agent runtime ARN stored (first successful if default fails)


### Step 5: Create Shared Resources Method

**File**: `infra-cdk/lib/backend-stack.ts`

**Purpose**: Extract shared resource creation into reusable method

**Implementation**:
```typescript
/**
 * Shared resources used by all agents in multi-agent patterns.
 */
interface SharedAgentResources {
  memory: cdk.CfnResource;
  memoryId: string;
  memoryArn: string;
  agentRole: AgentCoreRole;
}

/**
 * Creates shared backend resources used by all agents.
 * These resources are created once and shared across all agent runtimes.
 * 
 * @param config - Application configuration
 * @returns Shared resources object
 */
private createSharedAgentResources(config: AppConfig): SharedAgentResources {
  // Create AgentCore execution role
  const agentRole = new AgentCoreRole(this, "AgentCoreRole")

  // Create memory resource with long-term memory strategies
  const memory = new cdk.CfnResource(this, "AgentMemory", {
    type: "AWS::BedrockAgentCore::Memory",
    properties: {
      Name: cdk.Names.uniqueResourceName(this, { maxLength: 48 }),
      EventExpiryDuration: 30,
      Description: `Memory with long-term strategies for ${config.stack_name_base}`,
      MemoryStrategies: [
        {
          SummaryMemoryStrategy: {
            Name: "SessionSummarizer",
            Namespaces: ["/summaries/{actorId}/{sessionId}"],
          },
        },
        {
          UserPreferenceMemoryStrategy: {
            Name: "PreferenceLearner",
            Namespaces: ["/preferences/{actorId}"],
          },
        },
        {
          SemanticMemoryStrategy: {
            Name: "FactExtractor",
            Namespaces: ["/facts/{actorId}"],
          },
        },
      ],
      MemoryExecutionRoleArn: agentRole.roleArn,
      Tags: {
        Name: `${config.stack_name_base}_Memory`,
        ManagedBy: "CDK",
      },
    },
  })
  
  const memoryId = memory.getAtt("MemoryId").toString()
  const memoryArn = memory.getAtt("MemoryArn").toString()

  // Store the memory ARN for access from main stack
  this.memoryArn = memoryArn

  // Add memory-specific permissions to agent role
  agentRole.addToPolicy(
    new iam.PolicyStatement({
      sid: "MemoryResourceAccess",
      effect: iam.Effect.ALLOW,
      actions: [
        "bedrock-agentcore:CreateEvent",
        "bedrock-agentcore:GetEvent",
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:RetrieveMemoryRecords",
      ],
      resources: [memoryArn],
    })
  )

  // Add SSM permissions for Gateway URL lookup
  agentRole.addToPolicy(
    new iam.PolicyStatement({
      sid: "SSMParameterAccess",
      effect: iam.Effect.ALLOW,
      actions: ["ssm:GetParameter", "ssm:GetParameters"],
      resources: [
        `arn:aws:ssm:${this.region}:${this.account}:parameter/${config.stack_name_base}/*`,
      ],
    })
  )

  // Add Code Interpreter permissions
  agentRole.addToPolicy(
    new iam.PolicyStatement({
      sid: "CodeInterpreterAccess",
      effect: iam.Effect.ALLOW,
      actions: [
        "bedrock-agentcore:StartCodeInterpreterSession",
        "bedrock-agentcore:StopCodeInterpreterSession",
        "bedrock-agentcore:InvokeCodeInterpreter",
      ],
      resources: [`arn:aws:bedrock-agentcore:${this.region}:aws:code-interpreter/*`],
    })
  )

  // Output memory ARN
  new cdk.CfnOutput(this, "MemoryArn", {
    description: "ARN of the shared agent memory resource",
    value: memoryArn,
  })

  return {
    memory,
    memoryId,
    memoryArn,
    agentRole,
  }
}
```

**Note**: Gateway and Cognito are already created in separate methods and are automatically shared.


### Step 6: Create Individual Agent Runtime

**File**: `infra-cdk/lib/backend-stack.ts`

**Purpose**: Create a single agent runtime with agent-specific configuration

**Implementation**:
```typescript
/**
 * Creates a single AgentCore Runtime for one agent in a multi-agent pattern.
 * 
 * @param config - Application configuration
 * @param pattern - Pattern name
 * @param agentEntry - Agent metadata from manifest
 * @param sharedResources - Shared resources (memory, role)
 * @param deploymentType - Deployment type (docker or zip)
 * @returns Created runtime instance
 */
private createAgentRuntime(
  config: AppConfig,
  pattern: string,
  agentEntry: AgentManifestEntry,
  sharedResources: SharedAgentResources,
  deploymentType: DeploymentType
): agentcore.Runtime {
  const stack = cdk.Stack.of(this)
  const agentName = agentEntry.name

  // Create agent-specific runtime artifact
  let agentRuntimeArtifact: agentcore.AgentRuntimeArtifact

  if (deploymentType === "zip") {
    // ZIP deployment for this agent
    agentRuntimeArtifact = this.createZipArtifact(
      config,
      pattern,
      agentName
    )
  } else {
    // Docker deployment for this agent
    agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
      path.resolve(__dirname, "..", ".."),
      {
        platform: ecr_assets.Platform.LINUX_ARM64,
        file: `patterns/${pattern}/agents/${agentName}/Dockerfile`,
      }
    )
  }

  // Configure network mode (default to public)
  const networkConfiguration = agentcore.RuntimeNetworkConfiguration.usingPublicNetwork()

  // Configure JWT authorizer with Cognito
  const authorizerConfiguration = agentcore.RuntimeAuthorizerConfiguration.usingJWT(
    `https://cognito-idp.${stack.region}.amazonaws.com/${this.userPoolId}/.well-known/openid-configuration`,
    [this.userPoolClientId]
  )

  // Environment variables for the runtime
  const envVars: { [key: string]: string } = {
    AWS_REGION: stack.region,
    AWS_DEFAULT_REGION: stack.region,
    MEMORY_ID: sharedResources.memoryId,
    STACK_NAME: config.stack_name_base,
    AGENT_NAME: agentName, // Agent can use this to identify itself
  }

  // Create the runtime
  const runtime = new agentcore.Runtime(this, `Runtime-${agentName}`, {
    runtimeName: `${config.stack_name_base.replace(/-/g, "_")}_${agentName}`,
    agentRuntimeArtifact: agentRuntimeArtifact,
    executionRole: sharedResources.agentRole,
    networkConfiguration: networkConfiguration,
    protocolConfiguration: agentcore.ProtocolType.HTTP,
    environmentVariables: envVars,
    authorizerConfiguration: authorizerConfiguration,
    requestHeaderConfiguration: {
      allowlistedHeaders: ["Authorization"],
    },
    description: `${agentEntry.displayName} - ${agentEntry.description}`,
  })

  return runtime
}
```

**Key features**:
- Agent-specific Dockerfile path for Docker deployment
- Agent name included in environment variables
- Shared role and memory used across all agents
- Unique runtime name per agent


### Step 7: Store Agent Metadata in SSM

**File**: `infra-cdk/lib/backend-stack.ts`

**Implementation**:
```typescript
/**
 * Stores agent metadata in SSM Parameter Store for runtime discovery.
 * Used by backend services and will be used by frontend in Task 8.
 * 
 * @param config - Application configuration
 * @param agentEntry - Agent metadata from manifest
 * @param runtime - Created runtime instance
 * @param status - Deployment status ('success' or 'failed')
 */
private storeAgentMetadata(
  config: AppConfig,
  agentEntry: AgentManifestEntry,
  runtime: agentcore.Runtime,
  status: 'success' | 'failed'
): void {
  const agentName = agentEntry.name
  const baseParam = `/${config.stack_name_base}/agents/${agentName}`

  // Runtime ARN
  new ssm.StringParameter(this, `AgentRuntimeArn-${agentName}`, {
    parameterName: `${baseParam}/runtime-arn`,
    stringValue: runtime.agentRuntimeArn,
    description: `Runtime ARN for ${agentEntry.displayName}`,
  })

  // Runtime ID
  new ssm.StringParameter(this, `AgentRuntimeId-${agentName}`, {
    parameterName: `${baseParam}/runtime-id`,
    stringValue: runtime.agentRuntimeId,
    description: `Runtime ID for ${agentEntry.displayName}`,
  })

  // Display name
  new ssm.StringParameter(this, `AgentDisplayName-${agentName}`, {
    parameterName: `${baseParam}/display-name`,
    stringValue: agentEntry.displayName,
    description: `Display name for ${agentName} agent`,
  })

  // Description
  new ssm.StringParameter(this, `AgentDescription-${agentName}`, {
    parameterName: `${baseParam}/description`,
    stringValue: agentEntry.description,
    description: `Description for ${agentName} agent`,
  })

  // Is default flag
  new ssm.StringParameter(this, `AgentIsDefault-${agentName}`, {
    parameterName: `${baseParam}/is-default`,
    stringValue: agentEntry.isDefault.toString(),
    description: `Whether ${agentName} is the default agent`,
  })

  // Deployment status
  new ssm.StringParameter(this, `AgentStatus-${agentName}`, {
    parameterName: `${baseParam}/status`,
    stringValue: status,
    description: `Deployment status for ${agentName} agent`,
  })
}

/**
 * Stores failure metadata for agents that failed to deploy.
 * 
 * @param config - Application configuration
 * @param agentEntry - Agent metadata from manifest
 * @param errorMessage - Error message from deployment failure
 */
private storeAgentFailureMetadata(
  config: AppConfig,
  agentEntry: AgentManifestEntry,
  errorMessage: string
): void {
  const agentName = agentEntry.name
  const baseParam = `/${config.stack_name_base}/agents/${agentName}`

  // Deployment status
  new ssm.StringParameter(this, `AgentStatus-${agentName}`, {
    parameterName: `${baseParam}/status`,
    stringValue: 'failed',
    description: `Deployment status for ${agentName} agent`,
  })

  // Error message
  new ssm.StringParameter(this, `AgentError-${agentName}`, {
    parameterName: `${baseParam}/error`,
    stringValue: errorMessage.substring(0, 4096), // SSM limit
    description: `Error message for failed ${agentName} agent deployment`,
  })

  // Display name (for UI to show failed agent)
  new ssm.StringParameter(this, `AgentDisplayName-${agentName}`, {
    parameterName: `${baseParam}/display-name`,
    stringValue: agentEntry.displayName,
    description: `Display name for ${agentName} agent`,
  })
}
```

**Note**: Task 8 will implement frontend discovery by calling AgentCore Runtime API. SSM parameters are primarily for backend access and debugging.


### Step 8: Create CloudFormation Outputs

**File**: `infra-cdk/lib/backend-stack.ts`

**Implementation**:
```typescript
/**
 * Creates CloudFormation outputs for agent runtime information.
 * 
 * @param config - Application configuration
 * @param agentEntry - Agent metadata from manifest
 * @param runtime - Created runtime instance
 * @param status - Deployment status
 */
private createAgentOutputs(
  config: AppConfig,
  agentEntry: AgentManifestEntry,
  runtime: agentcore.Runtime,
  status: 'success' | 'failed'
): void {
  const agentName = agentEntry.name

  new cdk.CfnOutput(this, `AgentRuntimeArn-${agentName}`, {
    description: `ARN of ${agentEntry.displayName} runtime`,
    value: runtime.agentRuntimeArn,
    exportName: `${config.stack_name_base}-AgentRuntimeArn-${agentName}`,
  })

  new cdk.CfnOutput(this, `AgentRuntimeId-${agentName}`, {
    description: `ID of ${agentEntry.displayName} runtime`,
    value: runtime.agentRuntimeId,
    exportName: `${config.stack_name_base}-AgentRuntimeId-${agentName}`,
  })

  new cdk.CfnOutput(this, `AgentStatus-${agentName}`, {
    description: `Deployment status of ${agentEntry.displayName}`,
    value: status,
    exportName: `${config.stack_name_base}-AgentStatus-${agentName}`,
  })
}

/**
 * Creates CloudFormation outputs for failed agent deployments.
 * 
 * @param config - Application configuration
 * @param agentEntry - Agent metadata from manifest
 * @param errorMessage - Error message from deployment failure
 */
private createAgentFailureOutputs(
  config: AppConfig,
  agentEntry: AgentManifestEntry,
  errorMessage: string
): void {
  const agentName = agentEntry.name

  new cdk.CfnOutput(this, `AgentStatus-${agentName}`, {
    description: `Deployment status of ${agentEntry.displayName}`,
    value: 'failed',
    exportName: `${config.stack_name_base}-AgentStatus-${agentName}`,
  })

  new cdk.CfnOutput(this, `AgentError-${agentName}`, {
    description: `Error for ${agentEntry.displayName}`,
    value: errorMessage.substring(0, 200), // CloudFormation output limit
    exportName: `${config.stack_name_base}-AgentError-${agentName}`,
  })
}
```


### Step 9: Handle ZIP Deployment for Multi-Agent

**File**: `infra-cdk/lib/backend-stack.ts`

**Purpose**: Support ZIP deployment type for individual agents

**Implementation**:
```typescript
/**
 * Creates ZIP deployment artifact for a specific agent.
 * 
 * @param config - Application configuration
 * @param pattern - Pattern name
 * @param agentName - Name of the agent
 * @returns Agent runtime artifact for ZIP deployment
 */
private createZipArtifact(
  config: AppConfig,
  pattern: string,
  agentName: string
): agentcore.AgentRuntimeArtifact {
  const repoRoot = path.resolve(__dirname, "..", "..")
  const patternDir = path.join(repoRoot, "patterns", pattern)
  const agentDir = path.join(patternDir, "agents", agentName)

  // Create S3 bucket for agent code (reuse if exists)
  const bucketId = `AgentCodeBucket-${agentName}`
  let agentCodeBucket: s3.Bucket
  
  try {
    agentCodeBucket = this.node.tryFindChild(bucketId) as s3.Bucket
  } catch {
    agentCodeBucket = new s3.Bucket(this, bucketId, {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      versioned: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    })
  }

  // Lambda to package agent code
  const packagerLambda = new lambda.Function(this, `ZipPackagerLambda-${agentName}`, {
    runtime: lambda.Runtime.PYTHON_3_12,
    handler: "index.handler",
    code: lambda.Code.fromAsset(path.join(__dirname, "..", "lambdas", "zip-packager")),
    timeout: cdk.Duration.minutes(10),
    memorySize: 1024,
    ephemeralStorageSize: cdk.Size.gibibytes(2),
  })

  agentCodeBucket.grantReadWrite(packagerLambda)

  // Read agent code files and encode as base64
  const agentCode: Record<string, string> = {}
  
  // Read agent-specific .py files
  for (const file of fs.readdirSync(agentDir)) {
    if (file.endsWith(".py")) {
      const content = fs.readFileSync(path.join(agentDir, file))
      agentCode[file] = content.toString("base64")
    }
  }

  // Read shared modules (gateway/, tools/, patterns/utils/)
  for (const module of ["gateway", "tools"]) {
    const moduleDir = path.join(repoRoot, module)
    if (fs.existsSync(moduleDir)) {
      this.readDirRecursive(moduleDir, module, agentCode)
    }
  }
  
  // Read pattern-specific tools
  const patternToolsDir = path.join(patternDir, "tools")
  if (fs.existsSync(patternToolsDir)) {
    this.readDirRecursive(patternToolsDir, "tools", agentCode)
  }

  // Read requirements
  const requirementsPath = path.join(patternDir, "requirements.txt")
  const requirements = fs.readFileSync(requirementsPath, "utf-8")
    .split("\n")
    .map(line => line.trim())
    .filter(line => line && !line.startsWith("#"))

  // Create hash for change detection
  const contentHash = this.hashContent(JSON.stringify({ requirements, agentCode }))

  // Custom Resource to trigger packaging
  const provider = new cr.Provider(this, `ZipPackagerProvider-${agentName}`, {
    onEventHandler: packagerLambda,
  })

  const zipPackagerResource = new cdk.CustomResource(this, `ZipPackager-${agentName}`, {
    serviceToken: provider.serviceToken,
    properties: {
      BucketName: agentCodeBucket.bucketName,
      ObjectKey: `${agentName}_deployment_package.zip`,
      Requirements: requirements,
      AgentCode: agentCode,
      ContentHash: contentHash,
    },
  })

  return agentcore.AgentRuntimeArtifact.fromS3(
    {
      bucketName: agentCodeBucket.bucketName,
      objectKey: `${agentName}_deployment_package.zip`,
    },
    agentcore.AgentCoreRuntime.PYTHON_3_12,
    ["opentelemetry-instrument", `${agentName}_agent.py`]
  )
}
```

**Note**: Each agent gets its own ZIP package with agent-specific code.


## Files to Modify

### 1. infra-cdk/lib/utils/agent-manifest.ts (NEW)
**Purpose**: Agent manifest interfaces and validation logic
**Changes**: Create new file with TypeScript interfaces and validation functions

### 2. infra-cdk/lib/backend-stack.ts (MODIFY)
**Purpose**: Main CDK stack implementation
**Changes**:
- Import agent-manifest utilities
- Refactor `createAgentCoreRuntime()` to detect multi-agent patterns
- Extract existing logic to `createSingleAgentRuntime()` method
- Add `createMultiAgentRuntimes()` method
- Add `createSharedAgentResources()` method
- Add `createAgentRuntime()` method
- Add `storeAgentMetadata()` method
- Add `createAgentOutputs()` method
- Update `createZipArtifact()` for per-agent ZIP deployment

### 3. infra-cdk/config.yaml (MODIFY - for testing)
**Purpose**: Configuration file for deployment
**Changes**: Update to use single pattern mode for testing
```yaml
stack_name_base: marodon-fast
admin_user_email: null

backend:
  pattern: strands-multi-agent-orchestrator  # Single pattern mode
  deployment_type: docker
```

### 4. infra-cdk/test/agent-manifest.test.ts (NEW)
**Purpose**: Unit tests for agent manifest validation
**Changes**: Create comprehensive test suite


## Testing Strategy

### Phase 1: Unit Testing

**Test file**: `infra-cdk/test/agent-manifest.test.ts`

**Test cases**:
1. ✅ Valid manifest with all required fields
2. ✅ Missing agents array
3. ✅ Empty agents array
4. ✅ Missing required field (name, displayName, description, runtimeId)
5. ✅ Empty string for required field
6. ✅ Invalid isDefault type (not boolean)
7. ✅ No default agent (all isDefault: false)
8. ✅ Multiple default agents
9. ✅ Manifest file not found
10. ✅ Malformed JSON

**Run tests**:
```bash
cd infra-cdk
npm test
```

### Phase 2: CDK Synthesis Testing

**Purpose**: Verify CDK can synthesize CloudFormation template without errors

**Steps**:
1. Update config.yaml to use `pattern: strands-multi-agent-orchestrator`
2. Run CDK synthesis:
```bash
cd infra-cdk
npm run build
npx cdk synth
```

**Expected results**:
- ✅ Synthesis completes without errors
- ✅ CloudFormation template includes 4 AgentCore Runtime resources
- ✅ CloudFormation template includes 1 Memory resource (shared)
- ✅ CloudFormation template includes 1 Gateway resource (shared)
- ✅ SSM parameters created for each agent
- ✅ Outputs created for each agent

### Phase 3: Validation Testing

**Purpose**: Verify error handling for invalid configurations

**Test scenarios**:
1. **Missing agents.json**: Remove agents.json and verify deployment fails with clear error
2. **Invalid agent directory**: Reference non-existent agent in manifest
3. **Missing Dockerfile**: Remove Dockerfile for one agent
4. **Malformed manifest**: Invalid JSON in agents.json

**Expected behavior**: Deployment fails fast with descriptive error messages

### Phase 4: Deployment Testing (Optional - requires AWS account)

**Purpose**: Verify actual deployment to AWS

**Steps**:
1. Deploy to test environment:
```bash
cd infra-cdk
npx cdk deploy --all
```

2. Verify resources created:
   - Check CloudFormation console for all stacks
   - Verify 4 AgentCore Runtimes exist
   - Verify SSM parameters exist for each agent
   - Check CloudWatch logs for runtime initialization

3. Test agent invocation:
   - Use AWS CLI or SDK to invoke each runtime
   - Verify each agent responds correctly

### Phase 5: Linting and Formatting

**Purpose**: Ensure code quality standards

**Steps**:
```bash
cd infra-cdk
npm run build
npm run lint
```

**Expected**: No linting errors or warnings


## Deployment Validation Checklist

After implementation, verify the following:

### CloudFormation Resources
- [ ] 4 `AWS::BedrockAgentCore::Runtime` resources created (one per agent)
- [ ] 1 `AWS::BedrockAgentCore::Memory` resource created (shared)
- [ ] 1 `AWS::BedrockAgentCore::Gateway` resource created (shared)
- [ ] 4 ECR repositories created (one per agent, if Docker deployment)
- [ ] IAM role created with appropriate permissions

### SSM Parameters
- [ ] `/${stackName}/agents/orchestrator/runtime-arn`
- [ ] `/${stackName}/agents/orchestrator/runtime-id`
- [ ] `/${stackName}/agents/orchestrator/display-name`
- [ ] `/${stackName}/agents/orchestrator/description`
- [ ] `/${stackName}/agents/orchestrator/is-default`
- [ ] `/${stackName}/agents/orchestrator/status` (success/failed)
- [ ] Same parameters for colorado, umich, coder agents
- [ ] Failed agents have `/${stackName}/agents/${agentName}/error` parameter

### CloudFormation Outputs
- [ ] `AgentRuntimeArn-orchestrator`
- [ ] `AgentRuntimeId-orchestrator`
- [ ] `AgentStatus-orchestrator` (success/failed)
- [ ] `AgentRuntimeArn-colorado`
- [ ] `AgentRuntimeId-colorado`
- [ ] `AgentStatus-colorado` (success/failed)
- [ ] `AgentRuntimeArn-umich`
- [ ] `AgentRuntimeId-umich`
- [ ] `AgentStatus-umich` (success/failed)
- [ ] `AgentRuntimeArn-coder`
- [ ] `AgentRuntimeId-coder`
- [ ] `AgentStatus-coder` (success/failed)
- [ ] `DeploymentSummary` (total, successful, failed counts)
- [ ] `MemoryArn` (shared memory)
- [ ] `GatewayUrl` (shared gateway)
- [ ] Failed agents have `AgentError-${agentName}` output

### Docker Images (if Docker deployment)
- [ ] Image built for orchestrator agent
- [ ] Image built for colorado agent
- [ ] Image built for umich agent
- [ ] Image built for coder agent
- [ ] All images pushed to ECR successfully

### Runtime Configuration
- [ ] Each runtime has correct environment variables (MEMORY_ID, STACK_NAME, AGENT_NAME)
- [ ] Each runtime uses shared IAM role
- [ ] Each runtime has JWT authorizer configured
- [ ] Each runtime has request header configuration for Authorization header
- [ ] **AgentCore Runtime provides endpoints directly** (no API Gateway routes needed)
- [ ] Failed agents are marked in SSM with status='failed' and error message


## Risks and Mitigation Strategies

### Risk 1: Docker Build Context Size
**Description**: Building from repository root may include large files

**Mitigation**:
- ✅ Already mitigated: `.dockerignore` file excludes node_modules, .git, cdk.out
- Verify .dockerignore is comprehensive
- Monitor build times during testing

### Risk 2: Agent Dockerfile Path Resolution
**Description**: Nested Dockerfile paths may cause build issues

**Mitigation**:
- Use absolute paths in CDK: `path.resolve(__dirname, "..", "..")`
- Validate Dockerfile exists before attempting build (fail-fast)
- Test with actual pattern structure during development

### Risk 3: SSM Parameter Naming Conflicts
**Description**: Parameter names must be unique and consistent

**Mitigation**:
- Use consistent naming pattern: `/${stackName}/agents/${agentName}/*`
- Validate no conflicts with existing parameters
- Document parameter structure clearly

### Risk 4: Shared Resource Contention
**Description**: Multiple agents accessing shared Memory/Gateway simultaneously

**Mitigation**:
- ✅ Already handled: AgentCore Memory and Gateway are designed for concurrent access
- Session prefixing ensures isolation
- Monitor CloudWatch metrics for throttling

### Risk 5: Partial Deployment Failures
**Description**: One or more agents may fail to deploy

**Mitigation**:
- ✅ **IMPLEMENTED**: Graceful degradation with try-catch per agent
- Failed agents logged with warnings, not errors
- Deployment continues if at least one agent succeeds
- UI can show failed agents as "unhealthy" or hide them
- Orchestrator gracefully handles unavailable agents

### Risk 6: Runtime Deployment Order
**Description**: Agents may have dependencies on each other

**Mitigation**:
- All agents deployed in parallel (no dependencies)
- Orchestrator can invoke specialists via runtime endpoints (stored in SSM)
- No circular dependencies in architecture


## User Decisions - RESOLVED

All open questions have been resolved by the user. Key decisions:

### 1. Backward Compatibility: NOT NEEDED ✅
- **Decision**: Remove all backward compatibility considerations for `agents[]` array
- **Rationale**: The old approach was never deployed to production
- **Implementation**: Simplify by only supporting single pattern mode
- **Impact**: Cleaner code, no legacy support needed

### 2. AgentCore Runtime Architecture ✅
- **Decision**: AgentCore Runtime provides endpoints directly (no API Gateway needed)
- **Architecture**: Runtime is "Lambda for agents" - single service per AWS account
- Each agent gets its own endpoint within the Runtime service
- Runtime provides secure, serverless, scalable endpoints
- Each agent has a single `@app.endpoint` entry point (like Lambda handler)
- Agents can run from seconds up to 8 hours
- Runtime integrates with AgentCore Memory, Identity, Observability
- **Implementation**: NO API Gateway routes needed in CDK stack

### 3. Orchestrator Deployment: DEPLOY WITH OTHER AGENTS ✅
- **Decision**: Orchestrator is deployed alongside specialist agents
- **Architecture**: Orchestrator treats other agents as tools/sub-agents it can call
- All agents (including orchestrator) deployed from the manifest
- Future patterns may customize this for specific business problems
- **Implementation**: Deploy all agents in parallel from agents.json

### 4. Frontend Discovery: RUNTIME API + AGENT GALLERY ✅
- **Decision**: Frontend discovers agents by calling AgentCore Runtime API
- **UI Pattern**: Display agents as tiles in an agent gallery (like local deployment)
- Each tile shows: agent name, metadata, available tools, LLM, system prompt
- Users can click tile for details page, then click 'chat' to start conversation
- Orchestrator appears as one tile - users can chat with orchestrator OR directly with specialists
- **Task 7 Implementation**: Store agent metadata in SSM for backend access
- **Task 8 Implementation**: Frontend discovery via Runtime API (future work)

### 5. Partial Failures: GRACEFUL DEGRADATION ✅
- **Decision**: Deployment should continue even if one agent fails
- Failed agents should log errors and warnings but not block other agents
- UI should show failed agent as "unhealthy" tile or hide it
- Orchestrator should gracefully handle unavailable agents/tools
- **Implementation**: 
  - Use try-catch per agent in deployment loop
  - Store failure status in SSM with error message
  - Create CloudFormation outputs showing deployment status
  - Fail deployment only if ALL agents fail
  - At least one successful agent required


## Implementation Timeline

### Phase 1: Core Infrastructure (2-3 hours)
- [ ] Create agent-manifest.ts with interfaces and validation
- [ ] Write unit tests for manifest validation
- [ ] Refactor createAgentCoreRuntime() to detect multi-agent patterns
- [ ] Extract existing logic to createSingleAgentRuntime()

### Phase 2: Multi-Agent Runtime Creation (3-4 hours)
- [ ] Implement createSharedAgentResources()
- [ ] Implement createMultiAgentRuntimes() with graceful degradation
- [ ] Implement createAgentRuntime()
- [ ] Handle Docker deployment for each agent
- [ ] Handle ZIP deployment for each agent (if needed)
- [ ] Add try-catch error handling per agent
- [ ] Add deployment status tracking

### Phase 3: Metadata and Outputs (1-2 hours)
- [ ] Implement storeAgentMetadata() with status parameter
- [ ] Implement storeAgentFailureMetadata()
- [ ] Implement createAgentOutputs() with status
- [ ] Implement createAgentFailureOutputs()
- [ ] Add deployment summary output

### Phase 4: Testing and Validation (2-3 hours)
- [ ] Run unit tests
- [ ] Test CDK synthesis
- [ ] Validate error handling
- [ ] Run linting and formatting
- [ ] Update config.yaml for testing

### Phase 5: Documentation (1 hour)
- [ ] Update infra-cdk/README.md with multi-agent pattern info
- [ ] Update docs/DEPLOYMENT.md with migration guide
- [ ] Document SSM parameter structure
- [ ] Add troubleshooting section

**Total estimated time**: 9-13 hours


## Success Criteria

### Functional Requirements
- ✅ CDK stack reads agents.json manifest from pattern directory
- ✅ Separate AgentCore Runtime created for each agent in manifest
- ✅ Each agent has its own Docker image built from agent-specific Dockerfile
- ✅ Shared resources (Memory, Gateway, Cognito) created once and shared
- ✅ Agent metadata stored in SSM Parameter Store with deployment status
- ✅ CloudFormation outputs include all agent endpoints and deployment status
- ✅ Graceful degradation for partial deployment failures
- ✅ Deployment continues if at least one agent succeeds
- ✅ Failed agents marked in SSM and CloudFormation outputs
- ✅ No API Gateway routes created (Runtime provides endpoints)
- ✅ Backward compatibility with single-agent patterns maintained

### Quality Requirements
- ✅ All unit tests pass
- ✅ CDK synthesis completes without errors
- ✅ No linting errors or warnings
- ✅ Code follows TypeScript best practices
- ✅ All functions have proper docstrings
- ✅ Error messages are clear and actionable

### Documentation Requirements
- ✅ Implementation plan reviewed and approved ✅ **APPROVED - READY FOR IMPLEMENTATION**
- ✅ Code comments explain non-obvious logic
- ✅ README updated with multi-agent pattern information
- ✅ User decisions documented in plan

### Validation Requirements
- ✅ Manifest validation catches all error cases
- ✅ Deployment fails fast with descriptive errors for invalid manifests
- ✅ Deployment continues with warnings for individual agent failures
- ✅ CloudFormation template structure is correct
- ✅ SSM parameters follow consistent naming convention
- ✅ At least one agent must deploy successfully


## Next Steps

### Immediate Actions
1. **Review this plan** with the user for approval
2. **Answer open questions** (see Questions for User Review section)
3. **Verify pattern structure** - Confirm agents.json and Dockerfiles exist

### After Approval
1. **Create agent-manifest.ts** with validation logic
2. **Write unit tests** for manifest validation
3. **Refactor backend-stack.ts** following the implementation steps
4. **Test CDK synthesis** to verify CloudFormation template
5. **Run linting** to ensure code quality
6. **Update documentation** with new approach

### Before Deployment
1. **Update config.yaml** to use single pattern mode
2. **Verify all agent Dockerfiles** are present and valid
3. **Test in development environment** if possible
4. **Review CloudFormation template** for correctness
5. **Prepare rollback plan** in case of issues

## References

### Design Document
- `.kiro/specs/multi-agent-orchestration-pattern/design.md`
- Requirements 2.1, 2.2, 2.3, 2.4, 4.2, 4.3, 4.4, 11.2

### Existing Code
- `infra-cdk/lib/backend-stack.ts` - Current implementation
- `infra-cdk/lib/utils/config-manager.ts` - Config validation
- `patterns/strands-multi-agent-orchestrator/agents.json` - Agent manifest

### AWS Documentation
- [AWS CDK TypeScript Reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html)
- [Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)

---

**Plan created**: Ready for user review and approval before implementation begins.

---

## PLAN STATUS: ✅ APPROVED - READY FOR IMPLEMENTATION

**Approval Date**: User decisions incorporated and plan finalized

**Key Changes from User Decisions**:
1. ✅ **Backward compatibility removed** - `agents[]` array never deployed, simplified implementation
2. ✅ **No API Gateway routes** - AgentCore Runtime provides endpoints directly
3. ✅ **Orchestrator deployed with specialists** - All agents from manifest deployed in parallel
4. ✅ **Frontend discovery deferred to Task 8** - SSM metadata for backend access only
5. ✅ **Graceful degradation implemented** - Partial failures don't block deployment

**Implementation Ready**: All open questions resolved, plan approved for execution

**Next Action**: Begin Phase 1 implementation (Core Infrastructure)

