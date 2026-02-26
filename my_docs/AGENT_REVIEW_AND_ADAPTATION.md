# Agent Review and Adaptation Plan

## Agent Analysis

### 1. UMich Agent (`agents/umich_agent.py`)
**Purpose**: A helpful assistant who loves the University of Michigan

**Current Configuration**:
- **Model**: Claude Sonnet 4.5 (us.anthropic.claude-sonnet-4-5-20250929-v1:0) ✅ Good choice
- **Temperature**: Default (not specified, likely 0.7)
- **Tools**: 
  - `http_request` - NOT available in this repo ❌
  - `current_time` - NOT available in this repo ❌
- **System Prompt**: Simple and clear ✅
- **Memory**: None configured ❌

**Issues to Address**:
1. Missing tool imports (`strands_tools` module doesn't exist in this repo)
2. No memory integration
3. No authentication/user ID extraction
4. Uses old `bedrock_agentcore` import (should use `bedrock_agentcore.runtime`)
5. No Gateway integration
6. Missing proper error handling

### 2. Colorado Agent (`agents/colorado_agent.py`)
**Purpose**: A teacher who recently moved to Denver with a cat named Napoleon

**Current Configuration**:
- **Model**: Claude 3.5 Sonnet v2 (us.anthropic.claude-3-5-sonnet-20241022-v2:0) ⚠️ Older model
- **Temperature**: 0.7 ✅ Good for conversational agent
- **Tools**: None (pure conversational)
- **System Prompt**: Detailed personality ✅
- **Memory**: None configured ❌

**Issues to Address**:
1. Should upgrade to Claude Sonnet 4.5 for consistency
2. No memory integration
3. No authentication/user ID extraction
4. Uses old `bedrock_agentcore` import
5. No Gateway integration

### 3. Coder Agent (`agents/coder_agent.py`)
**Purpose**: Code execution and validation agent with Code Interpreter

**Current Configuration**:
- **Model**: Default (not specified, likely Claude 3.5)
- **Temperature**: Default
- **Tools**: 
  - `execute_python` - Custom Code Interpreter implementation ⚠️
- **System Prompt**: Excellent validation-focused prompt ✅
- **Memory**: None configured ❌

**Issues to Address**:
1. Uses custom Code Interpreter implementation instead of `strands_code_interpreter`
2. Hardcoded region (`us-east-1`)
3. Uses old `code_session` API
4. No memory integration
5. No authentication/user ID extraction
6. Uses old `bedrock_agentcore` import
7. No Gateway integration
8. Has standalone `main()` function that won't work in AgentCore Runtime

## Adaptation Strategy

### Common Changes for All Agents

1. **Update Imports**:
   ```python
   from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
   ```

2. **Add Memory Integration**:
   ```python
   from bedrock_agentcore.memory.integrations.strands.config import (
       AgentCoreMemoryConfig,
       RetrievalConfig,
   )
   from bedrock_agentcore.memory.integrations.strands.session_manager import (
       AgentCoreMemorySessionManager,
   )
   ```

3. **Add Authentication**:
   ```python
   from utils.auth import extract_user_id_from_context, get_gateway_access_token
   from utils.ssm import get_ssm_parameter
   ```

4. **Update Entrypoint Signature**:
   ```python
   @app.entrypoint
   async def agent_stream(payload, context: RequestContext):
       user_query = payload.get("prompt")
       session_id = payload.get("runtimeSessionId")
       user_id = extract_user_id_from_context(context)
   ```

5. **Add Shared Memory Configuration**:
   - All agents share same `memory_id`
   - Each agent uses unique session prefix
   - All agents access shared preferences/facts

### Agent-Specific Adaptations

#### UMich Agent
**Tools Decision**:
- **Option A**: Remove `http_request` and `current_time` tools (simplify)
- **Option B**: Add Gateway tools (if available)
- **Option C**: Keep Code Interpreter only
- **Recommendation**: Option A or C - focus on conversational ability

**Model**: Keep Claude Sonnet 4.5 ✅

**System Prompt**: Keep as-is, it's good ✅

#### Colorado Agent
**Model**: Upgrade to Claude Sonnet 4.5 for consistency

**Temperature**: Keep 0.7 for personality ✅

**System Prompt**: Keep as-is, excellent personality ✅

#### Coder Agent
**Tools**: Replace custom Code Interpreter with `strands_code_interpreter`:
```python
from strands_code_interpreter import StrandsCodeInterpreterTools

code_tools = StrandsCodeInterpreterTools(region)
tools=[code_tools.execute_python_securely]
```

**Model**: Specify Claude Sonnet 4.5 explicitly

**System Prompt**: Keep as-is, excellent validation focus ✅

**Remove**: Standalone `main()` function (not compatible with Runtime)

## Recommended Directory Structure

### Option 1: Move to patterns/ (Recommended)
```
patterns/
├── strands-single-agent/      # Existing basic agent
├── strands-umich-agent/       # UMich agent
├── strands-colorado-agent/    # Colorado agent
└── strands-coder-agent/       # Coder agent
```

Each pattern directory contains:
- `<agent_name>.py` - Main agent code
- `requirements.txt` - Dependencies
- `Dockerfile` - Container config (for docker deployment)

### Option 2: Multi-agent router in patterns/
```
patterns/
├── strands-single-agent/      # Existing
└── strands-multi-agent/       # New multi-agent pattern
    ├── router.py              # Routes to appropriate agent
    ├── umich_agent.py
    ├── colorado_agent.py
    ├── coder_agent.py
    └── requirements.txt
```

**Recommendation**: Option 1 for maximum flexibility

## Implementation Plan

### Phase 1: Adapt Agents (Following Coding Conventions)
For each agent:
1. ✅ Add comprehensive docstrings to all functions
2. ✅ Add explicit type hints
3. ✅ Add thorough comments
4. ✅ Update imports to use correct modules
5. ✅ Add memory integration with shared config
6. ✅ Add authentication with `extract_user_id_from_context`
7. ✅ Update entrypoint to match FAST pattern
8. ✅ Add proper error handling (fail loudly)
9. ✅ Use named parameters

### Phase 2: Create Pattern Directories
1. Create `patterns/strands-umich-agent/`
2. Create `patterns/strands-colorado-agent/`
3. Create `patterns/strands-coder-agent/`
4. Copy adapted agent code to each
5. Create `requirements.txt` for each
6. Create `Dockerfile` for each (if using docker deployment)

### Phase 3: Update Infrastructure
**Decision Needed**: How to deploy?

**Option A: Single Runtime with Router**
- One CDK deployment
- Router selects agent based on payload
- Shared memory resource
- Frontend sends agent selection in payload

**Option B: Multiple Runtimes**
- Three separate CDK deployments
- Each agent has own runtime
- Shared memory resource
- Frontend has dropdown to select runtime URL

**Option C: Staged Rollout**
- Deploy one agent at a time
- Test each individually
- Eventually combine or keep separate

**Recommendation**: Option C (staged rollout) then decide on A or B

### Phase 4: Frontend Integration
**If Multiple Runtimes**:
- Add agent selector dropdown
- Store runtime URLs in config
- Update API calls to use selected runtime

**If Single Runtime with Router**:
- Add agent selector dropdown
- Include `agentType` in payload
- Router handles agent selection

### Phase 5: Testing
1. Test each agent individually
2. Verify memory sharing works
3. Test tool access
4. Validate authentication
5. Check error handling
6. Run linting: `make all`

## Memory Configuration for Multi-Agent

All agents will share memory but use unique session prefixes:

```python
# Shared memory ID (from environment)
memory_id = os.environ.get("MEMORY_ID")

# Agent-specific session IDs
session_configs = {
    "umich": f"umich_{session_id}",
    "colorado": f"colorado_{session_id}",
    "coder": f"coder_{session_id}"
}

# Shared retrieval config (all agents access same preferences/facts)
shared_retrieval_config = {
    "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
    "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.3),
    "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=3, relevance_score=0.5),
}
```

**Benefits**:
- User preferences learned by one agent are available to all
- Facts shared across agents
- Each agent maintains its own conversation history
- Session summaries are agent-specific

## Tool Availability Matrix

| Agent | Gateway Tools | Code Interpreter | Custom Tools |
|-------|--------------|------------------|--------------|
| Basic (existing) | ✅ Yes | ✅ Yes | ❌ No |
| UMich | ⚠️ Optional | ⚠️ Optional | ❌ Remove http_request/current_time |
| Colorado | ❌ No (conversational) | ❌ No | ❌ No |
| Coder | ❌ No | ✅ Yes (primary) | ❌ No |

## Next Steps - Requires Your Decision

1. **Tool Configuration for UMich Agent**:
   - Remove tools entirely? (pure conversational)
   - Add Gateway tools?
   - Add Code Interpreter?

2. **Deployment Strategy**:
   - Single runtime with router?
   - Multiple runtimes?
   - Staged rollout?

3. **Frontend Changes**:
   - Should users select which agent to talk to?
   - Automatic routing based on query?
   - Separate chat interfaces per agent?

4. **Priority**:
   - Which agent should we adapt and deploy first?
   - All at once or one at a time?

## Estimated Effort

- **Adapt each agent**: 30-45 minutes
- **Create pattern directories**: 15 minutes
- **Update infrastructure** (per agent): 20-30 minutes
- **Frontend changes** (if needed): 1-2 hours
- **Testing**: 1-2 hours per agent

**Total**: 4-8 hours depending on deployment strategy

## Questions for You

1. Should UMich agent have tools, or be purely conversational?
2. Do you want all agents deployed simultaneously or one at a time?
3. Should users explicitly select which agent to talk to, or automatic routing?
4. Are you okay with upgrading Colorado agent to Claude Sonnet 4.5?
5. Should all agents share the same memory (preferences/facts)?
