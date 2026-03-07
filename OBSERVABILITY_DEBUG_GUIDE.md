# Observability Agent Filtering Debug Guide

## Fixes Applied

### 1. Metrics Lambda - Session ID Prefix Extraction
**File:** `infra-cdk/lambdas/observability-metrics/index.py`

Added the `extract_agent_name_from_session_id()` helper function that extracts agent names from session ID prefixes (e.g., "orchestrator_uuid" → "orchestrator").

Updated `aggregate_metrics()` function to:
1. First try extracting agent name from session ID prefix (most reliable)
2. Fall back to span-based extraction if no prefix found
3. Map internal agent name to display name via SSM

**Expected Result:** Metrics tab should now show "Orchestrator" instead of "unknown" for orchestrator sessions.

### 2. SessionFilters Component - Debug Logging
**File:** `frontend/src/components/observability/SessionFilters.tsx`

Added console logging to show:
- Available agents with their `name` and `displayName` fields
- Current filter value
- What value is sent to the API when user selects an agent

### 3. SessionsTab Component - Enhanced Debug Logging
**File:** `frontend/src/components/observability/SessionsTab.tsx`

Added console logging to show:
- Sample session structure from API
- All unique `agentName` values in the session data
- Filter comparison details

## How to Debug

### Step 1: Deploy the Changes
```bash
cd infra-cdk
cdk deploy --all
```

### Step 2: Open Browser Console
1. Navigate to the Observability page
2. Open browser DevTools (F12)
3. Go to the Console tab

### Step 3: Check Agent Discovery
Look for logs like:
```
[SessionFilters] Available agents: [
  { name: "orchestrator", displayName: "Orchestrator" },
  { name: "coder", displayName: "Coder Agent" },
  { name: "umich", displayName: "UMich Specialist" }
]
```

**Verify:** The `name` field contains internal names (lowercase, no spaces).

### Step 4: Check Session Data
Look for logs like:
```
[SessionsTab] Sample session from API: {
  sessionId: "orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c",
  agentName: "orchestrator",
  agentDisplayName: "Orchestrator",
  ...
}

[SessionsTab] All unique agentNames in sessions: ["orchestrator", "coder"]
```

**Verify:** The `agentName` field matches the `name` field from agent discovery.

### Step 5: Test Agent Filter
1. Select an agent from the dropdown
2. Look for logs like:
```
[SessionFilters] Agent filter changed: {
  selectedValue: "orchestrator",
  filterValue: "orchestrator",
  willSendToAPI: "orchestrator"
}

Filtering sessions: {
  totalSessions: 10,
  agentFilter: "orchestrator",
  userIdFilter: ""
}
```

3. Check if sessions are filtered correctly:
```
SessionsTab State: {
  allSessionsCount: 10,
  filteredSessionsCount: 5,
  agentFilter: "orchestrator",
  allSessions: [
    { id: "orchestrator_...", agent: "orchestrator" },
    { id: "coder_...", agent: "coder" },
    ...
  ],
  filteredSessions: [
    { id: "orchestrator_...", agent: "orchestrator" },
    ...
  ]
}
```

## Expected Behavior After Fix

### Metrics Tab
- Should show agent display names (e.g., "Orchestrator", "Coder Agent") instead of "unknown"
- Agent breakdown should correctly attribute sessions to the right agents

### Sessions Tab
- Agent filter dropdown should show all available agents
- Selecting an agent should filter sessions correctly
- No sessions should be incorrectly filtered out

## Common Issues to Look For

### Issue: Agent names don't match
**Symptom:** Filter returns 0 sessions even though sessions exist
**Debug:** Compare these values in console:
- `agent.name` from SessionFilters
- `session.agentName` from SessionsTab
- They should be identical (e.g., both "orchestrator")

### Issue: Session ID has no prefix
**Symptom:** Some sessions show as "unknown" in Metrics
**Debug:** Check session IDs in console:
- Good: "orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c"
- Bad: "7a289a85-c421-4520-8dcc-5c11121f133c" (no prefix)

If session IDs have no prefix, the span-based extraction should work as fallback.

### Issue: Display name vs internal name confusion
**Symptom:** Filter uses display name instead of internal name
**Debug:** Verify SessionFilters uses `agent.name` (not `agent.displayName`) as the filter value.

## Testing Checklist

- [ ] Deploy changes to AWS
- [ ] Open browser console
- [ ] Navigate to Observability → Metrics tab
- [ ] Verify agent names are not "unknown"
- [ ] Navigate to Observability → Sessions tab
- [ ] Verify sessions are listed
- [ ] Check console logs for agent discovery data
- [ ] Check console logs for session data
- [ ] Select an agent from the filter dropdown
- [ ] Verify sessions are filtered correctly
- [ ] Try different agents
- [ ] Verify each agent filter works

## Next Steps

If issues persist after these fixes:
1. Share the console logs from the browser
2. Check if session IDs have the expected format (agent_uuid)
3. Verify SSM parameters are set correctly for agent display names
4. Check CloudWatch Logs for Lambda errors
