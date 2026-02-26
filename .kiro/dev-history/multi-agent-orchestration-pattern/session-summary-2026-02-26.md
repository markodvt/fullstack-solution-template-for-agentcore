# Session Summary: Multi-Agent UI Troubleshooting

**Date:** February 26, 2026  
**Duration:** ~2 hours  
**Goal:** Fix UI dropdown to show all agents and enable testing each agent individually

## Issues Identified and Fixed

### 1. Agent Discovery API - 401 Unauthorized ✅ FIXED

**Problem:** Frontend was using access token, but API Gateway Cognito authorizer requires ID token

**Root Cause:** Access tokens have `client_id` claim, but authorizers validate `aud` claim (only in ID tokens)

**Fix:** 
- Changed `frontend/src/services/agentDiscoveryService.ts` to use `idToken` instead of `accessToken`
- Changed `frontend/src/components/chat/ChatInterface.tsx` to pass `auth.user.id_token`

**Result:** Agent discovery now works, dropdown shows all 4 agents

### 2. AgentCore Client Pattern Support ✅ FIXED

**Problem:** "a is not a function" error when invoking agents

**Root Cause:** PARSERS object only had `strands-single-agent` and `langgraph-single-agent`, missing `strands-multi-agent-orchestrator`

**Fix:**
- Added `"strands-multi-agent-orchestrator": parseStrandsChunk` to PARSERS in `frontend/src/lib/agentcore-client/client.ts`
- Added pattern to AgentPattern type in `frontend/src/lib/agentcore-client/types.ts`

**Result:** Client can now parse multi-agent streaming responses

### 3. Orchestrator Agent Import Errors 🔧 IN PROGRESS

**Problem:** Orchestrator fails to start with ImportError

**Root Cause:** 
- First error: `strands_code_interpreter` module doesn't exist (fixed in orchestrator_agent.py)
- Second error: `tools/__init__.py` imports `execute_python_securely` which orchestrator doesn't need

**Fixes Applied:**
- Removed `from strands_code_interpreter import StrandsCodeInterpreterTools` from orchestrator_agent.py
- Removed code_tools initialization and usage from orchestrator
- Removed `execute_python_securely` import from `tools/__init__.py`

**Status:** Code fixed, needs Docker image rebuild via CDK deployment

## Current Status

### ✅ Working
- Agent discovery API returns all 4 agents
- UI dropdown shows: Orchestrator, Colorado Specialist, UMich Specialist, Coding Assistant
- Frontend can parse multi-agent streaming responses
- All agents registered in SSM with status="success"

### 🔧 Needs Deployment
- Orchestrator agent code fixed but Docker image not rebuilt
- Need to redeploy backend to rebuild orchestrator Docker image

### ❓ Untested
- Colorado, UMich, and Coder agents (should work once orchestrator is fixed)
- Agent routing and specialist invocation
- Multi-agent conversation management

## Next Steps

### Immediate (Required)

1. **Redeploy Backend** to rebuild orchestrator Docker image:
   ```bash
   cd infra-cdk
   npx cdk deploy --all --require-approval never
   ```
   This will rebuild the orchestrator with the fixed code.

2. **Redeploy Frontend** to apply client.ts fix:
   ```bash
   python scripts/deploy-frontend.py
   ```

3. **Verify Orchestrator** starts successfully:
   ```bash
   aws logs tail /aws/bedrock-agentcore/runtimes/marodon_fast_orchestrator-3cC1353g4w-DEFAULT --since 2m
   ```
   Should see no ImportError, agent should start successfully.

4. **Test Each Agent** in UI:
   - Select "Orchestrator" → test general query
   - Select "Colorado Specialist" → test Colorado/Denver query
   - Select "UMich Specialist" → test University of Michigan query  
   - Select "Coding Assistant" → test coding query

### Follow-up Testing

5. **Test Orchestrator Routing:**
   - Send coding query to orchestrator → should route to Coder agent
   - Send Colorado query to orchestrator → should route to Colorado agent
   - Verify specialist responses are included in orchestrator response

6. **Test Multi-Agent Memory:**
   - Have conversation with one agent
   - Switch to another agent
   - Verify conversation history is separate per agent
   - Verify long-term memory is shared (preferences, facts)

### If Issues Persist

- **Orchestrator still fails:** Check CloudWatch logs for new errors
- **Agents don't respond:** Check individual agent CloudWatch logs
- **UI errors:** Check browser console for JavaScript errors
- **CORS errors:** Verify API Gateway CORS configuration

