---
inclusion: manual
---

# AgentCore Memory Guidance

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Memory Organization and Namespaces

When you create or update an AgentCore Memory, you can optionally create memory strategies. Within a strategy, use a namespace to specify how AgentCore Memory organizes long-term memories.

### Namespace Format

Use hierarchical format separated by forward slashes `/`, ending with a trailing slash:

```
/strategy/{memoryStrategyId}/actor/{actorId}/session/{sessionId}/
```

**Important:** The trailing slash prevents prefix collisions in multi-tenant applications. Use `/actors/Alice/` instead of `/actors/Alice`.

### Pre-defined Variables

Use these variables within braces in the namespace:

- `{actorId}` – Identifies who the long-term memory belongs to
- `{strategyId}` – Shows which memory strategy is being used
- `{sessionId}` – Identifies which session or conversation the memory is from

### Namespace Granularity Levels

```python
# Most granular - per session
"/strategy/{memoryStrategyId}/actor/{actorId}/session/{sessionId}/"

# Actor level - across sessions
"/strategy/{memoryStrategyId}/actor/{actorId}/"

# Strategy level - across actors
"/strategy/{memoryStrategyId}/"

# Global - across all strategies
"/"
```

---

## Short-term Memory (Events)

Short-term memory captures raw interaction data as immutable events, organized by actor and session. Events can be:
- **Conversational** - USER/ASSISTANT/TOOL messages
- **Blob** - Binary content for checkpoints or agent state

Only Conversational events are used for long-term memory extraction.

### Creating Events

```python
import boto3
import time

agentcore_client = boto3.client('bedrock-agentcore-runtime')

# Create memory resource
response = agentcore_client.create_memory(
    name="CustomerSupportMemory",
    description="Memory store for customer support agent",
    eventExpiryDuration=30,  # Store raw events for 30 days
    encryptionKeyArn="arn:aws:kms:REGION:ACCOUNT_ID:key/YOUR_KEY_ID",  # Optional
)

# Store a user message as an event
response = agentcore_client.create_event(
    memoryId="mem-123abcd",
    actorId="customer-456",
    sessionId="session-789",
    eventTimestamp=int(time.time() * 1000),
    payload=[
        {
            "conversational": {
                "content": {"text": "I'm looking for a waterproof camera under $300"},
                "role": "USER"
            }
        }
    ]
)

# Retrieve recent conversation history
events = agentcore_client.list_events(
    memoryId="mem-123abcd",
    actorId="customer-456",
    sessionId="session-789",
    maxResults=10,
)
```

---

## Long-term Memory

Long-term memory contains extracted insights, preferences, and knowledge derived from raw events. Unlike short-term memory (verbatim data), long-term memory captures meaningful information that persists across sessions.

The extraction process happens asynchronously after events are created, using the memory strategies defined within your memory resource.

### Creating Memory with Strategies

```python
response = agentcore_client.create_memory(
    name="CustomerSupportMemory",
    description="Memory store for customer support agent",
    eventExpiryDuration=30,
    encryptionKeyArn="arn:aws:kms:REGION:ACCOUNT_ID:key/YOUR_KEY_ID",
    memoryStrategies=[{
        "userPreferenceMemoryStrategy": {
            "name": "UserPreferences",
            "namespaces": ["customer-support/{actorId}/preferences"]
        }
    }]
)
```

### Memory Strategies

AgentCore Memory provides 3 built-in strategies (all ignore PII by default):

1. **Semantic Strategy** - Stores facts and knowledge mentioned in conversation
   - Example: "The customer's company has 500 employees across 3 office locations"

2. **Summary Strategy** - Stores running summary of conversation, scoped to session
   - Example: "Customer inquired about enterprise pricing, discussed timeline, requested demo"

3. **User Preferences Strategy** - Stores user preferences, choices, or styles
   - Example: "User prefers detailed technical explanations over high-level summaries"

### Defining Multiple Strategies

```python
strategies = [
    {
        "semanticMemoryStrategy": {
            "name": "semantic-facts",
            "namespaces": ["/customer/{actorId}/facts"],
        }
    },
    {
        "summaryMemoryStrategy": {
            "name": "conversation-summary",
            "namespaces": ["/customer/{actorId}/{sessionId}/summary"],
        }
    },
    {
        "userPreferenceMemoryStrategy": {
            "name": "user-preferences",
            "namespaces": ["/customer/{actorId}/preferences"],
        }
    }
]
```

### Custom Memory Strategies

For domain-specific extraction, use custom strategies with specific LLM and custom prompts:

```python
{
    "customMemoryStrategy": {
        "name": "domain-specific",
        "namespaces": ["/domain/{actorId}/custom"],
        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "extractionPrompt": "Extract only technical specifications...",
        "consolidationPrompt": "Consolidate technical specs..."
    }
}
```

---

## Retrieving Memories

Use semantic search to retrieve relevant memories:

```python
# Retrieve relevant memory records
memories = agentcore_client.retrieve_memory_records(
    memoryId="mem-12345abcdef",
    namespace="customer-support/user-1/preferences",
    searchCriteria={
        "searchQuery": "Which camera should I buy?",
        "topK": 5
    }
)
```

### Namespace Retrieval Patterns

```python
# Exact namespace match
namespace="customer-support/user-1/preferences"

# Prefix match (all sub-namespaces)
namespace="customer-support/user-1/"

# All memories for a strategy
namespace="customer-support/"
```

---

## Best Practices

### ✅ DO:
- Use trailing slashes in namespaces to prevent collisions
- Choose appropriate granularity level for your use case
- Use semantic search to retrieve relevant memories
- Set appropriate eventExpiryDuration for short-term memory
- Use custom strategies for domain-specific extraction

### ❌ DON'T:
- Forget trailing slash (causes prefix collisions)
- Store PII in long-term memory (automatically filtered)
- Use overly broad namespaces (reduces retrieval precision)
- Assume memories are immediately available (extraction is async)
- Hardcode actorId/sessionId (use variables in namespace)

---

## Multi-tenant Isolation

For multi-tenant applications, use hierarchical namespaces:

```python
# Organization + User isolation
"/org/{organizationId}/user/{actorId}/preferences/"

# Project + User isolation
"/project/{projectId}/user/{actorId}/session/{sessionId}/"

# Agent + User isolation
"/agent/{agentId}/user/{actorId}/preferences/"
```

This ensures memories are properly scoped and isolated between tenants.

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
