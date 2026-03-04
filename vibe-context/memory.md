# AgentCore Memory Guidance
https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-organization.html

When you create or update an AgentCore Memory, you can optionally create one or more memory strategies. Within a strategy, use a namespace to specify AgentCore Memory organizes long-term memories.

Every time AgentCore Memory extracts a new long-term memory with a memory strategy, the long-term memory is saved under the namespace you set. This means that all long-term memories are scoped to their specific namespace, keeping them organized and preventing any conflicts with other users or sessions. You should use a hierarchical format separated by forward slashes /, ending with a trailing slash. The trailing slash prevents prefix collisions in multi-tenant applications—for example, use /actors/Alice/ instead of /actors/Alice. As needed, you can use the following pre-defined variables within braces in the namespace based on your application's organization needs:

actorId – Identifies who the long-term memory belongs to.

strategyId – Shows which memory strategy is being used.

sessionId – Identifies which session or conversation the memory is from.

For example, if you define the following namespace as the input to your strategy when creating an AgentCore Memory:


/strategy/{memoryStrategyId}/actor/{actorId}/session/{sessionId}/
After memory creation, this namespace might look like:


/strategy/summarization-93483043/actor/actor-9830m2w3/session/session-9330sds8/
A namespace can have different levels of granularity:

Most granular Level of organization
/strategy/{memoryStrategyId}/actor/{actorId}/session/{sessionId}/

Granular at the actor Level across sessions
/strategy/{memoryStrategyId}/actor/{actorId}/

Granular at the strategy Level across actors
/strategy/{memoryStrategyId}/

Global across all strategies
/

For example code, see Enable long-term memory.

---

https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/

hort-term memory captures raw interaction data as immutable events, organized by actor and session. This organization supports structured storage of conversations between users and agents, system events, state changes, and other interaction data. It takes in events and stores them synchronously in the AgentCore Memory resource. These events can be either “Conversational” (USER/ASSISTANT/TOOL or other message types) or “blob” (contains binary content that can be used to store checkpoints or agent state). Out of the two event types, only the Conversational events are used for long-term memory extraction.

To create an event, you typically need 3 identifiers.

memoryId:This is automatically created and returned in the response when you create a new memory resource.
actorId:which typically identifies entities in your system (users, agents, project, or combinations),
sessionId: groups related events together.
This hierarchical structure enables precise retrieval of relevant conversation context without loading unrelated data. Let’s explore how to create a memory resource for a customer support agent using Boto3 client:

# Creating a new memory resource 
response = agentcore_client.create_memory(
    name="CustomerSupportMemory",
    description="Memory store for our customer support agent",
    eventExpiryDuration=30,  # Store raw events for 30 days
    encryptionKeyArn="arn:aws:kms:REGION:ACCOUNT_ID:key/YOUR_KEY_ID",  # Optional customer-managed KMS key
)

# Storing a user message as an event
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

# Retrieving recent conversation history
events = agentcore_client.list_events(
    memoryId="mem-123abcd",
    actorId="customer-456",
    sessionId="session-789",
    maxResults=10,
)
Python
3. Long-term memory
Long-term memory contains extracted insights, preferences, and knowledge derived from raw events. Unlike short-term memory, which stores verbatim data, long-term memory captures meaningful information that persists across sessions—such as user preferences, conversation summaries, and key insights.

The extraction process happens asynchronously after events are created, using the memory strategies defined within your memory resource. This managed asynchronous process extracts and consolidates long term memory records for efficient retrieval.

Let’s explore how to create the long-term memory resource for the customer support agent we saw before:

# Creating a new memory resource with long term
response = agentcore_client.create_memory(
    name="CustomerSupportMemory",
    description="Memory store for our customer support agent",
    eventExpiryDuration=30,  # Store raw events for 30 days
    encryptionKeyArn="arn:aws:kms:REGION:ACCOUNT_ID:key/YOUR_KEY_ID",  # Optional customer-managed KMS key
    memoryStrategies=[{
        "userPreferenceMemoryStrategy": {
            "name": "UserPreferences",
            "namespaces": ["customer-support/{actorId}/preferences"]
        }
    }]
)
Python
3.a Namespaces
Namespaces are a critical organizational concept within long-term memory that provide hierarchical structure within your memory resource. They function like file system paths, and you can use them to logically group and categorize memories. These are especially powerful in multi-tenant systems, be it multi-agent, multi-users, or both. Namespaces serve several important purposes:

Organizational structure: Separate different types of memories (preferences, summaries, entities) into distinct logical containers
Access control: Control which memories are accessible to different agents or in different contexts
Multi-tenant isolation: Segregate memories for different users or organizations with patterns like /org_id/user_id/preferences
Focused retrieval: Query specific types of memories without searching through unrelated information
For example, you might structure namespaces like:

/retail-agent/customer-123/preferences: For a specific customer’s preferences
/retail-agent/product-knowledge: For shared product information accessible to users
/support-agent/customer-123/case-summaries/session-001: For summaries of past support cases
The dynamic namespace creation above uses special placeholder variables in your namespace definitions:

{actorId}: Uses the actor identifier from the events being processed
{sessionId}: Uses the session identifier from the events
{strategyId}: Uses the strategy identifier for organization
This allows for elegant namespace structuring without hardcoding identifiers. When retrieving memories, you specify the exact namespace to search within, or a prefix match:

# Retrieving relevant memory records using semantic search
memories = agentcore_client.retrieve_memory_records(
    memoryId="mem-12345abcdef",
    namespace="customer-support/user-1/preferences",
    searchCriteria={
        "searchQuery": "Which camera should I buy?",
        "topK": 5
    }
)
Python
3.b Memory strategies
Memory strategies define the intelligence layer that transforms raw events into meaningful long-term memories. They determine what information should be extracted, how it should be processed, and where the resulting memories should be stored. Each strategy is configured with a specific namespace where the extracted memories will be stored and consolidated, creating a clear organizational structure for different types of memories. All strategies by default ignore personally identifiable information (PII) data from long-term memory records. AgentCore Memory provides 3 built-in strategies:

Semantic Strategy: Stores facts and knowledge mentioned in the conversation for future reference. For example, “The customer’s company has 500 employees across 3 office locations in Seattle, Austin, and Boston.”
Summary Strategy: Stores a running summary of a conversation, capturing main points and decisions, scoped to a session. For example, “Customer inquired about enterprise pricing, discussed implementation timeline requirements, and requested a follow-up demo.”
User Preferences Strategy: Stores user preferences, choices, or styles. For example, “User prefers detailed technical explanations over high-level summaries”, “User prefers Python for development work”.
Here are some examples of built-in memory strategies that are defined at the time of creating an AgentCore Memory resource:

# defining Memory Strategies
strategies = [{
    "semanticMemoryStrategy": {
        "name": "semantic-facts",
        "namespaces": ["/customer/{actorId}/facts"],
    },
    "summaryMemoryStrategy": {
        "name": "conversation-summary",
        "namespaces": ["/customer/{actorId}/{sessionId}/summary"],
    },
    "userPreferenceMemoryStrategy": {
        "name": "user-preferences",
        "namespace": ["/customer/{actorId}/preferences"],
    }
]
Python
To allow flexibility, Bedrock AgentCore also offers Custom memory strategies that lets you choose a specific LLM and override the prompt for extraction and consolidation to your specific domain or use case. For example, you might want to append to the semantic memory prompt so that it only extracts specific types of facts or memories.