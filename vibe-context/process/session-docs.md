---
inclusion: manual
---

# Session Documentation Guidelines

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

Proper documentation maintains project continuity, enables knowledge transfer, and provides an audit trail. This covers two types:

1. **Session Summaries** - Comprehensive logs of substantial work sessions
2. **Commit Messages** - Detailed commit descriptions for version control

---

## Session Summaries

### When to Create

Create a session summary when:
- ✅ Completing substantial work (2+ hours of focused development)
- ✅ Solving complex bugs that required investigation
- ✅ Making architectural decisions or discovering important patterns
- ✅ Completing multiple related tasks from a spec

Do NOT create for:
- ❌ Trivial changes (typo fixes, minor formatting)
- ❌ Single-file quick fixes
- ❌ Work fully captured in commit message

### File Location and Naming

**Location:** `.kiro/dev-history/{spec-name}/`

**Naming:** `session-summary-YYYY-MM-DD-{descriptor}.md`

**Examples:**
- `session-summary-2026-02-26-tasks-1-3.md`
- `session-summary-2026-02-27-bug-investigation.md`

### Content Structure

```markdown
# Session Summary: [Brief Title]

**Date:** [Month Day, Year]
**Duration:** [Approximate time]
**Goal:** [Primary objective]

## Previous Session Recap (if continuation)

- ✅ What was completed
- 🔧 What was in progress
- ❌ What was blocked

## Issues Identified and Fixed

### 1. [Issue Name] [Status]

**Problem:** Clear description

**Root Cause Analysis:**
1. Investigation process
2. Evidence gathered
3. Why it occurred

**Fix Applied:**
- File: `path/to/file.ext`
- Changes made
- Why this approach

**Result:** What happened after the fix

## Current Status

### ✅ Working
- Completed items

### 🔧 Fixed, Needs Deployment
- Pending validation

### ❓ Needs Investigation
- Known issues

## Files Modified

### [Category]
- `path/to/file.ext` - What changed and why

## Next Steps

1. **Action Item** with description
2. **Action Item** with description

### Testing Checklist
- [ ] Test case 1
- [ ] Test case 2

## Key Learnings

### [Learning Category]

**Critical Discovery:** Main insight

**Common Mistake:**
```language
// What NOT to do
```

**Correct Approach:**
```language
// Correct pattern
```

## Conclusion

Brief summary of accomplishments and current state.
```

### Status Indicators

- ✅ **Complete** - Fully working and tested
- 🔧 **In Progress** - Work started but not finished
- ❌ **Blocked** - Cannot proceed
- ❓ **Unknown** - Needs investigation

### Writing Guidelines

- **Be Specific:** Include exact file paths, error messages, code snippets
- **Explain the "Why":** Don't just list changes, explain reasoning
- **Think About Future Readers:** Assume unfamiliarity with the problem
- **Include Evidence:** Show error messages, logs, test results
- **Document Learnings:** Capture insights not obvious from code

---

## Commit Messages

### When to Create

Create when:
- ✅ Code changes ready to commit
- ✅ Changes tested and working
- ✅ Changes represent logical unit of work

### File Location

**Location:** `commit.txt` at project root

**Usage:** `git add . && git commit -eF commit.txt`

**Note:** Overwritten each time - template for current commit only.

### Content Structure

```plaintext
[Brief summary line - what was fixed/added]

Root Cause Analysis:
[For bugs: What was wrong and why.
 For features: The need and approach.
 2-4 sentences providing context.]

What Was Fixed/Added:
- Specific change 1
- Specific change 2
- Specific change 3

Key Changes:
- path/to/file1.ext
- path/to/file2.ext

Why This Matters:
- Impact 1: How this helps
- Impact 2: What problem this solves

Next Steps:
1. What needs to happen next
2. Follow-up work required

Testing:
- Test result 1
- Test result 2

Documentation:
- Session summary reference (if exists)
```

### Writing Guidelines

- **Summary Line:** Start with action verb (Fix, Add, Update), be specific (50-70 chars)
- **Root Cause Analysis:** Essential for bug fixes
- **Be Concise:** Shorter than session summaries
- **Reference Session Summaries:** Link if exists
- **Include Testing:** Show changes were validated

---

## Relationship Between Session Summaries and Commit Messages

### When to Create Both

Create both when:
- ✅ Substantial work session (2+ hours) with code changes
- ✅ Complex bug fix requiring investigation
- ✅ Multiple related changes across many files

**Pattern:**
1. Work on problem
2. Create session summary documenting journey
3. Create commit message summarizing changes
4. Reference session summary in commit

### When to Create Session Summary Only

- ✅ Exploratory work without code changes
- ✅ Planning and design sessions
- ✅ Investigation without immediate fix

### When to Create Commit Message Only

- ✅ Simple, straightforward changes
- ✅ Quick bug fixes with obvious cause
- ✅ Minor refactoring or cleanup

---

## Multi-Session Work

### Continuation Sessions

**First Session:**
- File: `session-summary-2026-02-26-tasks-1-2.md`
- Document work and end with "Next Steps"

**Second Session:**
- File: `session-summary-2026-02-27-continued.md`
- Start with "Previous Session Recap"
- Reference previous summary

### Multiple Commits in One Session

**Session Summary:**
- Document entire session
- Reference all commits

**Commit Messages:**
- Separate commit.txt for each logical unit
- Each references session summary

---

## Quick Reference

### When to Create What

| Scenario | Session Summary | Commit Message |
|----------|----------------|----------------|
| Complex bug fix with investigation | ✅ Yes | ✅ Yes |
| Simple bug fix (obvious cause) | ❌ No | ✅ Yes |
| Feature implementation (2+ hours) | ✅ Yes | ✅ Yes |
| Quick feature addition | ❌ No | ✅ Yes |
| Exploratory investigation | ✅ Yes | ❌ No |
| Typo fix | ❌ No | ✅ Yes (brief) |

### File Locations

- **Session Summaries:** `.kiro/dev-history/{spec-name}/session-summary-YYYY-MM-DD-{descriptor}.md`
- **Commit Messages:** `commit.txt` (project root)

### Commit Message Template

```plaintext
[Action verb] [brief summary]

Root Cause Analysis:
[Why this change was needed]

What Was Fixed/Added:
- Change 1
- Change 2

Key Changes:
- file1.ext
- file2.ext

Why This Matters:
- Impact 1
- Impact 2

Next Steps:
1. Step 1
2. Step 2

Testing:
- Test result 1
- Test result 2

Documentation:
- Session summary reference (if exists)
```

**ALWAYS FOLLOW THESE RULES WHEN DOCUMENTING SESSIONS**
