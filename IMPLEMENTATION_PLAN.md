# Implementation Plan: Long-Term Memory & Multi-Agent Observability

## Overview
This plan outlines the steps to:
1. Deploy the initial FAST infrastructure with Strands pattern
2. Upgrade AgentCore Memory to support long-term memory strategies
3. Test the enhanced memory capabilities
4. Prepare for future multi-agent setup with shared long-term memory
5. Add observability UI for sessions, traces, and spans

## Current State Analysis

### What's Already Working
- **Infrastructure**: CDK setup with Strands single agent pattern
- **Memory**: Short-term memory (conversation history) configured with 30-day retention
- **Tools**: Gateway tools (text analysis) + Code Interpreter integration
- **Authentication**: Cognito-based JWT authentication
- **Frontend**: React app with streaming support

### What Needs Enhancement
- **Memory**: Currently only short-term (empty `MemoryStrategies` array)
- **Observability**: No UI for viewing sessions/traces/spans
- **Multi-agent**: Single agent only (future requirement)

## Phase 1: Initial Deployment & Testing ✅ COMPLETED

**Deployment Summary:**
- **Stack Name**: `marodon-fast`
- **Region**: `us-east-1`
- **Cognito User Pool ID**: `us-east-1_ryuJOcMLn`
- **Cognito Console**: https://console.aws.amazon.com/cognito/
- **Memory ID**: `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1`
- **Frontend URL**: https://main.dy356n1qt88fa.amplifyapp.com
- **Container Runtime**: Finch (Docker alternative) with symlink
  - Finch provides a lightweight, open-source alternative to Docker Desktop
  - Symlink created to maintain Docker CLI compatibility
  - All `docker` commands work seamlessly with Finch backend

**Phase 1 Status**: All deployment steps completed successfully. Ready to create Cognito user and proceed to Phase 2.MPLETED
```bash
### Step 1.1: Pre-Deployment Checks ✅ COMPLETED
- [x] AWS CLI configured (user: marodon+agents)
- [x] AWS CDK installed (v2.1106.1)
- [x] Node.js installed (v24.13.1)
- [x] Docker alternative: Finch installed with symlink (instead of Docker)
  - **Note**: Instead of Docker Desktop, we installed Finch and created a symlink to make it compatible with Docker commands
  - This provides a lightweight, open-source alternative to Docker Desktop
- [x] Python 3.11+ available
- [x] Review and update `infra-cdk/config.yaml`
```bash
cd ..
python scripts/deploy-frontend.py
```

### Step 1.4: Create Cognito User & Test

**Testing Checklist:**
- [ ] User can log in
- [ ] Agent responds to queries
- [ ] Gateway tools work
- [ ] Code Interpreter works
- [ ] Conversation history persists within session

## Phase 2: Upgrade to Long-Term Memory

**Prerequisites:**
- ✅ Phase 1 deployment completed
- ✅ Backend stack deployed (marodon-fast)
- ✅ Memory resource created (marodonfastmarodonfastbackend8EA31761-64aLtD8bP1)
### Step 1.4: Create Cognito User & Test

**How to Create a Cognito User:**
1. Navigate to AWS Cognito Console: https://console.aws.amazon.com/cognito/
2. Click on your user pool: **"marodon-fast-user-pool"** (ID: `us-east-1_ryuJOcMLn`)
3. Click the **"Users"** tab in the left sidebar
4. Click **"Create user"** button
5. Fill in the user details:
   - **Username**: Choose a username (e.g., `testuser` or your email)
   - **Email**: Enter a valid email address
   - **Temporary password**: Create a temporary password (or let Cognito generate one)
   - **Email verification**: Choose whether to mark email as verified
   - **Invitation message**: Choose whether to send an invitation email
6. Click **"Create user"**
7. Note the temporary password (if you created one)
## Phase 2: Upgrade to Long-Term Memory ✅ COMPLETED

**Deployment Summary:**
- Memory strategies successfully added to stack: `marodon-fast`
- Three long-term memory strategies now active:
  - SessionSummarizer: Auto-generates session summaries
  - PreferenceLearner: Learns and recalls user preferences
  - FactExtractor: Extracts and stores important facts
- Agent code updated with retrieval configuration
- System prompt enhanced to acknowledge memory capabilities
- Deployment completed successfully

**Prerequisites:**https://main.dy356n1qt88fa.amplifyapp.com
2. Log in with the username and temporary password
3. You'll be prompted to change your password on first login
4. Set a new permanent password

**Testing Checklist:**
- [ ] User can log in successfully
- [ ] Agent responds to queries
- [ ] Gateway tools work
- [ ] Code Interpreter works
- [ ] Conversation history persists within session

**Status**: Ready to proceed - user creation and testing recommended before Phase 2
- [ ] Agent responds to queries
- [ ] Gateway tools work
- [ ] Code Interpreter works
- [ ] Conversation history persists within session

**Status**: Ready to proceed - user creation and testing recommended before Phase 2
**New Configuration:**
```typescript
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
```

**Rationale:**
- **SummaryMemoryStrategy**: Auto-generates session summaries for context
- **UserPreferenceMemoryStrategy**: Learns user preferences over time
- **SemanticMemoryStrategy**: Extracts and stores important facts

### Step 2.2: Update Agent Code to Use Long-Term Memory
**File**: `patterns/strands-single-agent/basic_agent.py`

**Current Configuration:**
```python
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id, 
    session_id=session_id, 
    actor_id=user_id
)
```

**Enhanced Configuration:**
```python
from bedrock_agentcore.memory.integrations.strands.config import RetrievalConfig

agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,
    session_id=session_id,
    actor_id=user_id,
    retrieval_config={
        "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
        "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.3),
        "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=3, relevance_score=0.5)
    }
)
```

**Rationale:**
- Retrieves relevant preferences, facts, and summaries before each agent invocation
- `top_k`: Number of records to retrieve
- `relevance_score`: Minimum similarity threshold (0.0-1.0)

### Step 2.3: Update System Prompt
Enhance the agent's system prompt to acknowledge long-term memory:

```python
system_prompt = """You are a helpful assistant with access to tools via the Gateway and Code Interpreter.

You have access to:
- Short-term memory: Recent conversation history within this session
- Long-term memory: User preferences, important facts, and session summaries across all conversations

When responding:
- Reference relevant information from past conversations when appropriate
- Learn and remember user preferences
- Build on previous context to provide personalized assistance

When asked about your tools, list them and explain what they do."""
```

### Step 2.4: Deploy Memory Updates
```bash
cd infra-cdk
cdk deploy
```

**Note**: Memory resource will be updated in-place. Existing conversation history is preserved.

### Step 2.5: Test Long-Term Memory
**Test Scenarios:**
1. **Preference Learning**: Tell agent "I prefer Python over JavaScript" → Start new session → Ask "What language should I use?" → Verify it remembers
2. **Fact Extraction**: Share important info "My project is called FastAI" → New session → Ask "What's my project name?" → Verify recall
3. **Session Summaries**: Have long conversation → New session → Verify agent has context from summary

## Phase 3: Multi-Agent Preparation (Future)

### Architecture for Shared Memory
When adding multiple agents:
- All agents use the same `MEMORY_ID` (shared memory resource)
- Each agent has unique `session_id` for its conversations
- All agents share the same `actor_id` (user identifier)
- Long-term memory (preferences, facts) is shared across all agents
- Short-term memory (conversation history) is session-specific

### Example Multi-Agent Setup
```python
# Agent 1: Research Assistant
research_agent = Agent(
    name="ResearchAgent",
    system_prompt="You are a research assistant...",
    session_manager=AgentCoreMemorySessionManager(
        agentcore_memory_config=AgentCoreMemoryConfig(
            memory_id=shared_memory_id,
            session_id="research_session",
            actor_id=user_id,
            retrieval_config=shared_retrieval_config
        )
    )
)

