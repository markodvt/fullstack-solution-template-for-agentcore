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
- Long-term memory storage service for agents
- Stores memories across sessions
- Supports multiple memory strategies (summary, preferences, semantic facts)

**What it does:**
- Stores memory records created by agents during conversations
- Retrieves memories for agents to use in future conversations
- Organizes memories by namespace (e.g., `/summaries/{actorId}/{sessionId}`)
- Automatically used by agents via AgentCore SDK

**What it does NOT do:**
- Does NOT store session transcripts (that's in Runtime traces)
- Does NOT provide UI-level memory management (read-only from UI perspective)
- Does NOT handle short-term conversation context (that's in Runtime sessions)

**Integration Pattern:**
```
Agent Code → Memory SDK → Memory Service (automatic)
Backend Lambda → Memory API → Read memory records (for UI display)
```

**Memory Strategies (from backend-stack.ts):**
1. **SummaryMemoryStrategy**: Namespaces: `["/summaries/{actorId}/{sessionId}"]`
2. **UserPreferenceMemoryStrategy**: Namespaces: `["/preferences/{actorId}"]`
3. **SemanticMemoryStrategy**: Namespaces: `["/facts/{actorId}"]`

**Key APIs:**
- `CreateEvent` - Store memory (used by agents)
- `GetEvent` - Retrieve specific memory
- `ListEvents` - List memories with filters
- `RetrieveMemoryRecords` - Query memories for long-term strategies

**Response Format:**
- **IMPORTANT**: Response schemas differ per memory strategy
- **VALIDATION REQUIRED**: Confirm actual response format from AgentCore documentation
- Do NOT assume structure without validation

**Documentation Source:**
- AWS Bedrock AgentCore Memory API documentation
- `docs/MEMORY_INTEGRATION.md` (exists in repo)
- `backend-stack.ts` lines 310-330 (memory configuration)

---

### 3. AgentCore Gateway

**What it is:**
- A tools and MCP (Model Context Protocol) gateway
- Routes tool execution requests from agents
- Manages authentication for tool access

**What it does:**
- Lists available tools (Lambdas, other agents, MCP servers)
- Executes tools on behalf of agents
- Performs RAG semantic search on tools
- Manages inbound auth (can specific agent on behalf of specific user access Gateway and specific tool?)
- Manages outbound auth (attaches auth tokens to tool requests)
- Provides separation of concerns (Gateway is deterministic, agents are untrusted)

**What it does NOT do:**
- Does NOT manage agent discovery (that's Runtime API + SSM)
- Does NOT act as an agent registry
- Does NOT execute agents (that's Runtime's job)
- Does NOT store agent metadata

**Integration Pattern:**
```
Agent Code → Gateway → Tool Execution (Lambda, MCP server, etc.)
```

**Key Configuration (from backend-stack.ts):**
- Protocol: MCP (Model Context Protocol)
- Supported versions: ["2025-03-26"]
- Authorizer: Custom JWT with Cognito
- Role: Comprehensive IAM permissions for tool invocation

**Common Misconception:**
- ❌ WRONG: "Gateway is an agent gateway or agent registry"
- ✅ CORRECT: "Gateway is a tools gateway for executing tools on behalf of agents"

**Documentation Source:**
- AWS Bedrock AgentCore Gateway API documentation
- `backend-stack.ts` lines 700-800 (gateway configuration)
- `gateway/` directory (tool implementations)

---

### 4. AgentCore Code Interpreter

**What it is:**
- A sandboxed Python code execution environment
- Called as a tool by agents

**What it does:**
- Executes Python code in a secure sandbox
- Returns execution results to agents
- Provides data analysis and computation capabilities

**What it does NOT do:**
- Does NOT require separate resource creation (it's a managed service)
- Does NOT need explicit integration beyond IAM permissions

**Integration Pattern:**
```
Agent Code → Code Interpreter API → Execute Python → Return results
```

**IAM Permissions (from backend-stack.ts lines 340-353):**
```typescript
actions: [
  "bedrock-agentcore:StartCodeInterpreterSession",
  "bedrock-agentcore:StopCodeInterpreterSession",
  "bedrock-agentcore:InvokeCodeInterpreter",
]
resources: [`arn:aws:bedrock-agentcore:${region}:aws:code-interpreter/*`]
```

**Documentation Source:**
- AWS Bedrock AgentCore Code Interpreter API documentation
- `backend-stack.ts` lines 340-353 (IAM permissions)

---

### 5. AgentCore Identity

**Status:** NOT YET IMPLEMENTED IN THIS CODEBASE

**What it is:**
- User identity and context management service
- Handles authentication and authorization for agents

**What it does:**
- Agent inbound auth (can user access agent?)
- Agent outbound auth (can agent on behalf of user access AWS resources, external resources, or Gateway targets?)
- Manages API keys and OAuth tokens without exposing them to agents/LLMs
- Provides user context to agents

**What it does NOT do:**
- Does NOT replace Cognito (works alongside it)
- Does NOT handle frontend authentication (that's Cognito's job)

**Current State:**
- Session ID, user ID, agent ID are handled by Runtime itself
- JWT tokens are validated by Runtime authorizer
- User identity is extracted from JWT in agent code

**Future Integration:**
- Will be added in future security enhancement spec
- Will provide more granular authorization controls
- Will handle external service credentials securely

**Documentation Source:**
- AWS Bedrock AgentCore Identity API documentation (when implementing)

---

### 6. AgentCore Observability

**What it is:**
- Structured observability data access service
- Provides APIs for querying traces, spans, and metrics

**What it does:**
- Provides structured access to OTEL-formatted traces
- Aggregates metrics across sessions
- Enables querying of observability data

**What it does NOT do:**
- Does NOT generate traces (Runtime does that)
- Does NOT store logs (CloudWatch does that)

**Integration Pattern:**
```
Backend Lambda → Observability API → Trace/span data
Backend Lambda → Runtime API → Session metadata
Backend Lambda → CloudWatch Logs → OTEL traces (alternative?)
```

**VALIDATION REQUIRED:**
- **Question**: Are observability logs retrieved via AgentCore Observability API or CloudWatch Logs API?
- **Current understanding**: Runtime emits logs to CloudWatch in OTEL format
- **Need to confirm**: Which API to use for trace retrieval

**Documentation Source:**
- AWS Bedrock AgentCore Observability API documentation
- Confirm whether to use Observability API or CloudWatch Logs API

---

## Agent Discovery Architecture

**Current Implementation:** SSM-based discovery

**Why SSM?**
- Stores agent metadata in SSM parameters
- Supports local agents (not hosted on Runtime) that still integrate with Memory
- Provides flexibility for hybrid deployments
- May store additional configuration details beyond what Runtime API provides

**Discovery Flow:**
```
Frontend → /api/agents → Lambda → Runtime API (list agents)
                                 → SSM (agent metadata)
                                 → Combine and return
```

**Future Consideration:**
- May shift some discovery to Runtime API later
- Keep SSM for now for flexibility
- Hybrid approach: Runtime API for runtime status, SSM for configuration

**Documentation Source:**
- `infra-cdk/lambdas/agent-discovery/index.py`
- `backend-stack.ts` (SSM parameter creation)

---

## Component Integration Map

```
Frontend Pages          Backend APIs           AgentCore Components
─────────────────────────────────────────────────────────────────
Agent Gallery    ──────> /agents         ──────> Runtime (list agents API)
                                         ──────> SSM (agent metadata)

Agent Details    ──────> /agents         ──────> Runtime (agent metadata)
                                         ──────> SSM (additional config)

Chat Page        ──────> Direct WS       ──────> Runtime (execution, session mgmt)
                                         ──────> Memory (auto-used by agents)
                                         ──────> Gateway (tool execution)
                                         ──────> Code Interpreter (via agent)

Memory Page      ──────> /memory         ──────> Memory (retrieve records)

Observability    ──────> /observability  ──────> Runtime (session metadata)
Dashboard                                ──────> CloudWatch Logs (OTEL traces)
                                                 OR Observability API (TBD)
```

---

## Common Misconceptions to Avoid

### ❌ WRONG: Gateway is an agent gateway
**✅ CORRECT:** Gateway is a tools gateway. Runtime is the "agent gateway" - its API supports listing agents and invoking them.

### ❌ WRONG: Memory is for session transcripts
**✅ CORRECT:** Memory is for long-term memories across sessions. Session transcripts are in Runtime traces.

### ❌ WRONG: Code Interpreter needs separate resource creation
**✅ CORRECT:** Code Interpreter is a managed service. Only IAM permissions are needed.

### ❌ WRONG: Identity is required for this feature
**✅ CORRECT:** Identity is a future enhancement. Current implementation uses Runtime's built-in JWT validation.

### ❌ WRONG: Observability API is the only way to get traces
**✅ CORRECT:** Need to validate whether to use Observability API or CloudWatch Logs API for OTEL traces.

---

## Data Model Validation Requirements

**CRITICAL:** When implementing backend APIs that interact with AgentCore components:

1. **DO NOT GUESS** response schemas
2. **ALWAYS VALIDATE** against AgentCore documentation
3. **TEST WITH REAL** AgentCore responses (not mocked data)
4. **CONFIRM SCHEMAS** for each memory strategy
5. **VERIFY OTEL FORMAT** structure from actual traces

**Add to ALL backend Lambda tasks:**
- Sub-task: Validate API response schemas against AgentCore documentation
- Sub-task: Confirm memory strategy schemas from CDK configuration
- Sub-task: Verify OTEL trace format structure
- Sub-task: Test with real AgentCore responses

---

## When to Use Which Component

**Use Runtime when:**
- Executing agents
- Querying session history
- Retrieving trace data
- Listing deployed agents

**Use Memory when:**
- Storing long-term memories (from agent code)
- Retrieving memories for display (from backend Lambda)
- Querying user preferences or facts

**Use Gateway when:**
- Executing tools from agent code
- Listing available tools
- Managing tool authentication

**Use Code Interpreter when:**
- Executing Python code from agent
- Performing data analysis
- Running computations

**Use Identity when (future):**
- Managing external service credentials
- Fine-grained authorization
- User context management

**Use Observability when (TBD):**
- Querying structured trace data
- Aggregating metrics
- (Confirm whether to use this or CloudWatch Logs)

---

## Documentation Sources

**Primary Sources:**
1. AWS Bedrock AgentCore API documentation (official AWS docs)
2. Repository documentation:
   - `docs/MEMORY_INTEGRATION.md`
   - `docs/GATEWAY.md` (if exists)
   - `docs/RUNTIME.md` (if exists)
3. Code examples:
   - `backend-stack.ts` (infrastructure configuration)
   - `infra-cdk/lambdas/agent-discovery/index.py` (discovery implementation)
   - `gateway/` directory (tool implementations)
   - `patterns/*/basic_agent.py` (agent code examples)

**When in Doubt:**
1. Check AWS Bedrock AgentCore documentation first
2. Review existing code in the repository
3. Ask the user for clarification
4. Do NOT make assumptions about API schemas or behavior

---

## ALWAYS FOLLOW THESE RULES WHEN WORKING WITH AGENTCORE COMPONENTS
