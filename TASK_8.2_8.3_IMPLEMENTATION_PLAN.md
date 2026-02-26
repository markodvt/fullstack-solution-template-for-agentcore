# Task 8.2 & 8.3 Implementation Plan - Frontend Agent Selection

## Overview

This plan outlines the implementation of agent selection functionality in the frontend UI, enabling users to discover available agents, select which agent to interact with, and maintain separate conversation histories per agent.

## Current State Analysis

### Backend (✅ Complete)
- Agent Discovery API deployed at `/agents` endpoint
- Returns agent metadata: name, displayName, description, runtimeArn, runtimeId, isDefault, status
- 4 agents deployed: orchestrator (default), colorado, umich, coder
- API requires Cognito JWT authentication

### Frontend (❌ Incomplete)
- Currently hardcoded to single agent via `aws-exports.json`
- No agent discovery or selection UI
- Single conversation history (not per-agent)
- AgentCore client configured with single runtime ARN

## Implementation Plan

### Phase 1: Agent Discovery Service (✅ CREATED)

**File**: `frontend/src/services/agentDiscoveryService.ts`

**Functions**:
1. `discoverAgents(accessToken: string): Promise<AgentDiscoveryResponse>`
   - Fetches agent list from `/agents` endpoint
   - Filters out failed agents (status !== 'success')
   - Returns successful agents only

2. `getDefaultAgent(agents: Agent[]): Agent | null`
   - Returns agent marked as default
   - Falls back to first agent if no default specified

**Types**:
- `Agent`: name, displayName, description, runtimeArn, runtimeId, isDefault, status
- `AgentDiscoveryResponse`: agents[], count

### Phase 2: Agent Selector Component (✅ CREATED)

**File**: `frontend/src/components/chat/AgentSelector.tsx`

**Component**: `AgentSelector`
- Props: agents, selectedAgent, onAgentChange, disabled
- Uses shadcn Select component for dropdown
- Displays agent displayName and description
- Emits agent change events to parent

**UI Design**:
- Bot icon + dropdown in ChatHeader
- Shows agent display name in trigger
- Dropdown items show name + description
- Disabled during message loading

### Phase 3: ChatInterface Updates (⏭️ TODO)

**File**: `frontend/src/components/chat/ChatInterface.tsx`

**Changes Required**:

1. **State Management**:
   ```typescript
   const [agents, setAgents] = useState<Agent[]>([])
   const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
   const [conversationHistories, setConversationHistories] = useState<Map<string, Message[]>>(new Map())
   const [sessionIds, setSessionIds] = useState<Map<string, string>>(new Map())
   ```

2. **Agent Discovery on Mount**:
   - Call `discoverAgents()` with access token
   - Set agents state
   - Load selected agent from localStorage or use default
   - Initialize AgentCore client with selected agent's runtime ARN

3. **Agent Switching Logic**:
   - Save current conversation to history map (keyed by agent name)
   - Load conversation history for newly selected agent
   - Get or create session ID for new agent
   - Reinitialize AgentCore client with new runtime ARN
   - Persist selected agent to localStorage

4. **Session Management**:
   - Each agent has its own session ID
   - Session IDs stored in Map<agentName, sessionId>
   - Session IDs persisted to localStorage
   - New session ID generated if none exists for agent

5. **Message State**:
   - Current messages state reflects selected agent's history
   - When switching agents, save current messages to map
   - Load messages from map for newly selected agent

### Phase 4: ChatHeader Integration (⏭️ TODO)

**File**: `frontend/src/components/chat/ChatHeader.tsx`

**Changes**:
- Add AgentSelector component between title and buttons
- Pass agents, selectedAgent, onAgentChange props
- Disable selector during message loading

**Layout**:
```
[Title] [AgentSelector] [New Chat] [Logout]
```

### Phase 5: AgentCore Client Updates (⏭️ TODO)

**File**: `frontend/src/lib/agentcore-client/client.ts`

**Changes**:
- Add `updateRuntimeArn(runtimeArn: string)` method
- Allow runtime ARN to be changed after initialization
- Validate runtime ARN before making requests

**Alternative**: Create new client instance when agent changes (simpler)

### Phase 6: Error Handling (⏭️ TODO)

**Scenarios to Handle**:

1. **Agent Discovery Fails**:
   - Show error message in UI
   - Fall back to single-agent mode using aws-exports.json
   - Log error for debugging

2. **No Agents Available**:
   - Show "No agents available" message
   - Disable chat interface
   - Provide retry button

3. **Selected Agent Unavailable**:
   - Show error when trying to send message
   - Suggest switching to different agent
   - Highlight available agents in dropdown

