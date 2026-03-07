# Status: Lambda Timeout Fix Required for Observability Dashboard

**Date:** February 27, 2025
**Duration:** Ongoing
**Goal:** Fix Lambda timeout issue preventing observability dashboard from querying sessions beyond 1-2 days

## Previous Session Recap

- ✅ **Agent filtering fixed** - Both frontend (client-side filtering) and backend (session ID prefix extraction) implemented
- ✅ **Trace viewer integration completed** - Tasks 9, 10, 20.3 from enhanced-agent-ui spec
- ✅ **Frontend working correctly** - SessionsTab displays sessions with proper agent names
- ❌ **CRITICAL BLOCKER:** Lambda times out when querying 7+ days of sessions

## Critical Issue: Lambda Timeout on Large Time Ranges

### Problem Summary

The observability-sessions Lambda **times out after 30 seconds** when users select 7-day or 30-day time ranges. This makes the time range filter completely non-functional for anything beyond 1-2 days.

### Root Cause

**CloudWatch Logs FilterLogEvents API is too slow for large time ranges:**
- Current timeout: 30 seconds (line 1806 in `infra-cdk/lib/backend-stack.ts`)
- Lambda queries ALL spans across the entire time range before returning
- Pagination loop in `infra-cdk/lambdas/observability-sessions/index.py` processes every page sequentially
- For 7 days of data, this exceeds 30 seconds consistently

### Evidence

**Debug script output (`debug-sessions-data.sh`):**
```json
{
  "errorType": "Sandbox.Timedout",
  "errorMessage": "RequestId: 9a7404a2-04a9-4f41-a4c6-4881ed285868 Error: Task timed out after 30.00 seconds"
}
```

**User experience:**
- UI shows only 2 sessions (partial data before timeout)
- Time range filter (7d, 30d) doesn't work - always times out
- Users cannot view historical session data

## Immediate Next Steps

### 1. Increase Lambda Timeout (Quick Fix)

**File:** `infra-cdk/lib/backend-stack.ts` (line 1806)

**Change:**
```typescript
// Current
timeout: cdk.Duration.seconds(30),

// Proposed
timeout: cdk.Duration.seconds(120),  // or 180 for 30-day queries
```

**Rationale:** Gives Lambda more time to complete pagination loop. Simple change, immediate relief.

**Risk:** May still timeout for 30-day queries with heavy usage. Not a long-term solution.

### 2. Optimize Pagination Logic (Medium-term Fix)

**File:** `infra-cdk/lambdas/observability-sessions/index.py`

**Current behavior:** Lambda queries ALL pages before returning any results.

**Proposed optimization:**
- Return early with partial results (e.g., first 100 sessions)
- Add pagination support to API response (nextToken)
- Let frontend request more pages if needed
- Add query limit parameter (default: 100 sessions)

**Benefits:**
- Faster initial response
- Users see data immediately
- Can load more on demand

### 3. Add Time-Based Pagination (Long-term Fix)

**Approach:** Break large time ranges into smaller windows.

**Example:**
- 7-day query → 7 separate 1-day queries
- Process in parallel or sequentially
- Aggregate results
- Return combined dataset

**Benefits:**
- More predictable query times
- Better CloudWatch Logs API performance
- Scales to 30-day queries

### 4. Consider Alternative Data Sources (Future Enhancement)

**Options:**
- Pre-aggregate session data into DynamoDB during agent execution
- Use CloudWatch Logs Insights queries (async, better for large ranges)
- Implement caching layer for frequently accessed time ranges

**Note:** These require more significant architectural changes.

## Files Involved

### Backend
- `infra-cdk/lib/backend-stack.ts` (line 1806) - Lambda timeout configuration
- `infra-cdk/lambdas/observability-sessions/index.py` - Pagination logic, query implementation

### Frontend
- `frontend/src/pages/ObservabilityPage/SessionsTab.tsx` - Time range handling, loading states

### Debug/Testing
- `debug-sessions-data.sh` - Debug script for testing Lambda directly (now fixed for macOS)

## Supporting Documentation

### Specs
- `.kiro/specs/observability-agent-filtering-fix/bugfix.md` - Agent filtering fix (completed)
- `.kiro/specs/enhanced-agent-ui/tasks.md` - Phase 6 tasks (mostly complete, except timeout issue)

### Analysis Documents
- `debug-agent-names-analysis.md` - Agent naming analysis (completed)
- `OBSERVABILITY_DEBUG_GUIDE.md` - Debugging guide for observability features

## Recommended Action Plan

**Priority 1 (Immediate - 15 minutes):**
1. Increase Lambda timeout to 120 seconds in `backend-stack.ts`
2. Deploy: `cd infra-cdk && cdk deploy`
3. Test with 7-day time range
4. Verify sessions load successfully

**Priority 2 (Short-term - 2-3 hours):**
1. Add pagination support to Lambda response
2. Implement early return with partial results (first 100 sessions)
3. Add query limit parameter to API
4. Update frontend to handle paginated responses
5. Test with 7-day and 30-day ranges

**Priority 3 (Long-term - 1-2 days):**
1. Implement time-based pagination (break queries into smaller windows)
2. Add parallel query processing
3. Consider caching layer for frequently accessed ranges
4. Performance testing and optimization

## Current State

### ✅ Working
- Agent filtering (both frontend and backend)
- Trace viewer integration
- Session display with proper agent names
- Time ranges up to 1-2 days (depending on data volume)

### 🔧 Fixed, Needs Deployment
- Agent filtering bug (already deployed)
- Trace viewer integration (already deployed)

### ❌ Blocked
- 7-day time range queries (timeout)
- 30-day time range queries (timeout)
- Historical session analysis (timeout)

## Testing Checklist

After implementing timeout fix:
- [ ] Test 7-day time range loads successfully
- [ ] Test 30-day time range loads successfully
- [ ] Verify all sessions are returned (not just partial data)
- [ ] Test with multiple agents selected
- [ ] Test with "All Agents" filter
- [ ] Verify loading states display correctly
- [ ] Test error handling if timeout still occurs

After implementing pagination:
- [ ] Test pagination works correctly
- [ ] Test "Load More" button functionality
- [ ] Verify session count is accurate
- [ ] Test with various page sizes
- [ ] Verify performance improvement

## Key Learnings

### CloudWatch Logs FilterLogEvents Performance

**Discovery:** FilterLogEvents API is slow for large time ranges (7+ days) with high log volume.

**Impact:** Sequential pagination through all results takes >30 seconds, causing Lambda timeouts.

**Solution:** Either increase timeout, implement early return with pagination, or break queries into smaller time windows.

### Lambda Timeout Configuration

**Location:** `infra-cdk/lib/backend-stack.ts` line 1806

**Current:** 30 seconds (too short for 7-day queries)

**Recommended:** 120-180 seconds for immediate relief, but pagination is better long-term solution.

## Conclusion

The observability dashboard is functional for recent sessions (1-2 days) but blocked for longer time ranges due to Lambda timeout. The immediate fix is simple (increase timeout), but the proper solution requires pagination support to handle large datasets efficiently. This is a high-priority issue as it prevents users from accessing historical session data, which is a core feature of the observability dashboard.