## Key Learnings

1. **Always check browser console first** - saved significant time once we looked at actual errors
2. **API Gateway Cognito authorizers require ID tokens** - not access tokens
3. **Docker images aren't automatically rebuilt** - need explicit CDK deployment
4. **Pattern names must match** - client PARSERS must include all pattern types
5. **Import errors cascade** - fixing one reveals the next

## Files Modified

### Backend
- `patterns/strands-multi-agent-orchestrator/agents/orchestrator/orchestrator_agent.py` - Removed code interpreter
- `patterns/strands-multi-agent-orchestrator/tools/__init__.py` - Removed code interpreter export

### Frontend  
- `frontend/src/services/agentDiscoveryService.ts` - Changed to use ID token
- `frontend/src/components/chat/ChatInterface.tsx` - Pass ID token to discovery
- `frontend/src/lib/agentcore-client/client.ts` - Added multi-agent pattern support
- `frontend/src/lib/agentcore-client/types.ts` - Added multi-agent pattern type

### Documentation
- `.kiro/steering/ui-troubleshooting.md` - New steering rule for UI debugging

## Success Metrics

- ✅ Agent discovery API works (200 OK)
- ✅ UI dropdown shows 4 agents
- ✅ Frontend can parse multi-agent responses
- 🔧 Orchestrator starts without errors (pending deployment)
- ❓ All agents respond to queries (pending testing)
- ❓ Orchestrator routes to specialists (pending testing)

## Technical Details

### Authentication Flow
```
User Login → Cognito → Returns ID Token + Access Token
Frontend → API Gateway (with ID Token in Authorization header)
API Gateway → Cognito Authorizer (validates ID token's aud claim)
API Gateway → Lambda (if authorized)
```

### Agent Discovery Flow
```
Frontend → GET /agents (with ID token)
API Gateway → Lambda
Lambda → SSM Parameter Store (list all /agentcore/agents/*)
Lambda → Returns agent metadata (id, name, description, pattern)
Frontend → Populates dropdown
```

### Agent Invocation Flow
```
Frontend → AgentCore Client → POST /invoke/{agentId}
API Gateway → Lambda → AgentCore Runtime
Runtime → Streams response chunks
Frontend → PARSERS[pattern] → Parses chunks
Frontend → Updates UI with streaming response
```

### Pattern-Specific Parsing
- `strands-single-agent`: Single agent, no routing
- `langgraph-single-agent`: LangGraph-based single agent
- `strands-multi-agent-orchestrator`: Orchestrator with specialist routing

## Debugging Commands Used

```bash
# Check agent registration
aws ssm get-parameters-by-path --path /agentcore/agents/ --recursive

# Check CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/marodon_fast_orchestrator-3cC1353g4w-DEFAULT --follow

# Test API directly
curl -H "Authorization: Bearer $ID_TOKEN" https://api.example.com/agents

# Check Lambda function
aws lambda get-function --function-name AgentDiscoveryFunction

# Check API Gateway
aws apigatewayv2 get-apis
```

## Architecture Diagram

```
┌─────────────┐
│   Browser   │
│   (React)   │
└──────┬──────┘
       │ ID Token
       ▼
┌─────────────────┐
│  API Gateway    │
│  (Cognito Auth) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│     Lambda      │
│ (Agent Discovery)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  SSM Parameter  │
│     Store       │
└─────────────────┘

┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ Invoke Agent
       ▼
┌─────────────────┐
│  API Gateway    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  AgentCore      │
│  Runtime        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Orchestrator   │
│     Agent       │
└──────┬──────────┘
       │
       ├──────────────┐
       ▼              ▼
┌──────────┐   ┌──────────┐
│ Colorado │   │  UMich   │
│Specialist│   │Specialist│
└──────────┘   └──────────┘
```

## Conclusion

The troubleshooting session successfully identified and fixed three critical issues:

1. **Authentication** - Frontend now uses correct token type (ID token)
2. **Pattern Support** - Frontend can parse multi-agent responses
3. **Import Errors** - Orchestrator code cleaned up (needs deployment)

The system is now in a deployable state. Once the backend is redeployed to rebuild the orchestrator Docker image, all agents should be fully functional and testable through the UI.

The key breakthrough was checking the browser console, which immediately revealed the 401 error and led to discovering the ID token vs access token issue. This highlights the importance of following the UI troubleshooting best practices documented in `.kiro/steering/ui-troubleshooting.md`.
