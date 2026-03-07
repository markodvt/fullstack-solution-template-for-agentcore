# Bugfix Requirements Document

## Introduction

The observability dashboard Sessions tab has broken agent filtering functionality caused by TWO distinct bugs:

1. **Frontend Bug**: When users change the agent filter dropdown, the frontend makes unnecessary API calls to the backend instead of filtering client-side from already-loaded data. This causes slow filtering (each change takes time to re-query) and poor user experience.

2. **Backend Bug**: The Lambda's agent name extraction logic in `parse_otel_span()` returns `"unknown"` for orchestrator sessions because it fails to parse runtime IDs that lack underscores (e.g., `marodonfastmarodonfastbackend8EA31761`). The session ID prefix (e.g., `orchestrator_`, `coder_`) contains reliable agent name information but is currently ignored.

The fix will:
- Implement client-side filtering in the frontend similar to the working MemoryPage pattern
- Fix backend agent name extraction to use session ID prefix as primary source with runtime ID parsing as fallback

## Bug Analysis

### Current Behavior (Defect)

#### Frontend Issues

1.1 WHEN user changes the agent filter dropdown in SessionsTab THEN the system makes a new API call to fetchSessions with the agentName parameter

1.2 WHEN the loadSessions callback includes agentFilter in its dependency array THEN the system re-executes the callback and fetches from backend on every filter change

1.3 WHEN user changes the agent filter THEN the system shows loading state and delays the filtering result instead of instant client-side filtering

#### Backend Issues

1.4 WHEN parse_otel_span() processes a runtime ID without underscores (e.g., `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1`) THEN the agent name extraction fails and returns None, which becomes "unknown"

1.5 WHEN build_session_summary() receives a session with ID prefix `orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c` THEN the system ignores the reliable `orchestrator_` prefix and relies only on span-based extraction

1.6 WHEN the agent name extraction fails THEN the API response contains `agentName: "unknown"` and `agentDisplayName: "unknown"`, causing the frontend dropdown to show "unknown" as an option

1.7 WHEN users filter by "orchestrator" THEN the system returns no results because orchestrator sessions are labeled as "unknown" in the database

### Expected Behavior (Correct)

#### Frontend Fixes

2.1 WHEN user changes the agent filter dropdown in SessionsTab THEN the system SHALL filter the already-loaded sessions client-side without making API calls

2.2 WHEN the loadSessions callback is defined THEN the system SHALL only include timeRangeHours and user.id_token in its dependency array, excluding agentFilter

2.3 WHEN fetchSessions is called THEN the system SHALL not pass the agentName parameter, fetching all sessions for client-side filtering

2.4 WHEN user changes the agent filter THEN the system SHALL instantly display filtered results using the useMemo hook without loading state

#### Backend Fixes

2.5 WHEN build_session_summary() processes a session ID with a prefix (e.g., `orchestrator_`, `coder_`) THEN the system SHALL extract the agent name from the prefix as the primary source

2.6 WHEN the session ID lacks a recognizable prefix THEN the system SHALL fall back to runtime ID parsing from OTEL span ARNs

2.7 WHEN parse_otel_span() processes a runtime ID without underscores THEN the system SHALL use the session ID prefix extraction as fallback instead of returning "unknown"

2.8 WHEN orchestrator sessions are processed THEN the API response SHALL contain `agentName: "orchestrator"` and the appropriate display name from SSM parameters

### Unchanged Behavior (Regression Prevention)

#### Frontend Preservation

3.1 WHEN user changes the time range filter THEN the system SHALL CONTINUE TO make a new API call to fetch sessions for the new time period

3.2 WHEN user clicks the refresh button THEN the system SHALL CONTINUE TO make a new API call to fetch the latest sessions

3.3 WHEN sessions are loaded THEN the system SHALL CONTINUE TO display them in SessionList with all existing functionality (expandable traces, status indicators, etc.)

3.4 WHEN no sessions match the filters THEN the system SHALL CONTINUE TO display the appropriate empty state message

3.5 WHEN the API call fails THEN the system SHALL CONTINUE TO display the error state with retry button

#### Backend Preservation

3.6 WHEN parse_otel_span() processes runtime IDs with underscores (e.g., `marodon_fast_coder-ObXJ0r2DLu`) THEN the system SHALL CONTINUE TO extract agent names correctly using the existing algorithm

3.7 WHEN build_session_summary() aggregates spans THEN the system SHALL CONTINUE TO calculate all existing metrics (duration, status, trace count, etc.) without changes

3.8 WHEN the API returns session data THEN the system SHALL CONTINUE TO include all existing fields (sessionId, agentId, status, startTime, endTime, etc.) in the response

3.9 WHEN SSM parameter lookups occur for agent display names THEN the system SHALL CONTINUE TO use the same parameter paths and caching logic

## Evidence

### Frontend Evidence

From `frontend/src/pages/ObservabilityPage/SessionsTab.tsx`:
- Line 47: `agentFilter` is included in loadSessions dependency array, causing re-fetches
- Line 52: `fetchSessions` is called with `agentName: agentFilter` parameter
- No client-side filtering logic exists (unlike MemoryPage which uses useMemo)

### Backend Evidence

From `debug-sessions-output.json` and `debug-agent-names-analysis.md`:

**Orchestrator session with incorrect agent name:**
```json
{
  "sessionId": "orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c",
  "agentName": "unknown",  // ❌ Should be "orchestrator"
  "agentDisplayName": "unknown",
  "agentId": "marodonfastmarodonfastbackend8EA31761-64aLtD8bP1"
}
```

**Root cause in `infra-cdk/lambdas/observability-sessions/index.py`:**
- Lines 195-217: `parse_otel_span()` agent name extraction fails when runtime ID lacks underscores
- Runtime ID `marodonfastmarodonfastbackend8EA31761` has no underscore after removing suffix
- Session ID prefix `orchestrator_` is ignored, even though it reliably indicates the agent name
- Line 289: `build_session_summary()` uses span voting but doesn't check session ID prefix first

## Files Involved

### Frontend
- `frontend/src/pages/ObservabilityPage/SessionsTab.tsx` - Remove agentFilter from dependencies, implement client-side filtering

### Backend
- `infra-cdk/lambdas/observability-sessions/index.py` - Add session ID prefix extraction in `build_session_summary()`, improve fallback logic
