# Memory API Parameter Validation Fix - Bugfix Design

## Overview

The Memory API Lambda function is failing due to incorrect parameter usage when calling AWS AgentCore Memory APIs. The function is missing required URI parameters (`actorId` and `sessionId`) for the `ListEvents` API and is calling a non-existent method (`retrieve_memory_records` instead of `list_memory_records`). This fix will correct the boto3 client calls to match the official AWS AgentCore Memory API signatures, ensuring proper parameter placement and method names.

The fix is minimal and targeted: update two functions to use correct API signatures without changing the overall architecture or data flow.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when the Memory Lambda calls AgentCore Memory APIs with incorrect parameters or method names
- **Property (P)**: The desired behavior - Memory APIs are called with correct parameters in the correct locations (URI vs body), returning memory records successfully
- **Preservation**: Existing filtering, sorting, transformation, CORS handling, and error handling logic that must remain unchanged
- **list_memory_events()**: The function in `infra-cdk/lambdas/memory/index.py` that retrieves short-term memory events using the ListEvents API
- **retrieve_memory_records_by_namespace()**: The function in `infra-cdk/lambdas/memory/index.py` that retrieves long-term memory records using the ListMemoryRecords API
- **actorId**: User identifier required as a URI parameter for ListEvents API (extracted from JWT token)
- **sessionId**: Session identifier required as a URI parameter for ListEvents API (currently not available in the Lambda context)
- **namespace**: Memory namespace prefix required as a body parameter for ListMemoryRecords API (e.g., "/summaries/{actorId}")

## Bug Details

### Fault Condition

The bug manifests when the Memory Lambda calls AgentCore Memory APIs. The `list_memory_events()` function is passing only `memoryId` as a body parameter, but the AWS API requires `actorId` and `sessionId` as URI parameters in the request path. The `retrieve_memory_records_by_namespace()` function is calling a non-existent method `retrieve_memory_records()` instead of the correct `list_memory_records()` method, and is passing incorrect parameters.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type MemoryAPICall
  OUTPUT: boolean
  
  RETURN (input.method == "list_events" 
          AND input.uri_parameters NOT CONTAINS "actorId"
          AND input.uri_parameters NOT CONTAINS "sessionId")
         OR (input.method == "retrieve_memory_records"
          AND method_exists("retrieve_memory_records") == FALSE)
         OR (input.method == "list_memory_records"
          AND input.body_parameters NOT CONTAINS "namespace")
