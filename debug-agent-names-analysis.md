# Agent Names Mismatch Analysis

## Executive Summary

The observability sessions API is returning `agentName: "unknown"` for orchestrator sessions due to a bug in the agent name extraction logic in `index.py`. The extraction algorithm fails to handle the orchestrator agent's runtime ID format correctly.

## Data Analysis

### Sessions in debug-sessions-output.json

Parsed from the JSON body, we have 5 sessions:

| Session ID | Agent Name | Agent Display Name | Agent ID | Status |
|------------|------------|-------------------|----------|---------|
| `coder_7a289a85-c421-4520-8dcc-5c11121f133c` | **coder** | Coding Assistant | `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1` | completed |
| `orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c` | **unknown** ❌ | unknown | `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1` | completed |
| `7a289a85-c421-4520-8dcc-5c11121f133c` | **coder** | Coding Assistant | `marodon_fast_orchestrator-3cC1353g4w` | completed |
| `coder_2b386568-8356-4c14-8c47-f073e75f77e2` | **coder** | Coding Assistant | `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1` | completed |
| `2b386568-8356-4c14-8c47-f073e75f77e2` | **coder** | Coding Assistant | `marodon_fast_coder-ObXJ0r2DLu` | completed |

### Unique Agent Names Found

- `coder` (appears 4 times)
- `unknown` (appears 1 time) ❌

### Agent ID to Agent Name Mapping

| Agent ID | Expected Agent Name | Actual Agent Name | Status |
|----------|-------------------|------------------|---------|
| `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1` | backend | coder | ⚠️ Ambiguous |
| `marodon_fast_orchestrator-3cC1353g4w` | orchestrator | coder | ❌ Wrong |
| `marodon_fast_coder-ObXJ0r2DLu` | coder | coder | ✅ Correct |

## Root Cause Analysis

### The Problem

Looking at session `orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c`:
- **Session ID prefix**: `orchestrator_` (indicates orchestrator session)
- **Agent ID**: `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1`
- **Extracted Agent Name**: `unknown` ❌
- **Expected Agent Name**: `orchestrator`

### The Bug in index.py

The agent name extraction logic in `parse_otel_span()` (lines 195-217) has a flawed algorithm:

```python
# Extract agent name from runtime ID
# Format: stack_agent-randomID (e.g., "marodon_fast_umich-v3vPp178fn")
# Split by dash to separate agent part from random ID
if "-" in runtime_id:
    base_part = runtime_id.rsplit("-", 1)[0]  # e.g., "marodon_fast_umich"
    
    # Now extract agent name by taking the last underscore-separated part
    # This handles multi-part stack names like "marodon_fast"
    if "_" in base_part:
        agent_name = base_part.rsplit("_", 1)[1]  # e.g., "umich"
```

### Why It Fails

**Case 1: Orchestrator session with backend agent ID**
- Runtime ID: `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1`
- After `rsplit("-", 1)[0]`: `marodonfastmarodonfastbackend8EA31761`
- Problem: No underscore in `marodonfastmarodonfastbackend8EA31761`
- Result: `agent_name` is never set, defaults to `None`, becomes `"unknown"`

**Case 2: Session with orchestrator agent ID**
- Session ID: `7a289a85-c421-4520-8dcc-5c11121f133c` (no prefix)
- Runtime ID: `marodon_fast_orchestrator-3cC1353g4w`
- After `rsplit("-", 1)[0]`: `marodon_fast_orchestrator`
- After `rsplit("_", 1)[1]`: `orchestrator` ✅
- But the session shows `agentName: "coder"` ❌

This suggests the "most common agent name" logic in `build_session_summary()` is overriding the correct extraction with spans from a different agent.

### Additional Issues

1. **Agent name voting logic**: The `build_session_summary()` function uses:
   ```python
   agent_name = max(set(agent_names), key=agent_names.count) if agent_names else "unknown"
   ```
   This picks the most common agent name across all spans in a session. If a session has spans from multiple agents (orchestrator + coder), it may pick the wrong one.

2. **Missing underscore handling**: Runtime IDs without underscores (like `marodonfastmarodonfastbackend8EA31761`) fail to extract any agent name.

3. **Session ID prefix ignored**: The session ID itself contains the agent name prefix (e.g., `orchestrator_`, `coder_`), but this is never used as a fallback.

## Impact

### User Experience
- Agent filter dropdown shows "unknown" as an option
- Filtering by "orchestrator" returns no results (204 response)
- Users cannot view orchestrator sessions even though they exist
- Confusion about which agent handled which sessions

### Data Integrity
- Session data is incomplete (missing agent identification)
- Analytics and monitoring cannot properly attribute sessions to agents
- SSM parameter lookups fail for "unknown" agent (no display name)

## Recommended Fix

### Option 1: Use Session ID Prefix (Recommended)

Extract agent name from the session ID prefix as the primary source:

```python
def extract_agent_name_from_session_id(session_id: str) -> Optional[str]:
    """Extract agent name from session ID prefix (e.g., 'orchestrator_uuid' -> 'orchestrator')"""
    if "_" in session_id:
        prefix = session_id.split("_", 1)[0]
        # Validate it's not just a UUID part
        if prefix and not prefix.isdigit():
            return prefix
    return None
```

Then in `build_session_summary()`:
```python
# Try session ID prefix first
agent_name = extract_agent_name_from_session_id(session_id)

# Fall back to span-based extraction
if not agent_name:
    agent_names = [span.get("agentName") for span in spans if span.get("agentName")]
    agent_name = max(set(agent_names), key=agent_names.count) if agent_names else "unknown"
```

### Option 2: Fix Runtime ID Parsing

Improve the runtime ID parsing to handle edge cases:

```python
# Handle runtime IDs without underscores by using the full base_part
if "_" in base_part:
    agent_name = base_part.rsplit("_", 1)[1]
else:
    # No underscore - try to extract from the end of the string
    # Look for common agent names as suffixes
    for known_agent in ["orchestrator", "coder", "backend", "umich"]:
        if base_part.endswith(known_agent):
            agent_name = known_agent
            break
```

### Option 3: Hybrid Approach (Most Robust)

Combine both approaches:
1. Try session ID prefix first (most reliable)
2. Fall back to improved runtime ID parsing
3. Use span voting as last resort
4. Default to "unknown" only if all methods fail

## Testing Recommendations

1. Test with orchestrator sessions (session ID prefix: `orchestrator_`)
2. Test with coder sessions (session ID prefix: `coder_`)
3. Test with sessions without prefixes (plain UUID)
4. Test with runtime IDs that have no underscores
5. Test with runtime IDs that have multiple underscores
6. Verify SSM parameter lookups work for all extracted agent names
7. Verify agent filter dropdown shows correct agent names
8. Verify filtering by each agent name returns correct sessions

## Next Steps

1. Implement Option 1 (session ID prefix extraction) as the primary fix
2. Add unit tests for agent name extraction logic
3. Add logging to track extraction method used (prefix vs runtime ID vs voting)
4. Update the bugfix spec to include backend agent name extraction fix
5. Deploy and verify with real session data
6. Monitor CloudWatch logs for "unknown" agent occurrences
