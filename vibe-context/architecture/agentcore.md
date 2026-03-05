---
inclusion: manual
---

# AgentCore Architecture and Component Clarifications

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

This document provides clear definitions of each AgentCore component, their purposes, integration patterns, and common misconceptions to avoid. This is critical for correctly implementing features that integrate with AgentCore services.

## AgentCore Components

### 1. AgentCore Runtime

**What it is:**
- The execution environment for agent code
- Manages agent sessions and invocations
- Provides APIs for listing agents and retrieving session metadata
- Generates observability data (traces, spans) in OTEL format

**What it does:**
- Executes agent code in response to user requests
- Manages WebSocket connections for streaming responses
- Tracks sessions and generates session IDs
- Emits traces and spans for observability
- Handles JWT authentication for agent invocations
- Provides APIs to query session history

**What it does NOT do:**
- Does NOT manage tool execution (that's Gateway's job)
- Does NOT store long-term memory (that's Memory's job)
- Does NOT provide agent discovery/registry (use Runtime API + SSM)

**Integration Pattern:**
```
Frontend → WebSocket → Runtime (agent execution)
Backend Lambda → Runtime API → Session/trace data
```

**Key APIs:**
- `InvokeAgent` - Execute agent with streaming response
- `ListSessions` - Query session history
- `GetSession` - Get session details
- `GetTrace` - Retrieve OTEL trace data for a session

**Documentation Source:**
- AWS Bedrock AgentCore Runtime API documentation
- `docs/RUNTIME.md` (if exists in repo)

---

### 2. AgentCore Memory

**What it is:**
- Long-term and short-term memory storage for agents
- Stores conversation history, user preferences, and extracted insights
- Provides semantic search over stored memories

**What it does:**
- Stores raw events (short-term memory) with expiry
- Extracts and consolidates long-term memories using strategies
- Provides APIs to create events and retrieve memories
- Organizes memories using hierarchical namespaces
- Supports semantic search over memory records

**What it does NOT do:**
- Does NOT execute agents (that's Runtime's job)
- Does NOT manage tool execution (that's Gateway's job)
- Does NOT automatically inject memories into agent context (you must retrieve and include them)

**Integration Pattern:**
```
Agent Code → Memory API → Store/Retrieve memories
Memory Strategies → Async extraction → Long-term records
```

**Key APIs:**
- `CreateEvent` - Store conversation events
- `ListEvents` - Retrieve event history
- `RetrieveMemoryRecords` - Semantic search over memories
- `CreateMemory` - Create memory resource with strategies

**Documentation Source:**
- AWS Bedrock AgentCore Memory API documentation
- `docs/MEMORY_INTEGRATION.md`
- `.kiro/steering/backend/memory.md` for namespace patterns

---

### 3. AgentCore Gateway

**What it is:**
- Tool execution and orchestration service
- Manages tool definitions, permissions, and invocations
- Provides built-in tools (web search, code interpreter, etc.)

**What it does:**
- Executes tools on behalf of agents
- Manages tool permissions and access control
- Provides built-in tools (web_search, code_interpreter, etc.)
- Handles tool authentication and authorization
- Routes tool calls to appropriate handlers

**What it does NOT do:**
- Does NOT execute agent code (that's Runtime's job)
- Does NOT store memories (that's Memory's job)
- Does NOT manage agent sessions (that's Runtime's job)

**Integration Pattern:**
```
Agent Code → Gateway API → Tool execution
Agent defines tools → Gateway registers → Runtime invokes
```

**Key APIs:**
- `InvokeTool` - Execute a tool
- `ListTools` - Query available tools
- `RegisterTool` - Add custom tools

**Documentation Source:**
- `docs/GATEWAY.md` (authoritative)
- AWS Bedrock AgentCore Gateway API documentation

---

## Common Integration Patterns

### Pattern 1: Agent with Memory
```python
# 1. Create event in Memory
agentcore_client.create_event(
    memoryId="mem-123",
    actorId="user-456",
    sessionId="session-789",
    payload=[{"conversational": {"content": {"text": msg}, "role": "USER"}}]
)

# 2. Retrieve relevant memories
memories = agentcore_client.retrieve_memory_records(
    memoryId="mem-123",
    namespace="user-456/preferences",
    searchCriteria={"searchQuery": query, "topK": 5}
)

# 3. Include memories in agent context
agent.invoke(context=memories)
```

### Pattern 2: Agent with Gateway Tools
```python
# 1. Register tools with Gateway (done in CDK)
# 2. Agent code references tools by name
# 3. Runtime calls Gateway to execute tools
# 4. Results returned to agent
```

### Pattern 3: Observability
```python
# 1. Runtime automatically generates traces
# 2. Query traces via Runtime API
trace = agentcore_client.get_trace(sessionId="session-789")

# 3. Display in observability dashboard
```

---

## Common Misconceptions

❌ **WRONG**: "Runtime stores memories"
✅ **CORRECT**: Runtime generates session data; Memory stores long-term memories

❌ **WRONG**: "Gateway executes agents"
✅ **CORRECT**: Gateway executes tools; Runtime executes agents

❌ **WRONG**: "Memory automatically injects context into agents"
✅ **CORRECT**: You must retrieve memories and include them in agent prompts

❌ **WRONG**: "Runtime provides agent discovery"
✅ **CORRECT**: Use Runtime API + SSM Parameter Store for agent metadata

---

## When to Use Each Component

**Use Runtime when:**
- Executing agent code
- Querying session history
- Retrieving trace data
- Managing agent invocations

**Use Memory when:**
- Storing conversation history
- Extracting user preferences
- Implementing long-term context
- Semantic search over past interactions

**Use Gateway when:**
- Executing tools (web search, code interpreter, etc.)
- Managing tool permissions
- Registering custom tools
- Orchestrating tool calls

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