END FUNCTION
```

### Examples

- **ListEvents API Call (Current - Incorrect)**:
  - Method: `agentcore_client.list_events(memoryId="abc123", maxResults=50)`
  - Expected: HTTP 200 with events list
  - Actual: HTTP 400 "Missing required parameter in input: 'actorId'" and "Missing required parameter in input: 'sessionId'"

- **ListEvents API Call (Fixed - Correct)**:
  - Method: `agentcore_client.list_events(memoryId="abc123", actorId="user-123", sessionId="session-456", maxResults=50)`
  - Expected: HTTP 200 with events list
  - Actual: HTTP 200 with events list

- **ListMemoryRecords API Call (Current - Incorrect)**:
  - Method: `agentcore_client.retrieve_memory_records(memoryId="abc123", searchCriteria={"searchQuery": "*"}, namespace="/summaries/user-123")`
  - Expected: HTTP 200 with memory records
  - Actual: AttributeError: 'AgentCore' object has no attribute 'retrieve_memory_records'

- **ListMemoryRecords API Call (Fixed - Correct)**:
  - Method: `agentcore_client.list_memory_records(memoryId="abc123", namespace="/summaries/user-123", maxResults=50)`
  - Expected: HTTP 200 with memory records
  - Actual: HTTP 200 with memory records

- **Edge Case - Missing sessionId Context**:
  - The Lambda doesn't have access to a specific sessionId since it's listing memories across all sessions
  - Expected: Use a wildcard or special value to retrieve events across all sessions
  - Solution: Remove ListEvents call entirely and rely only on ListMemoryRecords for long-term memory

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- JWT token extraction and user ID validation must continue to work exactly as before
- Memory filtering by agentName and userId must remain unchanged
- Memory sorting by timestamp must remain unchanged
- Memory transformation from AgentCore format to frontend format must remain unchanged
- CORS handling for preflight and actual requests must remain unchanged
- Error handling for authentication (401), validation (400), and server errors (500) must remain unchanged
- Retrieval from all three memory strategies (summaries, preferences, facts) must remain unchanged

**Scope:**
All inputs that do NOT involve calling AgentCore Memory APIs should be completely unaffected by this fix. This includes:
- Query parameter parsing
- JWT token extraction
- Filter and sort logic
- Response transformation
- CORS header generation
- Error response formatting

## Hypothesized Root Cause

Based on the bug description and AWS documentation, the most likely issues are:

1. **Incorrect Parameter Placement for ListEvents**: The function is passing `actorId` and `sessionId` as body parameters (or not at all), but the AWS API requires them as URI parameters in the request path pattern: `POST /memories/{memoryId}/actor/{actorId}/sessions/{sessionId}`

2. **Incorrect Method Name**: The function is calling `retrieve_memory_records()` which doesn't exist in the boto3 AgentCore client. The correct method name is `list_memory_records()`

3. **Incorrect Parameters for ListMemoryRecords**: The function is passing `searchCriteria` which is not a valid parameter. The correct required parameter is `namespace` as a body parameter

4. **Missing sessionId Context**: The Lambda is designed to list memories across all sessions for a user, but the ListEvents API requires a specific sessionId. This suggests we should either:
   - Remove the ListEvents call entirely (recommended)
   - Or implement a workaround to query events across all sessions (complex)

## Correctness Properties

Property 1: Fault Condition - Memory API Calls Use Correct Parameters

_For any_ Memory API call where the bug condition holds (incorrect parameters or method names), the fixed Lambda function SHALL use the correct boto3 method names with parameters placed in the correct locations (URI vs body), causing the AgentCore Memory API to return HTTP 200 with the requested memory records instead of HTTP 400 parameter validation errors.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Non-API-Call Logic Unchanged

_For any_ code path that does NOT involve calling AgentCore Memory APIs (JWT extraction, filtering, sorting, transformation, CORS handling, error handling), the fixed Lambda function SHALL produce exactly the same behavior as the original function, preserving all existing functionality for request processing, response formatting, and error handling.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `infra-cdk/lambdas/memory/index.py`

**Function 1**: `list_memory_events()` (Lines 68-110)

**Specific Changes**:
1. **Remove ListEvents Call Entirely**: Since the Lambda lists memories across all sessions and ListEvents requires a specific sessionId, remove this function call from the handler
   - Delete the `list_memory_events()` function definition
   - Remove the call to `list_memory_events()` in the handler (around line 445)
   - Remove events from `transform_memory_records()` call (around line 455)
   - Justification: Long-term memory records from ListMemoryRecords are sufficient for the Memory page UI

**Function 2**: `retrieve_memory_records_by_namespace()` (Lines 114-163)

**Specific Changes**:
1. **Fix Method Name**: Change `agentcore_client.retrieve_memory_records()` to `agentcore_client.list_memory_records()`
   - Line ~149: Replace method call

2. **Fix Parameters**: Update parameters to match AWS API signature
   - Remove: `searchCriteria` parameter (not valid)
   - Keep: `memoryId` (required URI parameter)
   - Keep: `namespace` (required body parameter)
   - Keep: `maxResults` (optional body parameter)
   - Keep: `nextToken` (optional body parameter)

3. **Fix Response Handling**: Update response key from `memoryRecords` to match actual API response
   - Line ~155: Verify correct response key name from AWS documentation
   - Update: `response.get('memoryRecords', [])` to correct key if different

**Function 3**: `transform_memory_records()` (Lines 230-273)

**Specific Changes**:
1. **Remove Events Parameter**: Since we're removing ListEvents, remove the events parameter and related logic
   - Line ~232: Remove `events: List[Dict[str, Any]]` parameter
   - Lines ~260-273: Remove the loop that transforms events
   - Update function signature to only accept `records` parameter

**Function 4**: `handler()` (Lines 362-end)

**Specific Changes**:
1. **Remove ListEvents Call**: Remove the call to `list_memory_events()`
   - Lines ~445-451: Delete the events_result assignment

2. **Update Transform Call**: Remove events parameter from `transform_memory_records()`
   - Line ~455: Change `transform_memory_records(records=..., events=...)` to `transform_memory_records(records=...)`

### Alternative Approach (If ListEvents is Required)

If short-term events are needed, implement a session discovery mechanism:
1. Query Runtime API to list all sessions for the user
2. Loop through sessions and call ListEvents for each with proper URI parameters
3. Aggregate results from all sessions

However, this is complex and likely unnecessary since long-term memory strategies already capture important information.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write a validation script that calls the AgentCore Memory APIs directly with the current (incorrect) parameters to observe the exact error messages. Then test with corrected parameters to confirm they work.

**Test Cases**:
1. **ListEvents with Missing URI Parameters**: Call `list_events(memoryId="test")` without actorId/sessionId (will fail on unfixed code with "Missing required parameter" error)
2. **Retrieve Memory Records Method**: Call `retrieve_memory_records()` method (will fail with AttributeError on unfixed code)
3. **ListMemoryRecords with Correct Parameters**: Call `list_memory_records(memoryId="test", namespace="/summaries/user")` (should succeed, confirming correct API signature)
4. **ListEvents with Correct URI Parameters**: Call `list_events(memoryId="test", actorId="user", sessionId="session")` (should succeed, confirming correct API signature)

**Expected Counterexamples**:
- ListEvents returns HTTP 400 with "Missing required parameter in input: 'actorId'" and "Missing required parameter in input: 'sessionId'"
- retrieve_memory_records() raises AttributeError
- Possible causes: incorrect parameter placement (body vs URI), incorrect method name, missing required parameters

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL api_call WHERE isBugCondition(api_call) DO
  result := fixed_lambda_handler(api_call)
  ASSERT result.statusCode == 200
  ASSERT result.body CONTAINS "memories"
  ASSERT len(result.body.memories) >= 0
END FOR
```

