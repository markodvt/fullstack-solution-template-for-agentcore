# Notes on Kiro tools

### MCP: `search_documentation`

Example:

```
{
  "search_phrase": "AgentCore Runtime sessions invocation history",
  "search_intent": "Find AgentCore Runtime API documentation for querying agent invocation sessions and history",
  "limit": 10
}
```

```
{
  "search_results": [
    {
      "rank_order": 1,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html",
      "title": "Invoke an AgentCore Runtime agent - Amazon Bedrock AgentCore",
      "context": "Invoke AgentCore Runtime agent, send requests to endpoints, maintain context across interactions, target specific agents, invoke streaming and multi-modal agents, implement error handling."
    },
    {
      "rank_order": 2,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html",
      "title": "Use isolated sessions for agents - Amazon Bedrock AgentCore",
      "context": "Isolated sessions enable AI agents to maintain complex state, perform privileged operations, and ensure deterministic security for non-deterministic processes while preserving ephemeral context across extended conversations and multi-step workflows."
    },
    {
      "rank_order": 3,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_InvokeAgentRuntime.html",
      "title": "InvokeAgentRuntime - Amazon Bedrock AgentCore Data Plane",
      "context": "Sends a request to an agent or tool hosted in an Amazon Bedrock AgentCore Runtime and receives responses in real-time."
    },
    {
      "rank_order": 4,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-runtime-metrics.html",
      "title": "AgentCore generated runtime observability data - Amazon Bedrock AgentCore",
      "context": "Enable observability data to monitor agent runtime invocations, view resource usage, analyze logs, track errors, monitor WebSocket connections, optimize requests."
    },
    {
      "rank_order": 5,
      "url": "https://docs.aws.amazon.com/sdk-for-kotlin/api/latest/bedrockagentcore/aws.sdk.kotlin.services.bedrockagentcore.model/-invoke-agent-runtime-response/runtime-session-id.html",
      "title": "runtimeSessionId - AWS SDK for Kotlin",
      "context": "Learn how to use runtimeSessionId in the AWS SDK for Kotlin"
    },
    {
      "rank_order": 6,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-troubleshooting.html",
      "title": "Troubleshoot AgentCore Runtime - Amazon Bedrock AgentCore",
      "context": "Comprehensive logging and incremental testing are key for troubleshooting agent runtime issues like payload format errors, authentication problems, and container startup failures."
    },
    {
      "rank_order": 7,
      "url": "https://docs.aws.amazon.com/sdk-for-kotlin/api/latest/bedrockagentcore/aws.sdk.kotlin.services.bedrockagentcore.model/-invoke-agent-runtime-request/runtime-session-id.html",
      "title": "runtimeSessionId - AWS SDK for Kotlin",
      "context": "Learn how to use runtimeSessionId in the AWS SDK for Kotlin"
    },
    {
      "rank_order": 8,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-lifecycle-settings.html",
      "title": "Configure Amazon Bedrock AgentCore lifecycle settings - Amazon Bedrock AgentCore",
      "context": "AgentCore Runtime lifecycle configuration manages runtime sessions, optimizes resource utilization by automatically cleaning up idle sessions, and prevents long-running instances from consuming resources indefinitely."
    },
    {
      "rank_order": 9,
      "url": "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/session-sessions-view.html",
      "title": "Agent details - Sessions - Amazon CloudWatch",
      "context": "Analyze span relationships, review span data, examine model inputs and outputs, filter traces, and sort table columns to troubleshoot session metrics and trace summaries."
    },
    {
      "rank_order": 10,
      "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html",
      "title": "How it works - Amazon Bedrock AgentCore",
      "context": "AgentCore Runtime handles scaling, infrastructure, security isolation, enabling focus on intelligent agent experiences. Defines agent behavior, capabilities, maintains context across interactions, isolates sessions, authenticates users/services, supports long-running operations, streams partial responses, enables bidirectional communication, deploys agent updates."
    }
  ],
  "facets": {
    "product_types": [
      "Amazon Bedrock AgentCore",
      "AWS SDK for Kotlin",
      "Botocore",
      "Amazon Bedrock",
      "Amazon Bedrock AgentCore Control Plane",
      "Boto3",
      "AWS CLI",
      "Amazon CloudWatch",
      "Cli",
      "AWS Prescriptive Guidance"
    ],
    "guide_types": [
      "Developer Guide",
      "SDK Reference",
      "Guide",
      "API Reference",
      "API reference",
      "User Guide",
      "AWS Security Reference Architecture (AWS SRA) – AI security",
      "Code Library",
      "Developer guide",
      "Implementation Guide"
    ]
  },
  "query_id": "87550374-8563-48e8-ba3c-a46f194f49b6"
}
```

