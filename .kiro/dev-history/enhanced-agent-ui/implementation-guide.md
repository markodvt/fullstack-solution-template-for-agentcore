# Agent Metadata Enhancement - Implementation Guide

**Date:** March 1, 2026  
**Status:** Ready for Implementation  
**Estimated Time:** 60-90 minutes

---

## Overview

Implement S3-based storage for agent source code with metadata extraction (tools, model ID) during CDK deployment.

## Problem

3 out of 4 agent files exceed SSM's 8KB limit:
- orchestrator_agent.py: 10.6 KB ❌
- umich_agent.py: 8.3 KB ❌  
- coder_agent.py: 9.7 KB ❌
- colorado_agent.py: 7.7 KB ✅

## Solution

Store source code in S3, metadata in SSM, generate presigned URLs in Lambda.

---

## Step 1: Modify backend-stack.ts

### 1.1 Add Import
At top of file (line ~9):
```typescript
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment"
```

### 1.2 Add S3 Bucket to createSharedAgentResources()
After Code Interpreter permissions (~line 1185):
```typescript
// Create S3 bucket for agent source code
const agentSourceCodeBucket = new s3.Bucket(this, "AgentSourceCodeBucket", {
  bucketName: `${config.stack_name_base}-agent-source-code`,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  autoDeleteObjects: true,
  versioned: true,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  encryption: s3.BucketEncryption.S3_MANAGED,
})
```

Update return statement (~line 1195):
```typescript
return {
  memory,
  memoryId,
  memoryArn,
  agentRole,
  agentSourceCodeBucket,  // ADD
}
```

### 1.3 Update SharedAgentResources Interface
Bottom of file (~line 1444):
```typescript
interface SharedAgentResources {
  memory: cdk.CfnResource
  memoryId: string
  memoryArn: string
  agentRole: AgentCoreRole
  agentSourceCodeBucket: s3.Bucket  // ADD
}
```

### 1.4 Add Metadata Extraction Method
After hashContent() (~line 973):
```typescript
private extractAgentMetadata(agentFilePath: string): {
  tools: string[]
  modelId: string
} {
  try {
    const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')
    
    // Extract tools
    const toolsMatch = sourceCode.match(/tools\s*=\s*\[([\s\S]*?)\]/m)
    let tools: string[] = []
    
    if (toolsMatch) {
      tools = toolsMatch[1]
        .split(',')
        .map(t => t.trim().replace(/['"]/g, ''))
        .filter(t => t && !t.startsWith('#'))
        .map(t => t.includes('.') ? t.split('.').pop() || t : t)
        .filter(Boolean)
    }
    
    // Extract model
    const modelMatch = sourceCode.match(/model_id\s*=\s*["']([^"']+)["']/)
    const modelId = modelMatch ? modelMatch[1] : 'unknown'
    
    return { tools, modelId }
  } catch (error) {
    console.warn(`Failed to extract metadata:`, error)
    return { tools: [], modelId: 'unknown' }
  }
}
```

