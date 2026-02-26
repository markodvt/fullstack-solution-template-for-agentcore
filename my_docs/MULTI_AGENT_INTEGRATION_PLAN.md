# Multi-Agent Integration Plan

## Overview
This plan outlines how to integrate three specialized agents (UMich Agent, Colorado Agent, and Coder Agent) into the FAST infrastructure, following the existing patterns and best practices.

## Current State Analysis

### Existing Infrastructure
- **Single Agent Pattern**: `patterns/strands-single-agent/basic_agent.py`
- **Memory**: Shared AgentCore Memory with long-term strategies (preferences, facts, summaries)
- **Tools**: Gateway MCP tools + Code Interpreter
- **Model**: Claude Sonnet 4.5 (us.anthropic.claude-sonnet-4-5-20250929-v1:0)
- **Authentication**: Cognito JWT-based with secure user ID extraction
- **Deployment**: Docker-based with CDK

### Agent Files to Review
You've added three agent files in `agents/` directory:
1. `agents/umich_agent.py` - Currently empty
2. `agents/colorado_agent.py` - Currently empty
3. `agents/coder_agent.py` - Currently empty

## Required Information

Before proceeding, I need to understand the agents from your prior repo:

### For Each Agent (UMich, Colorado, Coder):
1. **System Prompt**: What is the agent's specialized role and instructions?
2. **Tools**: What tools does each agent need?
   - Gateway tools (via MCP)?
   - Code Interpreter?
   - Custom tools?
   - Knowledge bases?
3. **Model Selection**: 
   - Which Bedrock model should each use?
   - Temperature settings?
   - Any special model parameters?
4. **Memory Strategy**: 
   - Should they share the same memory resource?
   - Different session IDs per agent?
   - Custom retrieval configurations?

## Proposed Architecture

### Option 1: Multiple Pattern Directories (Recommended)
Create separate pattern directories for each agent:
```
patterns/
├── strands-single-agent/     # Existing basic agent
├── strands-umich-agent/      # UMich specialized agent
├── strands-colorado-agent/   # Colorado specialized agent
└── strands-coder-agent/      # Coder specialized agent
```

**Pros**:
- Clean separation of concerns
- Each agent can have its own dependencies
- Easy to deploy individually
- Follows existing FAST pattern structure

**Cons**:
- More directories to maintain
- Requires multiple CDK deployments (or multi-runtime setup)

### Option 2: Single Pattern with Agent Router
Create one pattern with a router that selects the appropriate agent:
```
patterns/
└── strands-multi-agent/
    ├── multi_agent.py        # Router entrypoint
    ├── umich_agent.py        # UMich agent logic
    ├── colorado_agent.py     # Colorado agent logic
    ├── coder_agent.py        # Coder agent logic
    └── requirements.txt
```

**Pros**:
- Single deployment
- Shared dependencies
- Easier to manage shared memory

**Cons**:
- More complex routing logic
- All agents must use same base dependencies

### Option 3: Frontend Agent Selection
Keep separate patterns but let the frontend choose which agent to invoke:
- Deploy multiple runtimes (one per agent)
- Frontend dropdown to select agent
- Each agent has its own runtime URL

**Pros**:
- Maximum flexibility
- Independent scaling per agent
- Clear separation

**Cons**:
- Requires frontend changes
- More infrastructure to manage

## Recommended Approach

**Use Option 1 (Multiple Pattern Directories)** because:
1. Follows existing FAST architecture
2. Each agent can be independently configured
3. Aligns with the documentation in `docs/AGENT_CONFIGURATION.md`
4. Easier to test and debug individually
5. Can share memory resource while maintaining separate sessions

## Implementation Steps

### Phase 1: Review and Adapt Agent Code
1. **Provide Agent Content**: Share the code from your prior repo for each agent
2. **Review System Prompts**: Extract and adapt system prompts for this project
3. **Identify Tools**: Determine which tools each agent needs
4. **Model Selection**: Confirm model choices for each agent

### Phase 2: Create Pattern Directories
For each agent:
1. Create `patterns/strands-<agent-name>/` directory
2. Copy and adapt from `patterns/strands-single-agent/` as template
3. Customize:
   - System prompt
   - Tool selection
   - Model configuration
   - Memory retrieval config (if different)

### Phase 3: Update Infrastructure
1. **CDK Configuration**: Decide deployment strategy
   - Option A: Deploy all agents to same runtime (router pattern)
   - Option B: Deploy separate runtimes (requires CDK changes)
2. **Memory Sharing**: Configure shared memory with unique session IDs
3. **Frontend Integration**: Add agent selection UI (if needed)

### Phase 4: Testing
1. Test each agent individually
2. Verify memory sharing works correctly
3. Test tool access for each agent
4. Validate authentication and user ID extraction

## Shared Memory Configuration

All agents will share the same memory resource but use different session IDs:

```python
# UMich Agent
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,  # Same memory ID
    session_id=f"umich_{session_id}",  # Unique session prefix
    actor_id=user_id,  # Same user
    retrieval_config={...}  # Shared long-term memory
)

# Colorado Agent
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,  # Same memory ID
    session_id=f"colorado_{session_id}",  # Unique session prefix
    actor_id=user_id,  # Same user
    retrieval_config={...}  # Shared long-term memory
)

# Coder Agent
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,  # Same memory ID
    session_id=f"coder_{session_id}",  # Unique session prefix
    actor_id=user_id,  # Same user
    retrieval_config={...}  # Shared long-term memory
)
```

**Benefits**:
- All agents can access user preferences and facts
- Each agent maintains its own conversation history
- Session summaries are agent-specific

## Code Conventions to Follow

Based on project steering rules:

1. **Docstrings**: Add comprehensive docstrings to all functions
2. **Type Hints**: Use explicit type hints in function signatures
3. **Comments**: Thoroughly comment non-obvious code
4. **Error Handling**: Fail loudly, no silent fallbacks
5. **Named Parameters**: Use named parameters in function calls
6. **Authentication**: Use `extract_user_id_from_context()` for security

## Next Steps

**Please provide**:
1. The actual code content from your prior repo for each agent
2. System prompts for each agent
3. Tool requirements for each agent
4. Model preferences for each agent
5. Any special configuration needs

Once I have this information, I can:
1. Create adapted agent implementations
2. Set up the pattern directories
3. Configure shared memory properly
4. Update infrastructure as needed
5. Create deployment instructions

## Questions

1. **Deployment Strategy**: Do you want all agents in one runtime (router) or separate runtimes?
2. **Frontend**: Should users select which agent to talk to, or should there be automatic routing?
3. **Tools**: Do all agents need the same tools, or different tool sets?
4. **Memory**: Should all agents share preferences/facts, or be completely isolated?
5. **Priority**: Which agent should we implement first for testing?