# Agent 2: Code Assistant
code_agent = Agent(
    name="CodeAgent",
    system_prompt="You are a coding assistant...",
    session_manager=AgentCoreMemorySessionManager(
        agentcore_memory_config=AgentCoreMemoryConfig(
            memory_id=shared_memory_id,  # Same memory!
            session_id="code_session",
            actor_id=user_id,
            retrieval_config=shared_retrieval_config
        )
    )
)
```

## Phase 4: Observability UI (Future)

### Requirements
- View all sessions for a user
- Drill down into session traces
- View spans within traces
- Filter by agent, time range, status
- Search by content

### Implementation Options

**Option A: AWS X-Ray Integration**
- Strands already supports OpenTelemetry tracing
- Agent code already includes `trace_attributes`
- Need to enable X-Ray exporter in agent runtime
- Build custom UI to query X-Ray API

**Option B: Custom Observability Stack**
- Store traces in DynamoDB or OpenSearch
- Build React UI tab for visualization
- Query AgentCore Memory API for session data
- Integrate with existing frontend

**Option C: Third-Party Tools**
- Integrate with Datadog, New Relic, or Honeycomb
- Use their pre-built UIs
- Requires additional configuration and costs

### Recommended Approach
Start with **Option A (X-Ray)** because:
- Native AWS integration
- Strands already emits OpenTelemetry traces
- No additional infrastructure needed
- Can build custom UI on top of X-Ray API

### Implementation Steps (Future)
1. Enable X-Ray tracing in AgentCore Runtime
2. Configure OpenTelemetry exporter in agent code
3. Create new React component for observability tab
4. Query X-Ray API for traces and spans
5. Build visualization components (timeline, tree view, filters)

## Dependencies & Prerequisites

### Required AWS Permissions
- CloudFormation (stack creation)
- S3 (buckets for CDK, frontend)
- ECR (container registry)
- Bedrock AgentCore (runtime, memory, gateway)
- Cognito (user pools)
- IAM (roles, policies)
- SSM (parameter store)
- CloudWatch (logs)
- Amplify (hosting)

### Python Dependencies (Already in requirements.txt)
- `bedrock-agentcore[strands-agents]`
- `strands-agents`
- `boto3`

### Configuration Files to Review
- `infra-cdk/config.yaml`: Set `stack_name_base`, `admin_user_email`
- Ensure `backend.pattern` is `strands-single-agent`
- Ensure `backend.deployment_type` is `docker` (recommended)

## Testing Strategy

### Phase 1 Testing
- [ ] Backend deploys successfully
- [ ] Frontend deploys successfully
- [ ] User can log in
- [ ] Agent responds to queries
- [ ] Gateway tools work
- [ ] Code Interpreter works
- [ ] Conversation history persists within session

### Phase 2 Testing
- [ ] Long-term memory strategies are active
- [ ] Preferences are learned and recalled
- [ ] Facts are extracted and retrieved
- [ ] Session summaries are generated
- [ ] Memory persists across sessions
- [ ] Multiple sessions share long-term memory

## Rollback Plan

If issues occur:
1. **Memory issues**: Revert `MemoryStrategies` to `[]` and redeploy
2. **Agent issues**: Check CloudWatch logs for errors
3. **Complete rollback**: `cd infra-cdk && cdk destroy --force`

## Success Criteria

### Phase 1 Success
- ✅ Full stack deployed and accessible
- ✅ User can chat with agent
- ✅ Tools are functional
- ✅ Short-term memory works

### Phase 2 Success
- ✅ Long-term memory strategies active
- ✅ Agent recalls information across sessions
- ✅ User preferences are learned
- ✅ Facts are extracted and retrieved
- ✅ Session summaries provide context

## Next Steps After Approval

1. Verify Docker is running: `docker ps`
2. Review `infra-cdk/config.yaml` settings
3. Execute Phase 1 deployment
4. Test baseline functionality
5. Implement Phase 2 memory upgrades
6. Test long-term memory capabilities
7. Document findings and prepare for multi-agent expansion

## Questions for Clarification

1. **Stack Name**: What should we use for `stack_name_base` in config.yaml?
2. **Region**: Which AWS region do you prefer? (currently us-east-1)
3. **Admin Email**: Should we set `admin_user_email` for auto-user creation?
4. **Deployment Type**: Stick with `docker` (recommended) or try `zip`?
5. **Observability Timeline**: When do you want to tackle the observability UI?

## References

- [MEMORY_INTEGRATION.md](docs/MEMORY_INTEGRATION.md)
- [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [Strands Memory Integration](https://strandsagents.com/latest/documentation/docs/community/session-managers/agentcore-memory/)
- [AgentCore Memory Blog Post](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/)