### MCP: `read_documentation`

Example:

```
{
  "max_length": 10000,
  "url": "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html"
}
```

```
AWS Documentation from https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html:

# Use isolated sessions for agents

Amazon Bedrock AgentCore Runtime lets you isolate each user session and safely reuse context across
multiple invocations in a user session. Session isolation is critical for AI agent workloads
due to their unique operational characteristics:

* **Complete execution environment separation**: Each
  user session in AgentCore Runtime receives its own dedicated microVM with isolated Compute,
  memory, and filesystem resources. This prevents one user's agent from accessing
  another user's data. After session completion, the entire microVM is terminated and
  memory is sanitized to remove all session data, eliminating cross-session
  contamination risks.
* **Stateful reasoning processes**: Unlike stateless
  functions, AI agents maintain complex contextual state throughout their execution
  cycle, beyond simple message history for multi-turn conversations. AgentCore Runtime preserves
  this state securely within a session while ensuring complete isolation between
  different users, enabling personalized agent experiences without compromising data
  boundaries.
* **Privileged tool operations**: AI agents perform
  privileged operations on users' behalf through integrated tools accessing various
  resources. AgentCore Runtime's isolation model ensures these tool operations maintain proper
  security contexts and prevents credential sharing or permission escalation between
  different user sessions.
* **Deterministic security for non-deterministic
  processes**: AI agent behavior can be non-deterministic due to the
  probabilistic nature of foundation models. AgentCore Runtime provides consistent,
  deterministic isolation boundaries regardless of agent execution patterns,
  delivering the predictable security properties required for enterprise
  deployments.

###### Note

AgentCore does not enforce session-to-user mappings - your client backend should
maintain the relationship between users and their session IDs.
Additionally, your client backend should implement logic for user to session
lifecycle management like maximum number of sessions per user.

## Understanding ephemeral context

While AgentCore provides strong session isolation, these sessions are
ephemeral in nature. Any data stored in memory or written to disk persists only for the
session duration. This includes conversation history, user preferences, intermediate
calculation results, and any other state information your agent maintains.

For data that needs to be retained beyond the session lifetime (such as user
conversation history, learned preferences, or important insights), you should use
AgentCore Memory. This service provides purpose-built persistent storage designed
specifically for agent workloads, with both short-term and long-term memory
capabilities.

## Extended conversations and multi-step workflows

Unlike traditional serverless functions that terminate after each request,
AgentCore supports ephemeral, isolated compute sessions lasting up to 8 hours.
This simplifies building multi-step agentic workflows as you can make multiple calls to
the same environment, with each invocation building upon the context established by
previous interactions.

## AgentCore Runtime session lifecycle

###### Session creation

A new session is created on the first invoke with a unique runtimeSessionId
provided by your application. AgentCore Runtime provisions a dedicated
execution environment (microVM) for each session. Context is preserved between
invocations to the same session.

###### Session states

Sessions can be in one of the following states:

* **Active**: Either processing a sync request or
  doing background tasks. Sync invocation activity is automatically tracked based
  on invocations to a runtime session. Background tasks are communicated by the
  agent code by responding with "HealthyBusy" status in pings.
* **Idle**: When not processing any requests or
  background tasks. The session has completed processing but remains available for
  future invocations.
* **Terminated**: Execution environment provisioned
  for the session is terminated. This can be due to inactivity (of 15 minutes),
  reaching max duration (8 hours) or if it's deemed unhealthy based on health
  checks. Subsequent invokes to a terminated runtimeSessionId will provision a new
  execution environment.

## How to use sessions

To use sessions effectively:

* Generate a unique session ID for each user or conversation with at least 33 characters
* Pass the same session ID for all related invocations
* Use different session IDs for different users or conversations

###### Example Using sessions for a conversation

```
# First message in a conversation

response1 = agent_core_client.InvokeAgentRuntime(
   agentRuntimeArn=agent_arn,
   runtimeSessionId="user-123456-conversation-12345678", # or uuid.uuid4()
   payload=json.dumps({"prompt": "Tell me about AWS"}).encode()
)

# Follow-up message in the same conversation reuses the runtimeSessionId.

response2 = agent_core_client.InvokeAgentRuntime(
   agentRuntimeArn=agent_arn,
   runtimeSessionId="user-123456-conversation-12345678", # or uuid.uuid4()
   payload=json.dumps({"prompt": "How does it compare to other cloud providers"}).encode()
)
```

By using the same runtimeSessionId for related invocations, you ensure that context is
maintained across the conversation, allowing your agent to provide coherent responses
that build on previous interactions.
```