### 1.5 Add S3 Upload Method
After extractAgentMetadata():
```typescript
private uploadAgentSourceToS3(
  bucket: s3.Bucket,
  agentName: string,
  sourceCode: string
): string {
  const s3Key = `agents/${agentName}/${agentName}_agent.py`
  
  new s3deploy.BucketDeployment(this, `AgentSourceDeploy-${agentName}`, {
    sources: [s3deploy.Source.data(s3Key, sourceCode)],
    destinationBucket: bucket,
    prune: false,
  })
  
  return `s3://${bucket.bucketName}/${s3Key}`
}
```

### 1.6 Update storeAgentMetadata()
Add parameter to signature (~line 1280):
```typescript
private storeAgentMetadata(
  config: AppConfig,
  pattern: string,
  agentEntry: AgentManifestEntry,
  runtime: agentcore.Runtime,
  status: "success" | "failed",
  sharedResources: SharedAgentResources  // ADD
): void {
```

Add metadata extraction at start of method:
```typescript
const agentName = agentEntry.name
const baseParam = `/${config.stack_name_base}/agents/${agentName}`

// Extract metadata
const patternPath = path.resolve(__dirname, "..", "..", "patterns", pattern)
const agentFilePath = path.join(patternPath, "agents", agentName, `${agentName}_agent.py`)

let metadata = { tools: [], modelId: 'unknown' }
let sourceCodeUrl = ''

try {
  if (fs.existsSync(agentFilePath)) {
    metadata = this.extractAgentMetadata(agentFilePath)
    const sourceCode = fs.readFileSync(agentFilePath, 'utf-8')
    sourceCodeUrl = this.uploadAgentSourceToS3(
      sharedResources.agentSourceCodeBucket,
      agentName,
      sourceCode
    )
  }
} catch (error) {
  console.warn(`Failed to process metadata for ${agentName}:`, error)
}
```

Add new SSM parameters before closing brace:
```typescript
// Tools
new ssm.StringParameter(this, `SSMAgentTools-${agentName}`, {
  parameterName: `${baseParam}/tools`,
  stringValue: JSON.stringify(metadata.tools),
  description: `Tools for ${agentName}`,
})

// Model
new ssm.StringParameter(this, `SSMAgentModel-${agentName}`, {
  parameterName: `${baseParam}/model`,
  stringValue: metadata.modelId,
  description: `Model for ${agentName}`,
})

// Source code URL
if (sourceCodeUrl) {
  new ssm.StringParameter(this, `SSMAgentSourceCodeUrl-${agentName}`, {
    parameterName: `${baseParam}/source-code-url`,
    stringValue: sourceCodeUrl,
    description: `S3 URL for ${agentName} source`,
  })
}
```

### 1.7 Update storeAgentMetadata Call
In createMultiAgentRuntimes() (~line 1037):
```typescript
// Change from:
this.storeAgentMetadata(config, pattern, agentEntry, runtime, "success")

// To:
this.storeAgentMetadata(config, pattern, agentEntry, runtime, "success", sharedResources)
```

---

## Step 2: Modify agent-discovery Lambda

### 2.1 Add S3 Client
In index.py (~line 30):
```python
ssm_client = boto3.client("ssm")
s3_client = boto3.client("s3")  # ADD
```

### 2.2 Update get_agent_metadata()
Add new parameter handling in the loop (~line 75):
```python
elif param_name == "tools":
    try:
        metadata["tools"] = json.loads(param_value)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse tools for {agent_name}")
        metadata["tools"] = []
elif param_name == "model":
    metadata["model"] = param_value
elif param_name == "source-code-url":
    try:
        if param_value.startswith("s3://"):
            parts = param_value[5:].split("/", 1)
            if len(parts) == 2:
                bucket, key = parts
                
                # Generate presigned URL
                metadata["sourceCodeUrl"] = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=3600
                )
                
                # Fetch source code
                obj = s3_client.get_object(Bucket=bucket, Key=key)
                metadata["sourceCode"] = obj['Body'].read().decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to get source for {agent_name}: {e}")
        metadata["sourceCode"] = None
```

### 2.3 Add S3 Permissions
In backend-stack.ts, createAgentDiscoveryApi() (~line 680):
```typescript
agentDiscoveryLambda.addToRolePolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: ["s3:GetObject", "s3:ListBucket"],
    resources: [
      `arn:aws:s3:::${config.stack_name_base}-agent-source-code/*`,
      `arn:aws:s3:::${config.stack_name_base}-agent-source-code`,
    ],
  })
)
```

---

## Step 3: Update tasks.md

Mark Phase 3 as deferred (~line 450):
```markdown
### Phase 3: Inline Chat Observability (Week 3) - DEFERRED

**Status:** Deferred - Prioritizing Phase 4 (Memory Visualization)
```

Update Phase 4 priority (~line 550):
```markdown
### Phase 4: Memory Visualization (Week 4) - NEXT PRIORITY

**Status:** Ready to implement
```

---

## Testing

```bash
# Deploy
cd infra-cdk && cdk deploy

# Verify SSM
aws ssm get-parameters-by-path --path "/<stack>/agents/umich" --recursive

# Verify S3
aws s3 ls s3://<stack>-agent-source-code/agents/

# Test API
curl -H "Authorization: Bearer <token>" https://<api>/agents | jq
```

Expected response includes:
- `tools`: ["tool1", "tool2"]
- `model`: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
- `sourceCode`: "full source code"
- `sourceCodeUrl`: "https://s3..."

---

## Success Criteria

✅ S3 bucket created with agent files  
✅ SSM parameters include tools, model, source-code-url  
✅ API returns new fields  
✅ Frontend displays tools count and source code  
✅ No deployment errors

---

**Ready for implementation!**
