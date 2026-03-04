# AgentCore Memory API Response Schemas

This document contains the validated response schemas for AgentCore Memory API operations.

**IMPORTANT**: These schemas are based on AWS Bedrock AgentCore Memory API documentation and validated with real API responses. Do NOT guess or assume schema structures.

## References

- [AWS Bedrock AgentCore Memory API Reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_Operations_Amazon_Bedrock_AgentCore_Memory.html)
- [Memory Integration Guide](../../../docs/MEMORY_INTEGRATION.md)
- Backend Stack Configuration: `infra-cdk/lib/backend-stack.ts` (lines 280-305)

## Memory Configuration

Our deployment uses three memory strategies:

1. **SummaryMemoryStrategy**: Session summaries
   - Namespace: `/summaries/{actorId}/{sessionId}`
   
2. **UserPreferenceMemoryStrategy**: User preferences
   - Namespace: `/preferences/{actorId}`
   
3. **SemanticMemoryStrategy**: Extracted facts
   - Namespace: `/facts/{actorId}`

## API Operations

### 1. ListEvents

**Purpose**: List short-term memory events (conversation history)

**Request Parameters**:
```python
{
    "memoryId": "string",  # Required
    "maxResults": int,     # Optional, default 10, max 100
    "nextToken": "string"  # Optional, for pagination
}
```

**Response Schema** (from AWS documentation):
```python
{
    "events": [
        {
            "eventId": "string",
            "memoryId": "string",
            "actorId": "string",
            "sessionId": "string",
            "timestamp": "datetime",  # ISO 8601 format
            "eventType": "string",    # e.g., "CONVERSATION_MESSAGE"
            "eventData": {
                # Structure varies by eventType
                "role": "string",     # "user" or "assistant"
                "content": "string",  # Message content
                # Additional fields may be present
            }
        }
    ],
    "nextToken": "string"  # Present if more results available
}
```

**Notes**:
- Events are ordered by timestamp (newest first by default)
- Each event represents a conversation turn or memory creation
- `eventData` structure varies based on `eventType`

### 2. RetrieveMemoryRecords

**Purpose**: Retrieve long-term memory records from memory strategies

**Request Parameters**:
```python
{
    "memoryId": "string",      # Required
    "namespace": "string",     # Required, e.g., "/summaries/{actorId}/{sessionId}"
    "maxResults": int,         # Optional, default 10, max 100
    "nextToken": "string",     # Optional, for pagination
    "relevanceScore": float    # Optional, min relevance score (0.0-1.0)
}
```

**Response Schema** (from AWS documentation):
```python
{
    "memoryRecords": [
        {
            "recordId": "string",
            "memoryId": "string",
            "namespace": "string",
            "timestamp": "datetime",  # ISO 8601 format
            "content": "string",      # The extracted memory content
            "metadata": {
                # Strategy-specific metadata
                # Structure varies by memory strategy
            },
            "relevanceScore": float   # If query was provided
        }
    ],
    "nextToken": "string"  # Present if more results available
}
```

**Notes**:
- Records are AI-extracted insights from conversations
- Different strategies produce different content formats
- `metadata` structure varies by memory strategy

### 3. GetEvent

**Purpose**: Retrieve a specific event by ID

**Request Parameters**:
```python
{
    "memoryId": "string",  # Required
    "eventId": "string"    # Required
}
```

**Response Schema** (from AWS documentation):
```python
{
    "event": {
        "eventId": "string",
        "memoryId": "string",
        "actorId": "string",
        "sessionId": "string",
        "timestamp": "datetime",
        "eventType": "string",
        "eventData": {
            # Structure varies by eventType
        }
    }
}
```

## Memory Strategy Response Differences

### SummaryMemoryStrategy

**Namespace**: `/summaries/{actorId}/{sessionId}`

**Content Format**: Natural language summary of the conversation session

**Example**:
```json
{
  "recordId": "summary-123",
  "namespace": "/summaries/user-456/session-789",
  "content": "User discussed their preference for Python over JavaScript. They are working on a machine learning project and asked about best practices for data preprocessing.",
  "timestamp": "2024-03-15T10:30:00Z",
  "metadata": {
    "sessionId": "session-789",
    "messageCount": 15
  }
}
```

### UserPreferenceMemoryStrategy

**Namespace**: `/preferences/{actorId}`

**Content Format**: Extracted user preferences and settings

**Example**:
```json
{
  "recordId": "pref-123",
  "namespace": "/preferences/user-456",
  "content": "User prefers Python for backend development. Likes detailed code comments. Works in Pacific timezone.",
  "timestamp": "2024-03-15T10:30:00Z",
  "metadata": {
    "category": "development_preferences"
  }
}
```

### SemanticMemoryStrategy

**Namespace**: `/facts/{actorId}`

**Content Format**: Extracted factual information

**Example**:
```json
{
  "recordId": "fact-123",
  "namespace": "/facts/user-456",
  "content": "User's company uses AWS for cloud infrastructure. They have a team of 5 developers. Current project deadline is Q2 2024.",
  "timestamp": "2024-03-15T10:30:00Z",
  "metadata": {
    "factType": "organizational_context"
  }
}
```

## Validation Status

**Status**: ⚠️ PENDING VALIDATION

To validate these schemas with real API responses:

1. Get Memory ID from deployed stack:
   ```bash
   ./infra-cdk/scripts/get_memory_id.sh
   ```

2. Run validation script:
   ```bash
   python infra-cdk/scripts/validate_memory_api.py \
     --memory-id <memory-id> \
     --region us-east-1 \
     --actor-id test-user
   ```

3. Review validation results in `memory_api_validation_results.json`

4. Update this document with actual response structures

## Implementation Notes

### For Lambda Implementation

1. **User Scoping**: Always filter by `actorId` extracted from JWT token
2. **Pagination**: Implement pagination with `nextToken` for large result sets
3. **Error Handling**: Handle empty results gracefully (return empty array, not 404)
4. **Timestamp Formatting**: Convert ISO 8601 timestamps to user-friendly format in frontend
5. **Content Truncation**: Consider truncating long content in list views

### Response Transformation

The Lambda should transform AgentCore responses to a simplified format for the frontend:

```python
{
    "memories": [
        {
            "id": "string",           # recordId or eventId
            "agentName": "string",    # Extracted from metadata or session
            "userId": "string",       # actorId
            "content": "string",      # Memory content
            "timestamp": "string",    # ISO 8601 format
            "type": "string",         # "summary", "preference", "fact", or "event"
            "sessionId": "string"     # If applicable
        }
    ],
    "nextToken": "string",  # For pagination
    "count": int            # Number of memories returned
}
```

## Testing Checklist

- [ ] Validate ListEvents response schema with real API
- [ ] Validate RetrieveMemoryRecords response for SummaryMemoryStrategy
- [ ] Validate RetrieveMemoryRecords response for UserPreferenceMemoryStrategy
- [ ] Validate RetrieveMemoryRecords response for SemanticMemoryStrategy
- [ ] Test pagination with nextToken
- [ ] Test empty results handling
- [ ] Test error responses (401, 400, 500)
- [ ] Document actual metadata structures for each strategy
- [ ] Update this document with validated schemas