**Test Cases**:
1. **Unit Test - list_memory_records Call**: Verify `list_memory_records()` is called with correct parameters
2. **Unit Test - Response Parsing**: Verify response from `list_memory_records()` is correctly parsed
3. **Integration Test - Full Handler**: Call Lambda handler with valid JWT and verify HTTP 200 response with memories
4. **Integration Test - Multiple Namespaces**: Verify memories are retrieved from all three strategies (summaries, preferences, facts)

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT original_handler(input) = fixed_handler(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-API-call code paths

**Test Plan**: Observe behavior on UNFIXED code first for filtering, sorting, transformation, then write property-based tests capturing that behavior.

**Test Cases**:
1. **JWT Extraction Preservation**: Verify `extract_user_id_from_jwt()` continues to work correctly with various JWT formats
2. **Filter Preservation**: Verify `filter_memories()` produces same results for various filter combinations (agentName, userId, both, neither)
3. **Sort Preservation**: Verify `sort_memories()` produces same results for "asc" and "desc" sort orders
4. **Transform Preservation**: Verify `transform_memory_records()` produces same output format (after removing events parameter)
5. **CORS Preservation**: Verify `get_cors_headers()` returns same headers for various origins
6. **Error Handling Preservation**: Verify 401, 400, and 500 errors are returned in same scenarios

### Unit Tests

- Test `list_memory_records()` call with correct parameters (memoryId, namespace, maxResults, nextToken)
- Test response parsing from `list_memory_records()` API
- Test namespace construction for all three memory strategies
- Test error handling when AgentCore API returns errors
- Test pagination handling with nextToken

### Property-Based Tests

- Generate random user IDs and verify namespace construction is correct
- Generate random filter combinations and verify filtering logic is preserved
- Generate random sort orders and verify sorting logic is preserved
- Generate random memory records and verify transformation logic is preserved

### Integration Tests

- Test full Lambda handler with valid JWT token and verify HTTP 200 response
- Test Lambda handler with invalid JWT token and verify HTTP 401 response
- Test Lambda handler with missing MEMORY_ID environment variable and verify HTTP 500 response
- Test Lambda handler retrieves memories from all three strategies
- Test Lambda handler applies filters correctly
- Test Lambda handler applies sorting correctly
- Test Lambda handler returns correct response format for frontend
