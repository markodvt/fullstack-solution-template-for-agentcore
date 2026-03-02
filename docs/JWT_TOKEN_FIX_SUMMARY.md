# JWT Token Passing Fix for Specialist Agent Invocation

## Problem
The orchestrator agent was passing the wrong authentication token to specialist agents. It was using the OAuth2 `access_token` (intended for Gateway authentication) instead of the user's JWT token from Cognito authentication.

## Root Cause
- **OAuth2 access_token**: Machine-to-machine token for authenticating with the AgentCore Gateway
- **User JWT token**: User authentication token from Cognito, required by specialist agent runtimes

Specialist agents are configured with JWT (Cognito) authorization and expect the user's JWT token in the Authorization header, not the OAuth2 token.

## Changes Made

### 1. `orchestrator_agent.py` - Function Signature Update
**Location**: Line ~80

**Change**: Added `user_jwt_token` parameter to `create_orchestrator_agent()` function:

```python
def create_orchestrator_agent(user_id: str, session_id: str, user_jwt_token: str) -> Agent:
```

**Documentation**: Updated docstring to explain that `user_jwt_token` is the user's JWT token from Cognito authentication used for authenticating requests to specialist agents.

### 2. `orchestrator_agent.py` - JWT Token Extraction
**Location**: Line ~300 in `agent_stream()` function

**Change**: Extract the user's JWT token from the Authorization header:

```python
# Extract the JWT token itself for passing to specialist agents
# Specialist agents are configured with JWT (Cognito) authorization and need the user's token
auth_header = context.request_headers.get("Authorization", "")
user_jwt_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
```

**Change**: Pass the JWT token to `create_orchestrator_agent()`:

```python
agent = create_orchestrator_agent(
    user_id=user_id, 
    session_id=session_id,
    user_jwt_token=user_jwt_token
)
```

### 3. `orchestrator_agent.py` - Specialist Tools Initialization
**Location**: Line ~205 in `create_orchestrator_agent()` function

**Change**: Pass user's JWT token instead of OAuth2 access_token:

```python
specialist_tools = SpecialistInvocationTools(
    session_id=session_id,
    actor_id=user_id,
    access_token=user_jwt_token  # Pass user's JWT token for specialist authentication
)
```

**Note**: The OAuth2 `access_token` is still used for Gateway MCP client authentication (line ~195), which is correct.

### 4. `invoke_specialist.py` - Documentation Updates
**Locations**: Multiple function docstrings

**Changes**: Updated all docstrings to clarify that `access_token` parameter is:
- "User's JWT token from Cognito authentication"
- NOT "OAuth2 access token"

**Functions updated**:
- `invoke_colorado()`
- `invoke_umich()`
- `invoke_coder()`
- `_invoke_specialist()`
- `SpecialistInvocationTools.__init__()`

## Token Flow After Fix

```
User Request → Frontend
    ↓ (User JWT token in Authorization header)
Orchestrator Runtime
    ↓ (Validates JWT, extracts user_id)
Orchestrator Agent
    ↓ (Extracts JWT token from header)
    ├─→ Gateway MCP Client (uses OAuth2 access_token) ✓
    └─→ Specialist Tools (uses user JWT token) ✓
        ↓
    Specialist Agent Runtimes (expect user JWT token) ✓
```

## Testing Recommendations

1. **Test specialist invocation**: Verify that the orchestrator can successfully invoke Colorado, UMich, and Coder agents
2. **Test authentication**: Confirm that specialist agents receive and validate the correct JWT token
3. **Test Gateway tools**: Ensure Gateway MCP client still works with OAuth2 token
4. **Test memory access**: Verify that specialists can access user's long-term memory with the correct actor_id

## Files Modified

1. `patterns/strands-multi-agent-orchestrator/agents/orchestrator/orchestrator_agent.py`
   - Updated `create_orchestrator_agent()` signature
   - Added JWT token extraction in `agent_stream()`
   - Changed specialist tools initialization to use JWT token

2. `patterns/strands-multi-agent-orchestrator/tools/invoke_specialist.py`
   - Updated all docstrings to clarify token type
   - No code logic changes (parameter name remains `access_token`)

## Validation

- ✅ No syntax errors
- ✅ No linting errors
- ✅ Docstrings updated
- ✅ Comments clarified
- ✅ Type hints maintained