4. **Agent Switch During Message**:
   - Prevent agent switching while message is loading
   - Disable selector during streaming

### Phase 7: LocalStorage Persistence (⏭️ TODO)

**Keys**:
- `selectedAgentName`: Currently selected agent name
- `agentSessionIds`: JSON map of agent name -> session ID
- `agentConversationHistories`: JSON map of agent name -> messages[]

**Behavior**:
- Save on every agent switch
- Load on component mount
- Clear on logout
- Handle missing/corrupted data gracefully

## Testing Plan

### Manual Testing Checklist

1. **Agent Discovery**:
   - [ ] Verify agent dropdown shows all 4 agents
   - [ ] Verify default agent is pre-selected
   - [ ] Verify agent descriptions are visible

2. **Agent Selection**:
   - [ ] Select each agent and verify UI updates
   - [ ] Verify selected agent persists on page refresh
   - [ ] Verify selector is disabled during message loading

3. **Conversation Histories**:
   - [ ] Send messages to orchestrator
   - [ ] Switch to colorado, verify empty history
   - [ ] Send messages to colorado
   - [ ] Switch back to orchestrator, verify previous messages restored
   - [ ] Repeat for all agents

4. **Session Management**:
   - [ ] Verify each agent has unique session ID
   - [ ] Verify session IDs persist across page refreshes
   - [ ] Verify session IDs are different per agent

5. **Error Handling**:
   - [ ] Test with agent discovery API down
   - [ ] Test with invalid access token
   - [ ] Test switching agents during message streaming

6. **Integration**:
   - [ ] Test orchestrator routing to specialists
   - [ ] Test specialist tools (UMich http_request, current_time)
   - [ ] Verify conversation context preserved when switching

### Automated Testing (Future)

- Unit tests for agentDiscoveryService
- Component tests for AgentSelector
- Integration tests for ChatInterface with agent switching
- Property-based tests for conversation history preservation

## Implementation Order

1. ✅ Create agentDiscoveryService.ts
2. ✅ Create AgentSelector.tsx component
3. ⏭️ Update ChatInterface.tsx with agent discovery and switching logic
4. ⏭️ Update ChatHeader.tsx to include AgentSelector
5. ⏭️ Test agent discovery and selection
6. ⏭️ Implement conversation history per agent
7. ⏭️ Implement session management per agent
8. ⏭️ Add localStorage persistence
9. ⏭️ Add error handling
10. ⏭️ Manual testing of all scenarios
11. ⏭️ Run linting and formatting (`make all`)

## Design Decisions

### Why Map for Conversation Histories?
- Efficient lookup by agent name
- Easy to add/remove agents dynamically
- Clear separation of concerns

### Why localStorage for Persistence?
- Simple, no backend changes needed
- Works offline
- User-specific (per browser)
- Easy to clear on logout

### Why Separate Session IDs per Agent?
- Aligns with backend session prefixing design
- Enables separate conversation histories in AgentCore Memory
- Prevents session ID collisions

### Why Filter Failed Agents?
- Improves user experience (don't show broken agents)
- Prevents errors when trying to use failed agents
- Failed agents can be debugged separately

## Risks and Mitigations

### Risk: Agent Discovery API Failure
**Mitigation**: Fall back to single-agent mode using aws-exports.json

### Risk: Conversation History Too Large for localStorage
**Mitigation**: Implement history truncation (keep last N messages)

### Risk: Agent Switch During Streaming
**Mitigation**: Disable agent selector during message loading

### Risk: Session ID Conflicts
**Mitigation**: Use agent-specific session IDs (already handled by backend)

## Success Criteria

- [ ] User can see all available agents in dropdown
- [ ] User can select any agent and send messages
- [ ] Conversation histories are separate per agent
- [ ] Selected agent persists across page refreshes
- [ ] Agent switching preserves previous conversations
- [ ] Error handling works for all failure scenarios
- [ ] Code passes linting and formatting checks
- [ ] Manual testing checklist complete

## Next Steps After Implementation

1. Complete Task 8.3 (agent switching logic)
2. Complete Task 9 (end-to-end testing)
3. Test orchestrator routing to specialists
4. Test specialist tools (UMich http_request, current_time)
5. Commit code and update task status
6. Consider implementing Agent Gallery UI (separate spec)

## References

- Spec: `.kiro/specs/multi-agent-orchestration-pattern/`
- Session Summary: `.kiro/dev-history/multi-agent-orchestration-pattern/session-summary.md`
- UI Next Steps: `MULTI_AGENT_UI_NEXT_STEPS.md`
- Frontend README: `frontend/README.md`
- Agent Discovery Lambda: `infra-cdk/lambdas/agent-discovery/index.py`
