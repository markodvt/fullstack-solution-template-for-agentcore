---
inclusion: manual
---

# AgentCore Observability Guide

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

Amazon Bedrock AgentCore provides built-in metrics to monitor performance of runtime, memory, gateway, built-in tools, and identity resources. This data is available in Amazon CloudWatch.

**Note:** For detailed, up-to-date information, prefer using the AWS docs MCP server to query official AgentCore observability documentation.

## Enabling AgentCore Observability

### One-time Setup

1. **Enable CloudWatch Transaction Search** (one-time)
   - Use CloudWatch console or AWS CLI/SDK
   - Required to view metrics, spans, and traces

2. **Enable tracing for Memory resources** (when creating memory)
   - Set tracing configuration during memory creation
   - Required to view service-provided spans for memory

## Enabling Observability in Agent Code

### For AgentCore-hosted Agents

Use AWS Distro for Open Telemetry (ADOT) SDK to instrument your agent code:

```python
from aws_opentelemetry import trace
from opentelemetry import trace as otel_trace

# Get tracer
tracer = otel_trace.get_tracer(__name__)

# Create custom spans
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your code here
    result = perform_operation()
    span.set_attribute("result.count", len(result))
```

### Custom Runtime Metrics

Output custom metrics from agent code:

```python
from opentelemetry import metrics

# Get meter
meter = metrics.get_meter(__name__)

# Create counter
request_counter = meter.create_counter(
    "agent.requests",
    description="Number of agent requests"
)

# Increment counter
request_counter.add(1, {"agent.name": "my-agent"})
```

## Enhanced Observability with Custom Headers

### Runtime Custom Headers

Pass custom headers to enhance runtime observability:

```python
response = agentcore_client.invoke_agent(
    agentId="agent-123",
    sessionId="session-456",
    inputText="Hello",
    customHeaders={
        "x-user-id": "user-789",
        "x-request-source": "web-app"
    }
)
```

### Built-in Tools Custom Headers

Pass custom headers when invoking tools:

```python
response = gateway_client.invoke_tool(
    toolId="tool-123",
    input={"query": "search term"},
    customHeaders={
        "x-user-id": "user-789",
        "x-tool-context": "research"
    }
)
```

### Identity Custom Headers

Pass custom headers for identity operations:

```python
response = identity_client.authenticate(
    credentials=credentials,
    customHeaders={
        "x-client-app": "mobile-app",
        "x-client-version": "1.2.3"
    }
)
```

## Viewing Observability Data

### CloudWatch GenAI Observability Dashboard

1. Open Amazon CloudWatch console
2. Navigate to GenAI Observability page
3. View metrics, traces, and spans for your agents

### CloudWatch Logs

Agent logs are automatically sent to CloudWatch Logs:
- Log group: `/aws/bedrock/agentcore/{agentId}`
- Filter by sessionId to see specific conversation logs

### Querying Traces

Retrieve trace data programmatically:

```python
# Get trace for a session
trace = agentcore_client.get_trace(
    sessionId="session-456"
)

# Trace includes:
# - Spans for agent invocations
# - Tool execution spans
# - Memory operation spans
# - Custom spans from your code
```

## Observability Best Practices

### ✅ DO:
- Enable CloudWatch Transaction Search (one-time setup)
- Use ADOT SDK for custom instrumentation
- Add meaningful custom attributes to spans
- Use custom headers for enhanced context
- Monitor key metrics (latency, error rate, token usage)
- Set up CloudWatch alarms for critical metrics
- Use structured logging with JSON format

### ❌ DON'T:
- Log sensitive data (PII, credentials, etc.)
- Create excessive custom spans (impacts performance)
- Ignore error traces (they reveal issues)
- Skip custom headers (reduces observability context)
- Use overly verbose logging (increases costs)

## Common Metrics to Monitor

### Runtime Metrics
- `InvocationCount` - Number of agent invocations
- `InvocationLatency` - Time to complete invocation
- `InvocationErrors` - Failed invocations
- `TokensUsed` - LLM token consumption

### Memory Metrics
- `EventCreateCount` - Events created
- `MemoryRetrievalCount` - Memory retrievals
- `MemoryRetrievalLatency` - Retrieval time
- `ExtractionErrors` - Failed extractions

### Gateway Metrics
- `ToolInvocationCount` - Tool executions
- `ToolInvocationLatency` - Tool execution time
- `ToolInvocationErrors` - Failed tool calls

## Using Other Observability Platforms

AgentCore uses OpenTelemetry (OTEL) format, which is compatible with:
- Datadog
- New Relic
- Honeycomb
- Grafana
- Prometheus

Export OTEL data to your preferred platform using OTEL collectors.

## Troubleshooting

**No traces appearing:**
- Verify CloudWatch Transaction Search is enabled
- Check agent code includes OTEL instrumentation
- Ensure IAM permissions allow CloudWatch writes

**Missing custom spans:**
- Verify ADOT SDK is installed and configured
- Check tracer is properly initialized
- Ensure spans are properly closed

**High latency:**
- Check trace data to identify bottlenecks
- Look for slow tool executions
- Review memory retrieval times
- Check LLM response times

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
