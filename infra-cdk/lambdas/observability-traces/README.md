# Observability Traces API Lambda

## Overview

This Lambda function retrieves trace data for a specific session from CloudWatch Logs by querying OTEL spans emitted by AgentCore Runtime. It builds a hierarchical trace structure showing parent-child relationships between spans.

## Data Source

**CloudWatch Logs**: `aws/spans` log group (OTEL format)

The Lambda queries spans using the FilterLogEvents API with a filter pattern matching the session ID attribute.

## API Endpoint

**Path**: `GET /observability/traces/{sessionId}`

**Authentication**: Cognito JWT token required

**Path Parameters**:
- `sessionId` (required): Session ID to retrieve traces for

## Response Format

```json
{
  "trace": {
    "traceId": "abc123...",
    "sessionId": "orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c",
    "spans": [
      {
        "spanId": "span123",
        "parentSpanId": null,
        "traceId": "abc123...",
        "name": "POST /invocations http receive",
        "spanType": "agent_invocation",
        "startTime": 1704067200000,
        "endTime": 1704067210000,
        "duration": 10000,
        "status": "ok",
        "attributes": {}
      },
      {
        "spanId": "span456",
        "parentSpanId": "span123",
        "traceId": "abc123...",
        "name": "llm_invocation",
        "spanType": "llm_invocation",
        "startTime": 1704067201000,
        "endTime": 1704067205000,
        "duration": 4000,
        "status": "ok",
        "attributes": {
          "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
          "inputTokens": 1500,
          "outputTokens": 500,
          "totalTokens": 2000
        }
      },
      {
        "spanId": "span789",
        "parentSpanId": "span123",
        "traceId": "abc123...",
        "name": "tool_call",
        "spanType": "tool_call",
        "startTime": 1704067206000,
        "endTime": 1704067209000,
        "duration": 3000,
        "status": "ok",
        "attributes": {
          "toolName": "readFile",
          "toolInput": "{\"path\": \"example.txt\"}",
          "toolOutput": "File contents..."
        }
      }
    ],
    "startTime": 1704067200000,
    "endTime": 1704067210000,
    "duration": 10000
  }
}
```

## Span Types

The Lambda categorizes spans into the following types:

1. **agent_invocation**: Top-level agent invocation spans
2. **llm_invocation**: LLM model invocation spans (includes token usage)
3. **tool_call**: Tool execution spans (includes tool name and I/O)
4. **unknown**: Spans that don't match known patterns

## Span Attributes

Attributes are extracted based on span type:

### LLM Invocation Attributes
- `model`: LLM model identifier
- `inputTokens`: Number of input tokens
- `outputTokens`: Number of output tokens
- `totalTokens`: Total tokens used

### Tool Call Attributes
- `toolName`: Name of the tool executed
- `toolInput`: Tool input parameters (JSON string)
- `toolOutput`: Tool output result (JSON string)

### Error Attributes (all types)
- `errorType`: Type of error that occurred
- `errorMessage`: Error message details

## Error Responses

- **400 Bad Request**: Missing or invalid sessionId parameter
- **401 Unauthorized**: Invalid or missing JWT token
- **404 Not Found**: No trace data found for the specified session
- **500 Internal Server Error**: Failed to query CloudWatch Logs or parse spans

## IAM Permissions Required

```json
{
  "Effect": "Allow",
  "Action": [
    "logs:FilterLogEvents",
    "logs:DescribeLogStreams"
  ],
  "Resource": "arn:aws:logs:*:*:log-group:aws/spans:*"
}
```

## Environment Variables

- `STACK_NAME_BASE`: Base name of the CloudFormation stack
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Implementation Details

### OTEL Span Parsing

The Lambda parses OTEL spans from CloudWatch Logs events. Each span is a JSON object with:
- Trace and span identifiers
- Parent-child relationships via `parentSpanId`
- Timestamps in ISO 8601 format
- Attributes containing metadata

### Trace Structure Building

1. Query all spans for the session from CloudWatch Logs
2. Parse each OTEL span into a simplified structure
3. Sort spans by start time
4. Calculate overall trace duration from first to last span
5. Return hierarchical structure with all spans

### Parent-Child Relationships

Spans include `parentSpanId` to indicate their parent in the trace hierarchy. The frontend can use this to build a tree visualization showing the execution flow.

## Testing

To test the Lambda locally:

```bash
# Deploy the stack
cd infra-cdk
cdk deploy

# Get a session ID from the sessions API
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://your-api-url/observability/sessions

# Query traces for a specific session
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://your-api-url/observability/traces/SESSION_ID
```

## Related Files

- **Lambda**: `infra-cdk/lambdas/observability-traces/index.py`
- **CDK Infrastructure**: `infra-cdk/lib/backend-stack.ts` (createObservabilityTracesApi method)
- **Frontend Service**: `frontend/src/services/observabilityService.ts`
- **Deployment Script**: `scripts/deploy-frontend.py` (aws-exports.json generation)
