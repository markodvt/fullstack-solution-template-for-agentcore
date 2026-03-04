# Bugfix Requirements Document

## Introduction

The Memory API Lambda function (`infra-cdk/lambdas/memory/index.py`) is failing with HTTP 500 errors due to incorrect parameters being passed to the AWS AgentCore Memory API. The Lambda function is not providing required URI parameters (`actorId` and `sessionId`) when calling the `ListEvents` API, and is calling a non-existent method (`retrieve_memory_records` instead of `list_memory_records`) for long-term memory retrieval.

This bug prevents the Memory page in the frontend from displaying any memory records, breaking a core feature of the application.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `list_memory_events()` function calls `agentcore_client.list_events()` THEN the system fails with "Missing required parameter in input: 'sessionId'" and "Missing required parameter in input: 'actorId'" errors

1.2 WHEN the `retrieve_memory_records_by_namespace()` function calls `agentcore_client.retrieve_memory_records()` THEN the system fails because the method does not exist in the boto3 AgentCore client

1.3 WHEN the Memory Lambda handler processes a GET request THEN the system returns HTTP 500 with "Internal server error" message to the frontend

1.4 WHEN the frontend Memory page attempts to load memories THEN the system displays an error message and no memory records are shown

### Expected Behavior (Correct)

2.1 WHEN the `list_memory_events()` function calls the AgentCore Memory API THEN the system SHALL provide `actorId` and `sessionId` as required URI parameters in the API request path

2.2 WHEN the `retrieve_memory_records_by_namespace()` function calls the AgentCore Memory API THEN the system SHALL use the correct method name `list_memory_records()` instead of `retrieve_memory_records()`

2.3 WHEN the `list_memory_records()` function is called THEN the system SHALL provide `namespace` as a required body parameter in the request

2.4 WHEN the Memory Lambda handler processes a GET request with valid authentication THEN the system SHALL return HTTP 200 with a list of memory records in JSON format

2.5 WHEN the frontend Memory page loads THEN the system SHALL display memory records retrieved from both short-term events and long-term memory strategies

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Memory Lambda extracts user ID from JWT token THEN the system SHALL CONTINUE TO use the `extract_user_id_from_jwt()` function to get the authenticated user's ID

3.2 WHEN the Memory Lambda applies filters (agentName, userId) THEN the system SHALL CONTINUE TO filter memories using the `filter_memories()` function

3.3 WHEN the Memory Lambda sorts results THEN the system SHALL CONTINUE TO sort memories by timestamp using the `sort_memories()` function

3.4 WHEN the Memory Lambda transforms API responses THEN the system SHALL CONTINUE TO use the `transform_memory_records()` function to convert AgentCore format to frontend format

3.5 WHEN the Memory Lambda handles CORS preflight requests THEN the system SHALL CONTINUE TO return appropriate CORS headers using the `get_cors_headers()` function

3.6 WHEN the Memory Lambda encounters authentication errors THEN the system SHALL CONTINUE TO return HTTP 401 with appropriate error messages

3.7 WHEN the Memory Lambda encounters validation errors THEN the system SHALL CONTINUE TO return HTTP 400 with appropriate error messages

3.8 WHEN the Memory Lambda retrieves memories from multiple namespaces THEN the system SHALL CONTINUE TO query all three memory strategies (summaries, preferences, facts)
